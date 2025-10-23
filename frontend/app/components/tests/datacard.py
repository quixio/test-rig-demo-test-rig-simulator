from typing import Optional, Union

import flet as ft
from flet.core.text_style import TextThemeStyle

__all__ = ("DataCard",)


class DataCard:
    def __init__(
        self,
        data: dict[str, Union[str, ft.Control]],
        min_leading_width: Optional[int],
        label_style: TextThemeStyle = ft.TextThemeStyle.TITLE_SMALL,
        title_style: TextThemeStyle = ft.TextThemeStyle.TITLE_MEDIUM,
        expand: Union[None, bool, int] = None,
    ):
        self.data = data
        self.min_leading_width = min_leading_width
        self.label_style = label_style
        self.title_style = title_style
        self.expand = expand

    def render(self) -> ft.Control:
        from app.theme import theme_manager
        tiles = [
            ft.ListTile(
                leading=ft.Text(label, theme_style=self.label_style, selectable=True),
                title=ft.Text(title, theme_style=self.title_style, selectable=True)
                if isinstance(title, str)
                else title,
                min_leading_width=self.min_leading_width,
                title_alignment=ft.ListTileTitleAlignment.TITLE_HEIGHT,
                dense=True,
            )
            for label, title in self.data.items()
        ]
        return ft.Card(
            content=ft.Column(tiles), 
            expand=self.expand,
            color=theme_manager.colors.surface
        )
