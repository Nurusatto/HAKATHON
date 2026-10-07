from httpx import HTTPError
from postgrest.exceptions import APIError

from ..schemas import LogInput
from .supabase import supabase


def save_to_raw_logs(log: LogInput):
    """Таблица 1: Абсолютно все сырые логи"""
    try:
        data = {
            "username": log.user,
            "event_type": log.event,
            "source_ip": log.ip,
            "request_count_1m": log.request_count_1m,
            "download_size_mb": log.download_size_mb,
        }
        supabase.table("raw_logs").insert(data).execute()
    except (APIError, HTTPError) as e:
        print(f"[DB Error] Ошибка записи в raw_logs: {e}")
