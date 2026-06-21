FROM python:3.11-slim

# Устанавливаем uv внутрь контейнера для быстрой сборки
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Назначаем рабочую папку внутри контейнера
WORKDIR /app

# Сначала копируем только файлы зависимостей (чтобы кэшировать сборку)
COPY pyproject.toml uv.lock ./

# Устанавливаем все библиотеки из pyproject.toml прямо в систему контейнера
RUN uv pip install --system -r pyproject.toml

# Копируем весь остальной код (включая папку src) в контейнер
COPY . .

CMD ["python", "-m", "src.main"]