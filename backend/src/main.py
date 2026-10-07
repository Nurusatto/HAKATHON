import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import redis.asyncio as aioredis
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from httpx import HTTPError
from postgrest.exceptions import APIError
from src.lib import (
    load_blacklist_from_db,
    load_security_rules_from_db,
    save_to_raw_logs,
    save_to_security_alerts,
)
from src.lib.supabase import supabase  # Клиент supabase
from src.schemas import LogInput

from .ai import train_ai_model_from_db

load_dotenv()

ai_detector = None
cached_security_rules = {}
cached_banned_ips = set()
blacklist_reasons = {}
cached_user_profiles = {}  # Кэш для профилей пользователей
redis_client: aioredis.Redis = None  # type: ignore


def load_user_profiles_from_db():
    """Загрузка профилей пользователей из Supabase для кэширования"""
    try:
        response = supabase.table("user_profiles").select("*").execute()
        profiles = {row["username"]: row for row in response.data}  # type: ignore
        print(
            f"[Cache System] Успешно загружено профилей пользователей: {len(profiles)}"
        )
        return profiles
    except (APIError, HTTPError) as e:
        print(f"[DB Error] Ошибка загрузки профилей пользователей: {e}")
        return {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global \
        ai_detector, \
        cached_security_rules, \
        cached_banned_ips, \
        blacklist_reasons, \
        cached_user_profiles, \
        redis_client

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        message = "[ERROR] variable 'REDIS_URL' not set in .env"
        raise RuntimeError(message)
    redis_client = aioredis.from_url(redis_url, decode_responses=True)

    ai_detector = train_ai_model_from_db()
    cached_security_rules = load_security_rules_from_db()
    cached_banned_ips, blacklist_reasons = load_blacklist_from_db()
    cached_user_profiles = load_user_profiles_from_db()
    yield
    await redis_client.close()


app = FastAPI(title="AI Shield SIEM Engine", lifespan=lifespan)


@app.get("/")
def hello():
    return {"message": "AI SHIELD"}


GENERATOR_LOCK = "generator:running"


async def finish_generator(process: asyncio.subprocess.Process):
    try:
        await asyncio.wait_for(process.wait(), timeout=850)
        if process.returncode:
            logging.getLogger("uvicorn.error").error(
                "Generator exited with code %s", process.returncode
            )
    except TimeoutError:
        process.kill()
        await process.wait()
        logging.getLogger("uvicorn.error").error("Generator timed out")
    finally:
        await redis_client.delete(GENERATOR_LOCK)


@app.get("/api/v1/generator")
async def generator_status():
    return {"running": bool(await redis_client.exists(GENERATOR_LOCK))}


@app.post("/api/v1/generator", status_code=202)
async def start_generator(background_tasks: BackgroundTasks):
    if not await redis_client.set(GENERATOR_LOCK, "1", nx=True, ex=900):
        raise HTTPException(status_code=409, detail="Генератор уже запущен")

    backend_dir = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["GENERATOR_URL"] = (
        f"http://127.0.0.1:{os.getenv('API_PORT', '8000')}/protect-log"
    )
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-u",
            str(backend_dir / "generator.py"),
            cwd=backend_dir,
            env=env,
        )
    except OSError as error:
        await redis_client.delete(GENERATOR_LOCK)
        raise HTTPException(
            status_code=500, detail="Не удалось запустить генератор"
        ) from error

    background_tasks.add_task(finish_generator, process)
    return {"status": "started", "message": "Генератор запущен: 150 событий"}


@app.post("/protect-log")
async def process_log(log: LogInput, background_tasks: BackgroundTasks):
    is_banned = await redis_client.get(f"ban:{log.ip}")
    if is_banned:
        raise HTTPException(
            status_code=403,
            detail=f"Access Denied. Your IP {log.ip} is temporarily blocked by AI Shield IPS. Reason: {is_banned}",
        )

    background_tasks.add_task(save_to_raw_logs, log)

    event_mapping = {
        "normal_request": 0,
        "login_failed": 1,
        "password_reset": 2,
        "suspicious_ip": 3,
        "data_export": 4,
        "file_download": 5,
        "admin_access": 6,
        "login_success": 7,
    }
    event_code = event_mapping.get(log.event, 0)
    current_hour = datetime.now(timezone.utc).hour

    # Входной вектор для 4D Isolation Forest
    features = np.array(
        [[log.request_count_1m, log.download_size_mb, event_code, current_hour]]
    )

    ai_score = 0
    if ai_detector is not None:
        try:
            anomaly_score = ai_detector.score_samples(features)[0]
            if anomaly_score < -0.4:
                ai_score = int((abs(anomaly_score) - 0.4) * 250)
        except ValueError as e:
            print(f"[AI Predict Error] Ошибка инференса модели: {e}")

    base_risk = max(0, min(100, ai_score))

    final_risk = base_risk
    explanations = {}

    if ai_score > 40:
        explanations["ai_analytics"] = (
            f"Зафиксирована потенциальная атака (API Abuse / Аномальный трафик). "
            f"Интенсивность от IP {log.ip} составила {log.request_count_1m} запр/мин, "
            f"а общий объем переданных данных: {log.download_size_mb} МБ, что нетипично для времени суток {current_hour}:00."
        )

    if log.ip in cached_banned_ips:
        final_risk = 100
        explanations["blacklist"] = (
            f"Зафиксирован запрос с заблокированного IP. "
            f"Причина бана: {blacklist_reasons.get(log.ip, 'подозрительная активность')}"
        )

    rules_to_check = (
        cached_security_rules.values()
        if isinstance(cached_security_rules, dict)
        else cached_security_rules
    )

    if rules_to_check:
        for rule in rules_to_check:
            if isinstance(rule, dict) and rule.get("event_type") == log.event:
                explanations["static_rules"] = (
                    f"[База Правил]: {rule.get('description', '')}"
                )
                raw_severity = rule.get("severity_score")
                if isinstance(raw_severity, (int, float, str)):
                    severity = int(raw_severity)
                else:
                    severity = 0

                final_risk = max(final_risk, severity)

    # Проверка поведенческих профилей пользователей
    user_profile = cached_user_profiles.get(log.user)

    if not user_profile:
        user_profile = {
            "username": log.user,
            "max_requests_1m": 20,
            "max_download_mb": 50.0,
        }

    if user_profile and isinstance(user_profile, dict):
        raw_download = user_profile.get("max_download_mb")
        raw_requests = user_profile.get("max_requests_1m")

        max_download = (
            float(raw_download)
            if isinstance(raw_download, (int, float, str))
            else 99999.0
        )
        max_requests = (
            int(raw_requests) if isinstance(raw_requests, (int, float, str)) else 99999
        )

        # === ГИБРИДНАЯ ПРОВЕРКА DLP (Утечка данных) ===
        if log.download_size_mb > max_download:
            leak_ratio = round(log.download_size_mb / max_download, 1)
            explanations["dlp_leak_detection"] = (
                f"Потенциальная утечка данных (DLP). Объем скачивания ({log.download_size_mb} МБ) "
                f"превышает максимальный исторический порог пользователя ({max_download} МБ) in {leak_ratio} раз."
            )

            # Начинаем с базового риска 75% и плавно добавляем по 1.5% за каждую кратность превышения лимита
            dlp_calculated_risk = int(75 + min(25, leak_ratio * 1.5))
            final_risk = max(final_risk, dlp_calculated_risk)

        # === ГИБРИДНАЯ ПРОВЕРКА ФЛУДА (API Abuse / Request Flood) ===
        if log.request_count_1m > max_requests:
            request_ratio = round(log.request_count_1m / max_requests, 1)
            explanations["profile_anomaly_detected"] = (
                f"Критическое аномальное поведение для аккаунта '{log.user}'. "
                f"Количество запросов ({log.request_count_1m}) превысило его норму ({max_requests}) в {request_ratio} раз."
            )

            # Начинаем со стартового риска 70% и плавно накидываем по 1% за рост кратности flood
            flood_calculated_risk = int(70 + min(30, request_ratio * 1.0))
            final_risk = max(final_risk, flood_calculated_risk)

    if final_risk >= 50:
        # Фоновая задача на сохранение в БД, чтобы не тормозить ответ API
        background_tasks.add_task(
            save_to_security_alerts, log, final_risk, explanations
        )
        print(
            f"[SIEM ALERT] Подозрительная активность сохранена в БД. Риск: {final_risk}%"
        )

    if final_risk >= 80:
        reason_text = "Критический уровень риска (API Abuse/Аномалии)"

        if "blacklist" in explanations:
            reason_text = "Blacklist: Запрос с заблокированного IP"
        elif "dlp_leak_detection" in explanations:
            reason_text = "DLP: Попытка несанкционированной утечки данных"
        elif "profile_anomaly_detected" in explanations:
            reason_text = (
                f"Anomaly: Критическое превышение лимитов активности профиля {log.user}"
            )

        await redis_client.set(f"ban:{log.ip}", reason_text, ex=60)
        print(
            f"[Redis IPS] IP {log.ip} временно заблокирован на 60 секунд за риск {final_risk}%!"
        )

    return {"status": "ok", "risk": final_risk, "explanation": explanations}


@app.post("/api/v1/retrain")
async def retrain_model():
    global \
        ai_detector, \
        cached_security_rules, \
        cached_banned_ips, \
        blacklist_reasons, \
        cached_user_profiles

    ai_detector = train_ai_model_from_db()
    cached_security_rules = load_security_rules_from_db()
    cached_banned_ips, blacklist_reasons = load_blacklist_from_db()
    cached_user_profiles = load_user_profiles_from_db()

    return {
        "status": "success",
        "message": "Модель ИИ успешно переобучена, кэш правил, профилей и блеклиста синхронизирован!",
    }


if __name__ == "__main__":
    import uvicorn

    env_port = os.getenv("API_PORT")
    if not env_port:
        message = "\n[ERROR] variable 'API_PORT' not set in .env"
        raise RuntimeError(message)
    uvicorn.run("src.main:app", host="0.0.0.0", port=int(env_port))
