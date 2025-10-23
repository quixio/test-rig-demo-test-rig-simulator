import flet as ft


class Placeholder:
    def __init__(self, text: str = "Not set"):
        self._text = text

    def render(self) -> ft.Control:
        return ft.Text(
            "Not set",
            color=ft.Colors.ON_SECONDARY_CONTAINER,
            theme_style=ft.TextThemeStyle.BODY_SMALL,
        )


PLACEHOLDER = Placeholder().render()
