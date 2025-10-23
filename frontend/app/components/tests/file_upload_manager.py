import asyncio
import dataclasses
import enum
import logging
from typing import Callable, Optional

import flet as ft
import humanize
from flet.core.alert_dialog import AlertDialog
from flet.core.file_picker import FilePickerResultEvent, FilePickerUploadEvent
from flet.core.types import MainAxisAlignment

from app.components.base.buttons import FilledProgressButton

logger = logging.getLogger(__name__)


class _FileStatus(enum.Enum):
    READY = 0
    UPLOADING = 1
    COMPLETED = 2
    FAILED = 3


class UploadFailedError(Exception): ...


@dataclasses.dataclass
class _State:
    # TODO: Support non-unique filenames
    files_statuses: dict[str, _FileStatus] = dataclasses.field(default_factory=dict)

    def set_progress(self, filename: str, progress: float, error: Optional[str] = None):
        if error:
            status = _FileStatus.FAILED
        elif progress is None:
            status = _FileStatus.READY
        elif 0 < progress < 1:
            status = _FileStatus.UPLOADING
        elif progress >= 1:
            status = _FileStatus.COMPLETED
        else:
            status = _FileStatus.READY

        self.files_statuses[filename] = status

    @property
    def failed(self) -> bool:
        return any(
            status == _FileStatus.FAILED for status in self.files_statuses.values()
        )

    @property
    def completed(self) -> bool:
        completed_files = [
            f for f, s in self.files_statuses.items() if s == _FileStatus.COMPLETED
        ]
        return (
            bool(completed_files)
            and not self.failed
            and len(completed_files) == len(self.files_statuses)
        )


class FileUploadManager:
    def __init__(
        self,
        width: int,
        height: int,
        upload_url_callback: Callable[[str], str],
        on_success: Optional[Callable[[ft.Page], ...]] = None,
    ):
        self._width = width
        self._height = height
        self._files_list = ft.Column()
        self._file_picker = ft.FilePicker(
            on_result=self._on_files_picked, on_upload=self._on_upload_progress_update
        )
        self._state = _State()
        self._upload_url_callback = upload_url_callback
        self._confirm_button_ref = ft.Ref[ft.FilledButton]()
        self._cancel_button_ref = ft.Ref[ft.OutlinedButton]()
        self._error_msg_ref = ft.Ref[ft.Text]()
        self._dialog_ref = ft.Ref[ft.AlertDialog]()
        self._on_success = on_success

    def render(self) -> ft.FilePicker:
        return self._file_picker

    def _render_dialog(self) -> ft.Control:
        header = ft.Row(
            [
                ft.Text("Files", theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
            ],
            alignment=MainAxisAlignment.SPACE_BETWEEN,
        )

        self._update_files_list()
        content = ft.Column(
            width=self._width,
            height=self._height,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Column(
                    [
                        header,
                        ft.Divider(),
                        self._files_list,
                    ]
                ),
            ],
            tight=True,
        )

        error_msg = ft.Text(
            ref=self._error_msg_ref,
            visible=False,
            color=ft.Colors.ERROR,
            theme_style=ft.TextThemeStyle.TITLE_SMALL,
        )
        confirm_button = FilledProgressButton(
            text="Upload",
            progress_text="Uploading...",
            ref=self._confirm_button_ref,
            icon=ft.Icons.UPLOAD_FILE,
            bgcolor="#0064FF",
            color=ft.Colors.WHITE,
            on_click=self._on_confirm,
        )
        cancel_button = ft.OutlinedButton(
            "Cancel",
            ref=self._cancel_button_ref,
            icon=ft.Icons.CANCEL,
            on_click=self._on_cancel,
        )

        dialog = AlertDialog(
            ref=self._dialog_ref,
            modal=True,
            title="Upload files",
            content=content,
            actions=[
                ft.Column(
                    [
                        error_msg,
                        ft.Row(
                            [confirm_button, cancel_button],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                )
            ],
        )
        return dialog

    def _update_files_list(self, exclude_id: Optional[int] = None) -> None:
        if not self._file_picker.result or not self._file_picker.result.files:
            self._files_list.controls.clear()
            return

        if exclude_id is not None:
            for i, file in enumerate(self._file_picker.result.files):
                if file.id == exclude_id:
                    self._file_picker.result.files.pop(i)

        self._files_list.controls = [
            ft.ListTile(
                title=ft.Text(f.name),
                subtitle=ft.Text(humanize.naturalsize(f.size)),
                dense=True,
                data=f.id,
            )
            for f in self._file_picker.result.files
        ]

    async def _upload(self):
        if not self._file_picker.result or not self._file_picker.result.files:
            return

        upload_list = []
        for f in self._file_picker.result.files:
            self._state.set_progress(filename=f.name, progress=0)
            try:
                upload_url = self._upload_url_callback(f.name)
                logger.info(f"Got upload URL for {f.name}: {upload_url}")
                upload_list.append(
                    ft.FilePickerUploadFile(
                        name=f.name,
                        upload_url=upload_url,
                        method="POST",
                    )
                )
            except Exception as ex:
                logger.error(f"Failed to get upload URL for {f.name}: {ex}")
                raise
                
        # Start the upload
        logger.info(f"Starting upload of {len(upload_list)} files")
        self._file_picker.upload(upload_list)

        # Wait until the upload completes of fails before closing the modal
        # The uploading is asynchronous, so we must poll its status in separately
        timeout = 60  # 60 seconds timeout
        start_time = asyncio.get_event_loop().time()
        while not (self._state.completed or self._state.failed):
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise UploadFailedError("Upload timed out after 60 seconds")
            await asyncio.sleep(0.1)

        if self._state.completed:
            logger.info("Upload completed successfully")
            return
        elif self._state.failed:
            logger.error("Upload failed")
            raise UploadFailedError("Failed to upload files, try again.")

    def _on_upload_progress_update(self, e: FilePickerUploadEvent):
        progress_pct = (e.progress * 100) if e.progress is not None else 0
        logger.info(f"Upload progress for {e.file_name}: {progress_pct:.1f}%, error: {e.error}")
        self._state.set_progress(
            filename=e.file_name, progress=e.progress or 0, error=e.error
        )

    def _on_files_picked(self, e: FilePickerResultEvent):
        if e.files:
            e.page.open(self._render_dialog())

    async def _on_confirm(self, e: ft.ControlEvent):
        self._cancel_button_ref.current.disabled = True
        self._cancel_button_ref.current.update()

        try:
            await self._upload()
        except Exception as ex:
            logger.exception("Failed to upload files")
            error_msg = f"Failed to upload files: {str(ex)}"
            self._error_msg_ref.current.value = error_msg
            self._error_msg_ref.current.visible = True
            self._error_msg_ref.current.update()
            # Also show a snackbar for better visibility
            e.page.snack_bar = ft.SnackBar(content=ft.Text(error_msg))
            e.page.snack_bar.open = True
            e.page.update()
        else:
            e.page.close(self._dialog_ref.current)
            if self._on_success:
                self._on_success(e.page)
        finally:
            self._cancel_button_ref.current.disabled = False
            self._cancel_button_ref.current.update()

    def _on_cancel(self, e: ft.ControlEvent):
        # Clean up the picked files on modal close
        if self._file_picker.result and self._file_picker.result.files:
            self._file_picker.result.files.clear()
        e.page.close(self._dialog_ref.current)
