from typing import Callable, Optional

import flet as ft
from .models import Request


RouteHandler = Callable[[Request], ft.Control]
Route404Handler = Callable[[Request, str], ft.Control]


def default_handler_404(req: Request, message: Optional[str] = None) -> ft.Control:
    message = message or f"Page {req.url} is not found"

    return ft.Container(
        ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("404", theme_style=ft.TextThemeStyle.DISPLAY_SMALL),
                        ft.Text(message, theme_style=ft.TextThemeStyle.TITLE_LARGE),
                    ],
                    # Vertical center
                    alignment=ft.MainAxisAlignment.CENTER,
                    # Horizontal center
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                )
            ],
            expand=True,
        ),
        padding=200,
    )
