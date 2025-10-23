import flet as ft


class Link:
    def __init__(
        self, url: str, label: str = "", color: str = None
    ):
        self._url = url
        self._label = label or url
        self._color = color or "#0064FF"

    def render(self) -> ft.Control:
        span = ft.TextSpan(
            text=self._label,
            url=self._url,
            url_target=ft.UrlTarget.BLANK,
            style=ft.TextStyle(
                color=self._color,
                decoration=ft.TextDecoration.UNDERLINE,
                decoration_color=self._color,
            ),
        )
        return ft.Text(spans=[span], tooltip=self._url)
