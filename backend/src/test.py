# import os
# from contextlib import asynccontextmanager
# from datetime import datetime, timezone  # Добавили timezone
# from dotenv import load_dotenv
# from fastapi import BackgroundTasks, FastAPI, HTTPException
# import numpy as np

# from src.lib import (
#     load_blacklist_from_db,
#     load_security_rules_from_db,
#     save_to_raw_logs,
#     save_to_security_alerts,
# )
# from src.schemas import LogInput
# from .ML import train_ai_model_from_db
# import redis.asyncio as aioredis
# from src.lib.supabase import supabase  # Клиент supabase

# load_dotenv()

# ai_detector = None
# cached_security_rules = {}
# cached_banned_ips = set()
# blacklist_reasons = {}
# cached_user_profiles = {}  # Кэш для профилей пользователей
# redis_client: aioredis.Redis = None  # type: ignore


# def load_user_profiles_from_db():
#     """Загрузка профилей пользователей из Supabase для кэширования"""
#     try:
#         response = supabase.table("user_profiles").select("*").execute()
#         profiles = {row["username"]: row for row in response.data}  # type: ignore
#         print(
#             f"[Cache System] Успешно загружено профилей пользователей: {len(profiles)}"
#         )
#         return profiles
#     except Exception as e:
#         print(f"[DB Error] Ошибка загрузки профилей пользователей: {e}")
#         return {}


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global \
#         ai_detector, \
#         cached_security_rules, \
#         cached_banned_ips, \
#         blacklist_reasons, \
#         cached_user_profiles, \
#         redis_client

#     redis_client = aioredis.from_url("redis://redis:6379", decode_responses=True)

#     ai_detector = train_ai_model_from_db()
#     cached_security_rules = load_security_rules_from_db()
#     cached_banned_ips, blacklist_reasons = load_blacklist_from_db()
#     cached_user_profiles = load_user_profiles_from_db()
#     yield
#     await redis_client.close()


# app = FastAPI(title="AI Shield SIEM Engine", lifespan=lifespan)


# @app.get("/")
# def hello():
#     return {"message": "AI SHIELD"}


# @app.post("/protect-log")
# async def process_log(log: LogInput, background_tasks: BackgroundTasks):
#     global \
#         ai_detector, \
#         cached_security_rules, \
#         cached_banned_ips, \
#         blacklist_reasons, \
#         cached_user_profiles

#     # 1. Проверяем, не забанен ли IP в Redis IPS прямо сейчас
#     is_banned = await redis_client.get(f"ban:{log.ip}")
#     if is_banned:
#         raise HTTPException(
#             status_code=403,
#             detail=f"Access Denied. Your IP {log.ip} is temporarily blocked by AI Shield IPS. Reason: {is_banned}",
#         )

#     # Добавляем лог в фоновое сохранение в сырые логи
#     background_tasks.add_task(save_to_raw_logs, log)

#     # Токенизируем событие для ИИ
#     event_mapping = {
#         "normal_request": 0,
#         "login_failed": 1,
#         "password_reset": 2,
#         "suspicious_ip": 3,
#         "data_export": 4,
#         "file_download": 5,
#         "admin_access": 6,
#         "login_success": 7,
#     }
#     event_code = event_mapping.get(log.event, 0)

#     # 🔥 ИСПРАВЛЕНО: Теперь используем современный timezone-aware подход вместо utcnow()
#     current_hour = datetime.now(timezone.utc).hour

#     # Входной вектор для 4D Isolation Forest
#     features = np.array(
#         [[log.request_count_1m, log.download_size_mb, event_code, current_hour]]
#     )

#     ai_score = 0
#     if ai_detector is not None:
#         try:
#             # Считаем оценку аномальности
#             anomaly_score = ai_detector.score_samples(features)[0]
#             if anomaly_score < -0.4:
#                 ai_score = int((abs(anomaly_score) - 0.4) * 250)
#         except Exception as e:
#             print(f"[AI Predict Error] Ошибка инференса модели: {e}")

#     base_risk = max(0, min(100, ai_score))

#     final_risk = base_risk
#     explanations = {}

#     if ai_score > 40:
#         explanations["ai_analytics"] = (
#             f"Зафиксирована потенциальная атака (API Abuse / Аномальный трафик). "
#             f"Интенсивность от IP {log.ip} составила {log.request_count_1m} запр/мин, "
#             f"а общий объем переданных данных: {log.download_size_mb} МБ, что нетипично для времени суток {current_hour}:00."
#         )

#     if log.ip in cached_banned_ips:
#         final_risk = 100
#         explanations["blacklist"] = (
#             f"[Блеклист]: Зафиксирован запрос с заблокированного IP. "
#             f"Причина бана: {blacklist_reasons.get(log.ip, 'подозрительная активность')}"
#         )

#     rules_to_check = (
#         cached_security_rules.values()
#         if isinstance(cached_security_rules, dict)
#         else cached_security_rules
#     )

#     if rules_to_check:
#         for rule in rules_to_check:
#             if isinstance(rule, dict) and rule.get("event_type") == log.event:
#                 explanations["static_rules"] = (
#                     f"[База Правил]: {rule.get('description', '')}"
#                 )
#                 final_risk = max(final_risk, rule.get("severity_score", 0))

#     # 4. Проверка поведенческих профилей пользователей
#     user_profile = cached_user_profiles.get(log.user)
#     if user_profile and isinstance(user_profile, dict):
#         # Проверка DLP (Утечка данных)
#         if log.download_size_mb > user_profile.get("max_download_mb", 99999):
#             leak_ratio = round(
#                 log.download_size_mb / user_profile["max_download_mb"], 1
#             )
#             explanations["dlp_leak_detection"] = (
#                 f"Потенциальная утечка данных (DLP). Объем скачивания ({log.download_size_mb} МБ) "
#                 f"превышает максимальный исторический порог пользователя ({user_profile['max_download_mb']} МБ) в {leak_ratio} раз."
#             )

#             # Если превышение лимита скачивания в 10 раз и более — это 100% инцидент слива
#             if leak_ratio >= 10.0:
#                 final_risk = 100
#             else:
#                 final_risk = max(final_risk, 85)

#         if log.request_count_1m > user_profile.get("max_requests_1m", 99999):
#             request_ratio = round(
#                 log.request_count_1m / user_profile["max_requests_1m"], 1
#             )
#             explanations["profile_anomaly_detected"] = (
#                 f"Критическое аномальное поведение для аккаунта '{log.user}'. "
#                 f"Количество запросов ({log.request_count_1m}) превысило его норму ({user_profile['max_requests_1m']}) в {request_ratio} раз."
#             )

#             # Если частота запросов превышает норму в 15 раз и более — это жесткий Flood
#             if request_ratio >= 15.0:
#                 final_risk = 100
#             else:
#                 final_risk = max(final_risk, 80)

#     if final_risk >= 80:
#         background_tasks.add_task(
#             save_to_security_alerts, log, final_risk, explanations
#         )

#         if "dlp_leak_detection" in explanations:
#             reason_text = "DLP: Попытка несанкционированной утечки данных"
#         elif "profile_anomaly_detected" in explanations:
#             reason_text = (
#                 f"Anomaly: Критическое превышение лимитов активности профиля {log.user}"
#             )
#         else:
#             reason_text = "Критический уровень риска (API Abuse/Аномалии)"

#         # Баним вредоносный IP в Redis на 60 секунд
#         await redis_client.set(f"ban:{log.ip}", reason_text, ex=60)
#         print(
#             f"[Redis IPS] IP {log.ip} временно заблокирован на 60 секунд за риск {final_risk}%!"
#         )

#     return {"status": "ok", "risk": final_risk, "explanation": explanations}


# @app.post("/api/v1/retrain")
# async def retrain_model():
#     global \
#         ai_detector, \
#         cached_security_rules, \
#         cached_banned_ips, \
#         blacklist_reasons, \
#         cached_user_profiles

#     ai_detector = train_ai_model_from_db()
#     cached_security_rules = load_security_rules_from_db()
#     cached_banned_ips, blacklist_reasons = load_blacklist_from_db()
#     cached_user_profiles = load_user_profiles_from_db()

#     return {
#         "status": "success",
#         "message": "Модель ИИ успешно переобучена, кэш правил, профилей и блеклиста синхронизирован!",
#     }


# if __name__ == "__main__":
#     import uvicorn

#     env_port = os.getenv("API_PORT")
#     if not env_port:
#         raise RuntimeError("\n[ERROR] variable 'API_PORT' not set in .env")
#     uvicorn.run("src.main:app", host="0.0.0.0", port=int(env_port))
# FAZA 2

# import os
# from contextlib import asynccontextmanager
# from datetime import datetime, timezone
# from dotenv import load_dotenv
# from fastapi import BackgroundTasks, FastAPI, HTTPException
# import numpy as np
# from typing import Any, cast

# from src.lib import (
#     load_blacklist_from_db,
#     load_security_rules_from_db,
#     save_to_raw_logs,
#     save_to_security_alerts,
# )
# from src.schemas import LogInput
# from .ML import train_ai_model_from_db
# import redis.asyncio as aioredis
# from src.lib.supabase import supabase  # Клиент supabase

# load_dotenv()

# ai_detector = None
# cached_security_rules = {}
# cached_banned_ips = set()
# blacklist_reasons = {}
# cached_user_profiles = {}  # Кэш для профилей пользователей
# redis_client: aioredis.Redis = None  # type: ignore


# def load_user_profiles_from_db():
#     """Загрузка профилей пользователей из Supabase для кэширования"""
#     try:
#         response = supabase.table("user_profiles").select("*").execute()
#         profiles = {row["username"]: row for row in response.data}  # type: ignore
#         print(
#             f"[Cache System] Успешно загружено профилей пользователей: {len(profiles)}"
#         )
#         return profiles
#     except Exception as e:
#         print(f"[DB Error] Ошибка загрузки профилей пользователей: {e}")
#         return {}


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global \
#         ai_detector, \
#         cached_security_rules, \
#         cached_banned_ips, \
#         blacklist_reasons, \
#         cached_user_profiles, \
#         redis_client

#     redis_client = aioredis.from_url("redis://redis:6379", decode_responses=True)

#     ai_detector = train_ai_model_from_db()
#     cached_security_rules = load_security_rules_from_db()
#     cached_banned_ips, blacklist_reasons = load_blacklist_from_db()
#     cached_user_profiles = load_user_profiles_from_db()
#     yield
#     await redis_client.close()


# app = FastAPI(title="AI Shield SIEM Engine", lifespan=lifespan)


# @app.get("/")
# def hello():
#     return {"message": "AI SHIELD"}


# @app.post("/protect-log")
# async def process_log(log: LogInput, background_tasks: BackgroundTasks):
#     global \
#         ai_detector, \
#         cached_security_rules, \
#         cached_banned_ips, \
#         blacklist_reasons, \
#         cached_user_profiles

#     is_banned = await redis_client.get(f"ban:{log.ip}")
#     if is_banned:
#         raise HTTPException(
#             status_code=403,
#             detail=f"Access Denied. Your IP {log.ip} is temporarily blocked by AI Shield IPS. Reason: {is_banned}",
#         )

#     background_tasks.add_task(save_to_raw_logs, log)

#     event_mapping = {
#         "normal_request": 0,
#         "login_failed": 1,
#         "password_reset": 2,
#         "suspicious_ip": 3,
#         "data_export": 4,
#         "file_download": 5,
#         "admin_access": 6,
#         "login_success": 7,
#     }
#     event_code = event_mapping.get(log.event, 0)
#     current_hour = datetime.now(timezone.utc).hour

#     # Входной вектор для 4D Isolation Forest
#     features = np.array(
#         [[log.request_count_1m, log.download_size_mb, event_code, current_hour]]
#     )

#     ai_score = 0
#     if ai_detector is not None:
#         try:
#             # Считаем
#             anomaly_score = ai_detector.score_samples(features)[0]
#             if anomaly_score < -0.4:
#                 ai_score = int((abs(anomaly_score) - 0.4) * 250)
#         except Exception as e:
#             print(f"[AI Predict Error] Ошибка инференса модели: {e}")

#     base_risk = max(0, min(100, ai_score))

#     final_risk = base_risk
#     explanations = {}

#     if ai_score > 40:
#         explanations["ai_analytics"] = (
#             f"Зафиксирована потенциальная атака (API Abuse / Аномальный трафик). "
#             f"Интенсивность от IP {log.ip} составила {log.request_count_1m} запр/мин, "
#             f"а общий объем переданных данных: {log.download_size_mb} МБ, что нетипично для времени суток {current_hour}:00."
#         )

#     if log.ip in cached_banned_ips:
#         final_risk = 100
#         explanations["blacklist"] = (
#             f"[Блеклист]: Зафиксирован запрос с заблокированного IP. "
#             f"Причина бана: {blacklist_reasons.get(log.ip, 'подозрительная активность')}"
#         )

#     rules_to_check = (
#         cached_security_rules.values()
#         if isinstance(cached_security_rules, dict)
#         else cached_security_rules
#     )

#     if rules_to_check:
#         for rule in rules_to_check:
#             if isinstance(rule, dict) and rule.get("event_type") == log.event:
#                 explanations["static_rules"] = (
#                     f"[База Правил]: {rule.get('description', '')}"
#                 )
#                 raw_severity = rule.get("severity_score")
#                 if isinstance(raw_severity, (int, float)) or isinstance(
#                     raw_severity, str
#                 ):
#                     severity = int(raw_severity)
#                 else:
#                     severity = 0

#                 final_risk = max(final_risk, severity)

#     # 4. Проверка поведенческих профилей пользователей
#     user_profile = cached_user_profiles.get(log.user)
#     if user_profile and isinstance(user_profile, dict):
#         # 🔥 ИСПРАВЛЕНО: Достаем лимиты с явным приведением типов для безопасного сравнения/деления
#         raw_download = user_profile.get("max_download_mb")
#         raw_requests = user_profile.get("max_requests_1m")

#         raw_download = user_profile.get("max_download_mb")
#         raw_requests = user_profile.get("max_requests_1m")

#         max_download = (
#             float(raw_download)
#             if isinstance(raw_download, (int, float, str))
#             else 99999.0
#         )
#         max_requests = (
#             int(raw_requests) if isinstance(raw_requests, (int, float, str)) else 99999
#         )

#         # Проверка DLP (Утечка данных)
#         if log.download_size_mb > max_download:
#             leak_ratio = round(log.download_size_mb / max_download, 1)
#             explanations["dlp_leak_detection"] = (
#                 f"Потенциальная утечка данных (DLP). Объем скачивания ({log.download_size_mb} МБ) "
#                 f"превышает максимальный исторический порог пользователя ({max_download} МБ) в {leak_ratio} раз."
#             )

#             # Если превышение лимита скачивания в 10 раз и более — это 100% инцидент слива
#             if leak_ratio >= 10.0:
#                 final_risk = 100
#             else:
#                 final_risk = max(final_risk, 85)

#         # Проверка флуда запросами
#         if log.request_count_1m > max_requests:
#             request_ratio = round(log.request_count_1m / max_requests, 1)
#             explanations["profile_anomaly_detected"] = (
#                 f"Критическое аномальное поведение для аккаунта '{log.user}'. "
#                 f"Количество запросов ({log.request_count_1m}) превысило его норму ({max_requests}) в {request_ratio} раз."
#             )

#             # Если частота запросов превышает норму в 15 раз и более — это жесткий Flood
#             if request_ratio >= 15.0:
#                 final_risk = 100
#             else:
#                 final_risk = max(final_risk, 80)

#     if final_risk >= 80:
#         # 🔥 ИСПРАВЛЕНО: Передаем explanations как JSON-строку, так как функция ожидает тип str
#         background_tasks.add_task(
#             save_to_security_alerts, log, final_risk, cast(Any, explanations)
#         )

#         if "dlp_leak_detection" in explanations:
#             reason_text = "DLP: Попытка несанкционированной утечки данных"
#         elif "profile_anomaly_detected" in explanations:
#             reason_text = (
#                 f"Anomaly: Критическое превышение лимитов активности профиля {log.user}"
#             )
#         else:
#             reason_text = "Критический уровень риска (API Abuse/Аномалии)"

#         # Баним вредоносный IP в Redis на 60 секунд
#         await redis_client.set(f"ban:{log.ip}", reason_text, ex=60)
#         print(
#             f"[Redis IPS] IP {log.ip} временно заблокирован на 60 секунд за риск {final_risk}%!"
#         )

#     return {"status": "ok", "risk": final_risk, "explanation": explanations}


# @app.post("/api/v1/retrain")
# async def retrain_model():
#     global \
#         ai_detector, \
#         cached_security_rules, \
#         cached_banned_ips, \
#         blacklist_reasons, \
#         cached_user_profiles

#     ai_detector = train_ai_model_from_db()
#     cached_security_rules = load_security_rules_from_db()
#     cached_banned_ips, blacklist_reasons = load_blacklist_from_db()
#     cached_user_profiles = load_user_profiles_from_db()

#     return {
#         "status": "success",
#         "message": "Модель ИИ успешно переобучена, кэш правил, профилей и блеклиста синхронизирован!",
#     }


# if __name__ == "__main__":
#     import uvicorn

#     env_port = os.getenv("API_PORT")
#     if not env_port:
#         raise RuntimeError("\n[ERROR] variable 'API_PORT' not set in .env")
#     uvicorn.run("src.main:app", host="0.0.0.0", port=int(env_port))
