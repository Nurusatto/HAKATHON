import os
import random
import time

import requests

URL = os.getenv("GENERATOR_URL", "http://localhost:8000/protect-log")
TOTAL_LOGS = 150

# 1. Расширенный список пользователей (для более интересной статистики)
users = [
    "user_1",
    "user_2",
    "user_3",
    "user_4",
    "admin",
    "hr_manager",
    "guest_wifi",
    "dev_ops_main",
    "finance_dir",
    "sales_team_1",
    "external_consultant",
]

events = ["login_success", "login_failed", "file_download", "password_reset"]

# Расширенный блеклист IP
BANNED_IPS = [
    "185.220.101.5",
    "45.227.254.12",
    "198.51.100.42",
    "103.245.77.112",
    "185.156.174.4",
]


# Пулы IP-адресов для разных отделов (для реалистичности)
def get_random_ip():
    subnets = [
        "192.168.1",  # Общая сеть
        "192.168.10",  # Отдел разработки
        "192.168.20",  # Бухгалтерия и HR
        "10.0.4",  # VPN-пул для удаленщиков
    ]
    return f"{random.choice(subnets)}.{random.randint(2, 254)}"


print(
    f"Запуск расширенного генератора логов (Сценарий: {TOTAL_LOGS} событий для проверки алертов)..."
)

for i in range(1, TOTAL_LOGS + 1):
    is_attack = False
    attack_type = None

    # ---- ТРИГГЕРЫ АТАК НА РАЗНЫХ ЭТАПАХ ----
    # 1. Точечные проверки на ранних этапах
    if i == 15:
        is_attack = True
        attack_type = "blacklist"
    elif i == 32:
        is_attack = True
        attack_type = "brute_force"
    elif i == 55:
        is_attack = True
        attack_type = "dlp_leak_medium"  # Средний риск
    elif i == 77:
        is_attack = True
        attack_type = "api_abuse"

    # 2. Первая волна распределенной атаки (периодические аномалии)
    elif 100 <= i <= 115 and i % 3 == 0:
        is_attack = True
        attack_type = "suspicious_activity"  # Даст средний риск (60-80%)

    # 3. Финальный массированный штурм и попытка слива (150-185 логов)
    elif 150 <= i <= 185:
        # Смешаем атаки с легитимным шумом, чтобы IPS банил точечно
        if random.random() < 0.65:
            is_attack = True
            attack_type = "critical_flood"

    # ---- ГЕНЕРАЦИЯ ДАННЫХ ----
    if not is_attack:
        # 🟢 Обычный фоновый трафик
        user = random.choice(users)
        event = random.choice(events)
        ip = get_random_ip()

        # Разные профили поведения
        if user in ["user_4", "guest_wifi"]:
            req_count = random.randint(1, 4)
            download_size = round(random.uniform(0.1, 0.9), 2)
        elif user in ["dev_ops_main", "finance_dir"]:
            req_count = random.randint(5, 12)
            download_size = round(random.uniform(2.0, 8.5), 2)
        else:
            req_count = random.randint(2, 8)
            download_size = round(random.uniform(0.5, 4.0), 2)

    else:
        # 🔴 Контролируемые инциденты (разной степени тяжести)
        if attack_type == "blacklist":
            user = "external_consultant"
            event = "login_failed"
            ip = random.choice(BANNED_IPS)
            req_count = 3
            download_size = 0.0

        elif attack_type == "brute_force":
            user = "sales_team_1"
            event = "login_failed"
            ip = "192.168.10.45"
            req_count = 25  # Превышение лимита попыток входа
            download_size = 0.1

        elif attack_type == "dlp_leak_medium":
            user = "hr_manager"
            event = "file_download"
            ip = get_random_ip()
            req_count = 12
            download_size = 45.0  # Заметное превышение, но не критические гигабайты

        elif attack_type == "api_abuse":
            user = "user_2"
            event = "file_download"
            ip = "192.168.1.66"
            req_count = 180  # Высокая скорость, но ниже критического максимума
            download_size = 5.0

        elif attack_type == "suspicious_activity":
            # Имитация сканирования или прощупывания системы
            user = "guest_wifi"
            event = random.choice(["file_download", "login_failed"])
            ip = f"10.0.4.{random.randint(100, 150)}"
            req_count = random.randint(45, 70)  # Подозрительно для guest_wifi
            download_size = round(random.uniform(15.0, 30.0), 2)

        elif attack_type == "critical_flood":
            # Тяжелая комбо-атака для вылета в 100% риск и триггера IPS банов
            user = random.choice(["user_4", "guest_wifi", "external_consultant"])
            event = "file_download"
            # Разные атакующие IP, чтобы посмотреть, как разрастается блеклист в Redis
            ip = f"192.168.1.{random.randint(200, 245)}"
            req_count = random.choice([450, 550, 600])
            download_size = random.choice([1200.0, 1800.0, 2500.0])

    # Сборка payload
    payload = {
        "user": user,  # type: ignore
        "event": event,  # type: ignore
        "ip": ip,  # type: ignore
        "request_count_1m": req_count,  # type: ignore
        "download_size_mb": download_size,  # type: ignore
    }

    # Отправка
    try:
        print(f"[{i}/{TOTAL_LOGS}]")
        print(f"Отправлено: {payload}")

        response = requests.post(URL, json=payload, timeout=5)

        if response.status_code == 200:
            res_json = response.json()
            risk = res_json.get("risk", 0)
            expl = res_json.get("explanation", {})
            print(f"Ответ Бэкенда: Риск {risk}% | {expl}")
        else:
            print(f"Ошибка Бэкенда: Статус {response.status_code} | {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Не удалось отправить запрос: {e}")

    print("-" * 50)
    time.sleep(0.3)  # Чуть ускорил шаг, чтобы 200 логов прошли быстрее (около минуты)

print(f"Готово! Все {TOTAL_LOGS} логов успешно прогнали через AI Shield.")
