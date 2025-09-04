import time
from datetime import datetime


def get_epoch_ms() -> int:
    """Get current time in milliseconds since epoch"""
    return int(time.time() * 1000)


def datetime_to_epoch_ms(dt: datetime) -> int:
    """Convert datetime to milliseconds since epoch"""
    return int(dt.timestamp() * 1000)


def epoch_ms_to_datetime(epoch_ms: int) -> datetime:
    """Convert milliseconds since epoch to datetime"""
    return datetime.fromtimestamp(epoch_ms / 1000)

