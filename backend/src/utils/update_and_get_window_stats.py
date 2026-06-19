import time
from collections import defaultdict

sliding_windows = defaultdict(
    lambda: {"count": 0, "size": 0, "last_reset": time.time()}
)


def update_and_get_window_stats(ip_address: str, current_size_mb: float):

    now = time.time()
    window = sliding_windows[ip_address]


    if now - window["last_reset"] > 60:
        window["count"] = 1
        window["size"] = current_size_mb
        window["last_reset"] = now
    else:
        window["count"] += 1
        window["size"] += current_size_mb

    return window["count"], window["size"]
