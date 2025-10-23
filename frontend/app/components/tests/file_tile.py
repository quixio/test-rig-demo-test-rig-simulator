import flet as ft
import humanize
from app.components.base import ConfirmationDialog
from app.models import TestFile
from app.store import STORE
from app.utils.date import format_date
from app.utils.routing import Router


class FileTile:
    def __init__(self, test_id: str, file: TestFile, router: Router):
        self._test_id = test_id
        self._file = file
        self._router = router

    def _on_delete(self, e: ft.ControlEvent):
        def on_confirm():
            STORE.delete_test_file(test_id=self._test_id, file_id=file_id)
            self._router.refresh(e.page)

        file_data = e.control.data
        file_id, filename = file_data["id"], file_data["name"]
        dialog = ConfirmationDialog(
            title=ft.Text("Please confirm"),
            content=ft.Text(f'Are you sure you want to delete file "{filename}"?'),
            on_confirm=on_confirm,
        )
        e.page.open(dialog.render())

    def render(self) -> ft.Control:
        title = ft.Text(f"{self._file.name}")
        subtitle = ft.Text(
            spans=[
                ft.TextSpan(humanize.naturalsize(self._file.size)),
                ft.TextSpan(", "),
                ft.TextSpan(
                    format_date(self._file.uploaded_at),
                ),
            ]
        )
        action_buttons = ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.DOWNLOAD,
                    icon_size=20,
                    data={"id": self._file.id, "name": self._file.name},
                    url_target=ft.UrlTarget.BLANK,
                    url=STORE.get_file_download_url(
                        test_id=self._test_id, file_id=self._file.id
                    ),
                    tooltip="Download file",
                ),
                # TODO: Share link button
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINED,
                    icon_size=20,
                    data={"id": self._file.id, "name": self._file.name},
                    on_click=self._on_delete,
                    tooltip="Delete file",
                ),
            ],
            tight=True,
        )

        tile = ft.ListTile(
            expand=True,
            title=title,
            subtitle=subtitle,
            trailing=action_buttons,
            dense=True,
        )
        return tile
