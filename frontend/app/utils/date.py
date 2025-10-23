import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from app.env import TESTMANAGER_TIMEZONE

_FORMAT = "%d.%m.%Y %H:%M:%S"

_TZ = ZoneInfo(TESTMANAGER_TIMEZONE)


def format_date(dt: Optional[datetime.datetime]) -> Optional[str]:
    """
    Format datetime to a fixed format and render it in a configured timezone.

    :param dt: datetime to format (optional).
    :return: string or None.
    """
    if dt is None:
        return None
    return dt.astimezone(tz=_TZ).strftime("%d.%m.%Y %H:%M:%S")
