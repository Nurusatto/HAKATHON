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

load_dotenv()


ai_detector = None
cached_security_rules = {}
cached_banned_ips = set()
blacklist_reasons = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ai_detector, cached_security_rules, cached_banned_ips, blacklist_reasons

    ai_detector = train_ai_model_from_db()
    cached_security_rules = load_security_rules_from_db()
    cached_banned_ips, blacklist_reasons = load_blacklist_from_db()
    yield


app = FastAPI(title="AI Shield SIEM Engine", lifespan=lifespan)


@app.post("/fake-log")
async def process_fake_log(log: LogInput, background_tasks: BackgroundTasks):
    if ai_detector is None:
        raise HTTPException(status_code=503, detail="AI Detector unavailable")

    base_risk = 10
    explanations = {}

    if log.ip in cached_banned_ips:
        reason = blacklist_reasons.get(log.ip, "Внесен в черный список администратором")
        ip_rule = cached_security_rules.get(
            "suspicious_ip", {"weight": 60, "desc": "Запрос со скомпрометированного IP"}
        )

        base_risk += ip_rule["weight"]  # type: ignore

        explanations["blacklist"] = f"{ip_rule['desc']} ({log.ip}). Причина: {reason}."

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

    EVENT_MAPPING = {
        "login_success": 1,
        "login_failed": 2,
        "file_download": 3,
        "admin_access": 4,
        "password_reset": 5,
    }

    event_encoded = EVENT_MAPPING.get(log.event, 0)
    current_hour = datetime.now().hour

    # Скармливаем ИИ суммарное количество запросов и объема данных вместо единичного лога
    features = np.array(
        [[log.request_count_1m, log.download_size_mb, event_encoded, current_hour]]
    )
    ai_prediction = ai_detector.predict(features)

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

    background_tasks.add_task(save_to_raw_logs, log)

    if final_risk >= 50:
        background_tasks.add_task(
            save_to_security_alerts,
            log,
            final_risk,  # type: ignore
            explanations,  # Передаем словарь целиком! # type: ignore
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

    env_port = os.getenv("PORT")
    if not env_port:
        raise RuntimeError("\n[ERROR] variable 'PORT' not set in .env!\n")

    try:
        port = int(env_port)
    except ValueError:
        raise ValueError(
            f"\n[ERROR] no correct PORT='{env_port}'. Please set an integer.\n"
        )

    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
