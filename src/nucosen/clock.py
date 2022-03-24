from datetime import datetime, timezone
from time import sleep


def waitUntil(limit: datetime):
    timeDelta = limit - datetime.now(timezone.utc)
    deltaSeconds = timeDelta.total_seconds()
    sleep(deltaSeconds if deltaSeconds > 0 else 0)
