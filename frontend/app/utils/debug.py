import flet as ft


def highlight(element: ft.Control) -> ft.Control:
    """
    Adds a red border around the element and a badge with "expanded" status to
    help during debugging.
    """
    return ft.Container(
        element,
        border=ft.border.all(
            3, color=ft.Colors.RED if element.expand else ft.Colors.GREEN
        ),
        badge=ft.Badge(f"expanded:{element.expand}") if element.expand else None,
        expand=element.expand,
        expand_loose=element.expand_loose,
    )
