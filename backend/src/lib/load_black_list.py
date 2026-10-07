from httpx import HTTPError
from postgrest.exceptions import APIError

from .supabase import supabase


def load_blacklist_from_db():
    try:
        print("[System] Обновление кэша Blacklist из Supabase...")
        response = (
            supabase.table("security_bl").select("*").eq("is_active", True).execute()
        )
        data = response.data or []

        # Пересобираем кэш
        banned_ips = {row["value"] for row in data if row["type"] == "ip"}  # type: ignore
        reasons = {row["value"]: row["reason"] for row in data if row["type"] == "ip"}  # type: ignore

        print(
            f"[System] Кэш блеклиста успешно обновлен. Загружено IP: {len(banned_ips)}"
        )
        return banned_ips, reasons
    except (APIError, HTTPError) as e:
        print(f"[System Critical Error] Не удалось загрузить Blacklist из БД: {e}")
        return set(), {}
