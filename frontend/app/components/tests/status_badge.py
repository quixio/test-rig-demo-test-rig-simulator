import flet as ft
from app.models import TestStatus
from app.theme import theme_manager

from ..base import Badge


class TestStatusBadge:
    def __init__(self, status: TestStatus):
        self._status = status

    def render(self) -> ft.Control:
        colors = theme_manager.colors
        if self._status == TestStatus.FINISHED:
            bgcolor = colors.badge_finished_bg
            color = colors.badge_finished_text
        elif self._status == TestStatus.IN_PROGRESS:
            bgcolor = colors.badge_progress_bg
            color = colors.badge_progress_text
        else:
            bgcolor = colors.badge_draft_bg
            color = colors.badge_draft_text
        badge = Badge(text=self._status.label, bgcolor=bgcolor, color=color).render()
        badge = ft.Row([badge], expand=False)
        return badge
