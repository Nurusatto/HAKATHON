import logging
from typing import Any, cast

import numpy as np
from sklearn.ensemble import IsolationForest
from src.lib.supabase import supabase

# Настраиваем логгер
logger = logging.getLogger("uvicorn.error")


EVENT_MAPPING = {
    "normal_request": 0,
    "login_failed": 1,
    "password_reset": 2,
    "suspicious_ip": 3,
    "data_export": 4,
}


def train_ai_model_from_db() -> IsolationForest:
    logger.info(
        "[AI Engine] Exporting profiles from user_profiles to train 4D-model..."
    )
    try:
        response = supabase.table("user_profiles").select("*").execute()
        profiles = cast(list[dict[str, Any]], response.data)

        if not profiles or len(profiles) < 3:
            logger.warning(
                "[AI Engine] No data available. Enabling fallback 4D-dataset."
            )
            X_train = np.random.normal(
                loc=[10, 5, 0, 14], scale=[3, 1, 0, 2], size=(100, 4)
            )
            # Округляем категории и часы до целых чисел
            X_train[:, 2] = np.clip(np.round(X_train[:, 2]), 0, 4)
            X_train[:, 3] = np.clip(np.round(X_train[:, 3]), 0, 23)
        else:
            X_train = []
            normal_event = EVENT_MAPPING["normal_request"]

            for p in profiles:
                X_train.append(
                    [p["avg_requests_1m"], p["avg_download_mb"], normal_event, 14]
                )

                X_train.append(
                    [p["max_requests_1m"], p["max_download_mb"], normal_event, 16]
                )

                X_train.append(
                    [
                        p["avg_requests_1m"] * 1.1,
                        p["avg_download_mb"] * 1.1,
                        normal_event,
                        11,
                    ]
                )

            X_train = np.array(X_train)
            logger.info(
                f"[AI Engine] Successfully loaded {len(profiles)} profiles. "
                f"Formed 4D training points: {len(X_train)}"
            )

        model = IsolationForest(contamination=0.06, random_state=42)
        model.fit(X_train)

        logger.info(
            "[AI Engine] 4D-AI model successfully trained and ready for real-time anomaly detection!"
        )
        return model

    except Exception as e:
        logger.error(
            f"[AI Engine Critical Error] Error training model from database: {e}"
        )
        logger.info("[AI Engine] Deploying emergency local 4D model...")

        fallback_X = np.random.normal(
            loc=[10, 5, 0, 14], scale=[3, 1, 0, 3], size=(50, 4)
        )
        fallback_X[:, 2] = np.clip(np.round(fallback_X[:, 2]), 0, 4)
        fallback_X[:, 3] = np.clip(np.round(fallback_X[:, 3]), 0, 23)

        model = IsolationForest(contamination=0.1, random_state=42)
        model.fit(fallback_X)
        return model
