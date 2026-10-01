from typing import Any

from ..schemas import LogInput
from .supabase import supabase


def save_to_security_alerts(log: LogInput, risk: int, explanation: dict[str, Any]):
    """Таблица 3: Только инциденты и аналитика"""
    try:
        data = {
            "username": log.user,
            "event_type": log.event,
            "risk_score": risk,
            "explanation": explanation,
            "ip_address": log.ip,
        }
        supabase.table("security_alerts").insert(data).execute()
        print(
            f"[Alert System] ИНЦИДЕНТ ЗАФИКСИРОВАН! Пользователь: {log.user}, Риск: {risk}%"
        )
    except Exception as e:
        print(f"[DB Error] Ошибка записи в security_alerts: {e}")
