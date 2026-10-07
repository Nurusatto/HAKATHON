from httpx import HTTPError
from postgrest.exceptions import APIError

from .supabase import supabase


def load_security_rules_from_db():
    """Загружает активные правила из Supabase и пересобирает словарь кэша"""
    try:
        print("[System] Обновление кэша правил безопасности из Supabase...")
        response = (
            supabase.table("security_rules").select("*").eq("is_active", True).execute()
        )
        db_rules = response.data or []

        # Превращаем в плоский словарь для мгновенного поиска по O(1):
        rules_dict = {
            r["event_type"]: {"weight": r["risk_weight"], "desc": r["description"]}  # type: ignore
            for r in db_rules
        }
        print(f"[System] Кэш успешно обновлен. Загружено правил: {len(rules_dict)}")
        print(rules_dict)
        return rules_dict
    except (APIError, HTTPError) as e:
        print(f"[System Critical Error] Не удалось загрузить правила из БД: {e}")

        return {}
