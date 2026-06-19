import random
import requests
import time

URL = "http://localhost:8000/fake-log"

events = [
    "login_success",
    "login_failed",
    "file_download",
    "admin_access",
    "password_reset",
]

# Юзеры
users = ["user_1", "user_2", "user_3", "user_4", "admin", "hr_manager", "guest_wifi"]

BANNED_IP = [
    "192.168.1.132",
    "10.0.4.89",
    "185.220.101.5",
    "45.227.254.12",
    "172.16.42.100",
]

print("Запуск генератора логов...")

for i in range(50):
    # Примерно каждый 5-й лог будет аномальным
    is_attack = random.choice([True, False, False, False, False])

    if is_attack:
        user = random.choice(["user_2", "user_4", "guest_wifi"])
        req_count = random.choice([300, 450, 600])
        download_size = random.choice([500.0, 1200.0, 2500.0])
        event = "file_download"
    else:
        user = random.choice(users)

        if user == "admin":
            req_count = random.randint(30, 80)
            download_size = round(random.uniform(50.0, 300.0), 2)
            event = random.choice(["admin_access", "file_download", "login_success"])
        else:
            req_count = random.randint(1, 15)
            download_size = round(random.uniform(0.1, 6.0), 2)
            event = random.choice(events)

    if random.random() < 0.15:
        ip = random.choice(BANNED_IP)
    else:
        ip = f"192.168.1.{random.randint(1, 255)}"

    payload = {
        "user": user,
        "event": event,
        "ip": ip,
        "request_count_1m": req_count,
        "download_size_mb": download_size,
    }

    try:
        response = requests.post(URL, json=payload)
        res_data = response.json()

        print(f"[{i + 1}/50]")
        print("Отправлено:", payload)
        print(f"Ответ Бэкенда: Риск {res_data['risk']}% | {res_data['explanation']}")
        print("-" * 50)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

    time.sleep(0.6)

print("Готово. Отправлено 50 логов.")
