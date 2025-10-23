import flet as ft


class Badge:
    def __init__(
        self,
        text: str,
        color: ft.ColorValue = ft.Colors.WHITE,
        bgcolor: ft.ColorValue = ft.Colors.BLUE_800,
        padding: int = 4,
        border_radius: int = 8,
    ):
        self._text = text
        self._color = color
        self._bgcolor = bgcolor
        self._padding = padding
        self._border_radius = border_radius

    def render(self) -> ft.Control:
        badge = ft.Container(
            ft.Text(
                self._text,
                style=ft.TextStyle(
                    color=self._color,
                ),
            ),
            bgcolor=self._bgcolor,
            border_radius=self._border_radius,
            padding=ft.padding.all(self._padding),
        )

        return badge
