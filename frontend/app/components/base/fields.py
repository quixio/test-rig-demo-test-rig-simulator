import zoneinfo
from datetime import datetime
from typing import Optional

import flet as ft

__all__ = ("DateTimeField",)

from app.env import TESTMANAGER_TIMEZONE

DATETIME_FORMAT = "%d.%m.%Y %H:%M:%S"


class DateTimeField(ft.TextField):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        kwargs.setdefault("hint_text", "dd.mm.yyyy hh:mm:ss")
        kwargs.setdefault("on_blur", self._validate_datetime_format)
        super().__init__(*args, **kwargs)

    def _validate_datetime_format(self, _: ft.ControlEvent):
        value = self.value.strip()

        if not value:
            self.error_text = ""
            return

        try:
            # Attempt to parse it into a datetime object
            datetime.strptime(value, DATETIME_FORMAT)
            self.error_text = ""
        except ValueError:
            self.error_text = "Format must be: DD.MM.YYYY HH:MM:SS"

        self.update()

    @classmethod
    def parse(cls, value: Optional[str]) -> Optional[datetime]:
        if value:
            return datetime.strptime(value, DATETIME_FORMAT).replace(
                tzinfo=zoneinfo.ZoneInfo(TESTMANAGER_TIMEZONE)
            )
        return None
