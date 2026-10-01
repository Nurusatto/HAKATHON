from pydantic import BaseModel, Field, NonNegativeFloat, NonNegativeInt


class LogInput(BaseModel):
    user: str = Field(..., description="Имя или ID пользователя")
    event: str = Field(..., description="Тип события безопасности")
    ip: str = Field(..., description="IP-адрес источника")

    request_count_1m: NonNegativeInt = Field(
        ..., description="Кол-во запросов за последнюю минуту"
    )
    download_size_mb: NonNegativeFloat = Field(
        ..., description="Объем скачанных данных в МБ"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user": "user_4",
                    "event": "file_download",
                    "ip": "192.168.1.45",
                    "request_count_1m": 5,
                    "download_size_mb": 1.2,
                }
            ]
        }
    }
