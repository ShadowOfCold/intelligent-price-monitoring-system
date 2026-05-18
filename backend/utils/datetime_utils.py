from datetime import datetime
from zoneinfo import ZoneInfo


IRKUTSK_TIMEZONE = ZoneInfo("Asia/Irkutsk")


def get_current_datetime() -> datetime:
    return datetime.now(IRKUTSK_TIMEZONE).replace(tzinfo=None)