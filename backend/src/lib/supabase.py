import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "Критические переменные SUPABASE_URL или SUPABASE_KEY не найдены в .env!"
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
