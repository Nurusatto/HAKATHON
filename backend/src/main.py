import os
from contextlib import asynccontextmanager
from datetime import datetime
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
import numpy as np

from src.lib import (
    load_blacklist_from_db,
    load_security_rules_from_db,
    save_to_raw_logs,
    save_to_security_alerts,
)
from src.schemas import LogInput
from .ML import train_ai_model_from_db
import redis.asyncio as aioredis

load_dotenv()


ai_detector = None
cached_security_rules = {}
cached_banned_ips = set()
blacklist_reasons = {}
redis_client: aioredis.Redis = None  # type: ignore


@asynccontextmanager
async def lifespan(app: FastAPI):
    global \
        ai_detector, \
        cached_security_rules, \
        cached_banned_ips, \
        blacklist_reasons, \
        redis_client

    redis_client = aioredis.from_url("redis://redis:6379", decode_responses=True)

    ai_detector = train_ai_model_from_db()
    cached_security_rules = load_security_rules_from_db()
    cached_banned_ips, blacklist_reasons = load_blacklist_from_db()
    yield
    await redis_client.close()


app = FastAPI(title="AI Shield SIEM Engine", lifespan=lifespan)


@app.get("/")
def hello():
    return {"message": "AI SHIELD"}


@app.post("/protect-log")
async def process_fake_log(log: LogInput, background_tasks: BackgroundTasks):
    if ai_detector is None:
        raise HTTPException(status_code=503, detail="AI Detector unavailable")

    base_risk = 10
    explanations = {}

    # --- ЭШЕЛОН 1: Перманентный черный список (Supabase) ---
    if log.ip in cached_banned_ips:
        reason = blacklist_reasons.get(log.ip, "Внесен в черный список администратором")
        raise HTTPException(
            status_code=403,
            detail=f"Доступ запрещен. Ваш IP находится в постоянном черном списке. Причина: {reason}",
        )

    # --- ЭШЕЛОН 2: Временный автобан (Redis) ---
    is_temporary_banned = await redis_client.get(f"ban:{log.ip}")
    if is_temporary_banned:
        raise HTTPException(
            status_code=429,
            detail=f"Too Many Requests. Вы временно заблокированы. Причина: {is_temporary_banned}",
        )

    # --- ЭШЕЛОН 3: СТАТИЧЕСКИЕ ПРАВИЛА И ПЕНАЛЬТИ ---
    if log.event in cached_security_rules and log.event != "suspicious_ip":
        rule = cached_security_rules[log.event]
        base_risk += rule["weight"]  # type: ignore
        explanations["static_rules"] = f"[База Правил]: {rule['desc']}"

        if log.event == "login_failed" and log.request_count_1m > 3:
            brute_force_penalty = min((log.request_count_1m - 3) * 5, 50)
            base_risk += brute_force_penalty
            explanations["brute_force_detection"] = (
                f"Обнаружены признаки брутфорса. Зафиксировано {log.request_count_1m} "
                f"неудачных попыток авторизации за минуту от IP {log.ip}."
            )

    # --- ЭШЕЛОН 4: DLP МОНИТОРИНГ (ДЕТЕКЦИЯ УТЕЧЕК) ---
    if log.event == "file_download" and log.download_size_mb > 1000:
        if log.user in ["admin", "hr_manager"]:
            base_risk += 20
            explanations["dlp_leak_detection"] = (
                f"[DLP Предупреждение]: Привилегированный пользователь {log.user} "
                f"скачивает крупный объем данных ({log.download_size_mb} МБ). Превышение лимита, требуется аудит."
            )
        else:
            base_risk += 70  # Гарантированный порог 80+ для улета в автобан
            explanations["dlp_leak_detection"] = (
                f"[DLP Критический инцидент]: Неавторизованный или рядовой сегмент ({log.user}) "
                f"пытается выгрузить {log.download_size_mb} МБ. Доступ заблокирован для предотвращения утечки данных (Data Leakage)."
            )

    # --- ЭШЕЛОН 5: ПОВЕДЕНЧЕСКИЙ АНАЛИЗ (ИИ / ISOLATION FOREST) ---
    EVENT_MAPPING = {
        "login_success": 1,
        "login_failed": 2,
        "file_download": 3,
        "admin_access": 4,
        "password_reset": 5,
    }
    event_encoded = EVENT_MAPPING.get(log.event, 0)
    current_hour = datetime.now().hour

    features = np.array(
        [[log.request_count_1m, log.download_size_mb, event_encoded, current_hour]]
    )
    ai_prediction = ai_detector.predict(features)
    print(f"[AI Engine] Prediction for IP {log.ip}: {ai_prediction}")

    if ai_prediction[0] == -1:
        base_risk += 40
        explanations["ai_analytics"] = (
            f"Зафиксирована потенциальная атака (API Abuse / Аномальный трафик). "
            f"Интенсивность от IP {log.ip} составила {log.request_count_1m} запр/мин, "
            f"а общий объем переданных данных: {log.download_size_mb:.2f} МБ, "
            f"что нетипично для времени суток {current_hour}:00."
        )

    final_risk = min(base_risk, 100)

    if not explanations:
        explanations["status"] = (
            "Поведение пользователя полностью укладывается в рамки нормы."
        )

    # --- АСИНХРОННАЯ ЗАПИСЬ И ОПОВЕЩЕНИЯ ---
    background_tasks.add_task(save_to_raw_logs, log)

    if final_risk >= 50:
        background_tasks.add_task(
            save_to_security_alerts,
            log,
            final_risk,  # type: ignore
            explanations,  # type: ignore
        )

    # --- АВТОМАТИЧЕСКИЙ РЕАКТИВНЫЙ БАН (REDIS) ---
    if final_risk >= 80:
        # Динамически вытаскиваем причину для Redis, приоритет отдаем DLP или Брутфорсу
        if "dlp_leak_detection" in explanations:
            reason_text = "DLP: Попытка несанкционированной утечки данных"
        elif "brute_force_detection" in explanations:
            reason_text = "Brute-Force: Превышено число попыток входа"
        else:
            reason_text = "Критический уровень риска (API Abuse/Аномалии)"

        await redis_client.set(f"ban:{log.ip}", reason_text, ex=60)
        print(
            f"[Redis IPS] IP {log.ip} временно заблокирован на 60 секунд за риск {final_risk}%!"
        )

    return {"status": "ok", "risk": final_risk, "explanation": explanations}


@app.post("/api/v1/retrain")
async def retrain_model():
    global ai_detector, cached_security_rules, cached_banned_ips, blacklist_reasons

    ai_detector = train_ai_model_from_db()
    cached_security_rules = load_security_rules_from_db()
    cached_banned_ips, blacklist_reasons = load_blacklist_from_db()

    return {
        "status": "success",
        "message": "Модель ИИ успешно переобучена, кэш правил и блеклиста синхронизирован!",
    }


if __name__ == "__main__":
    import uvicorn

    env_port = os.getenv("API_PORT")
    if not env_port:
        raise RuntimeError("\n[ERROR] variable 'PORT' not set in .env!\n")

    try:
        port = int(env_port)
    except ValueError:
        raise ValueError(
            f"\n[ERROR] no correct PORT='{env_port}'. Please set an integer.\n"
        )

    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
