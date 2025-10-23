import flet as ft
from app.components.base import Badge, ConfirmationDialog
from app.models import LogbookEntry
from app.store import STORE
from app.utils.date import format_date
from app.utils.routing import Router


class LogbookEntryTile:
    def __init__(self, entry: LogbookEntry, router: Router):
        self._entry = entry
        self._router = router

    def _on_delete(self, e: ft.ControlEvent):
        def on_confirm():
            STORE.delete_logbook_entry(test_id=test_id, entry_id=entry_id)
            self._router.refresh(e.page)

        entry_data = e.control.data
        entry_id, test_id = entry_data["id"], entry_data["test_id"]
        dialog = ConfirmationDialog(
            title=ft.Text("Please confirm"),
            content=ft.Text("Are you sure you want to delete the logbook entry?"),
            on_confirm=on_confirm,
        )
        e.page.open(dialog.render())

    def render(self) -> ft.Control:
        entry = self._entry

        sensors_badges = [
            Badge(text=sensor_id, bgcolor=ft.Colors.SECONDARY).render()
            for sensor_id in entry.sensor_ids
        ]
        sensors_row = (
            ft.Row(
                [
                    ft.Text("Parameters:", theme_style=ft.TextThemeStyle.TITLE_SMALL),
                    *sensors_badges,
                ],
                tight=True,
                alignment=ft.MainAxisAlignment.START,
            )
            if sensors_badges
            else ft.Row()
        )

        tile = ft.ExpansionTile(
            leading=ft.CircleAvatar(
                content=ft.Text(entry.operator[:1].capitalize()),
                color=ft.Colors.ON_TERTIARY,
                bgcolor=ft.Colors.TERTIARY,
            ),
            title=ft.Text(entry.operator),
            subtitle=ft.Column(
                [
                    sensors_row,
                    ft.Text(
                        format_date(entry.timestamp),
                        color=ft.Colors.ON_SECONDARY_CONTAINER,
                    ),
                ],
                tight=True,
            ),
            affinity=ft.TileAffinity.PLATFORM,
            maintain_state=True,
            text_color=ft.Colors.SECONDARY,
            controls_padding=ft.padding.all(10),
        )

        content_block = ft.Row(
            [
                ft.Container(
                    ft.Text(
                        entry.content,
                        selectable=True,
                        theme_style=ft.TextThemeStyle.BODY_LARGE,
                    ),
                    expand=True,
                    padding=20,
                    border_radius=8,
                    bgcolor=ft.Colors.SURFACE,
                )
            ],
            alignment=ft.MainAxisAlignment.START,
        )
        buttons_block = ft.Row(
            [
                ft.FilledButton(
                    "Edit",
                    icon=ft.Icons.EDIT,
                    data={"id": entry.id, "test_id": entry.test_id},
                    bgcolor=ft.Colors.SECONDARY,
                    on_click=lambda e: e.page.go(
                        f"/tests/{e.control.data['test_id']}/logbook/{e.control.data['id']}/edit",
                    ),
                ),
                ft.OutlinedButton(
                    "Delete",
                    icon=ft.Icons.DELETE,
                    data={"id": entry.id, "test_id": entry.test_id},
                    on_click=self._on_delete,
                ),
            ],
            alignment=ft.MainAxisAlignment.END,
        )

        tile.controls = [
            ft.Column(
                [
                    content_block,
                    buttons_block,
                ]
            )
        ]
        return tile
