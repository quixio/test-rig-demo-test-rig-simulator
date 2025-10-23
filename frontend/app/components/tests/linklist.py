import flet as ft
from app.models import TestLink
from flet.core.text_style import TextStyle
from flet.core.types import UrlTarget

from ..base import Placeholder


class LinkList:
    def __init__(self, links: list[TestLink]):
        self.links = links

    def render(self) -> ft.Control:
        if not self.links:
            return Placeholder().render()

        spans = []
        for i, link in enumerate(self.links, start=1):
            spans.append(
                ft.TextSpan(
                    text=link.label or link.url,
                    url=link.url,
                    url_target=UrlTarget.BLANK,
                    style=TextStyle(
                        color=ft.Colors.BLUE, decoration=ft.TextDecoration.UNDERLINE
                    ),
                )
            )
            if i < len(self.links):
                spans.append(ft.TextSpan(", "))

        return ft.Text(spans=spans, selectable=True)
