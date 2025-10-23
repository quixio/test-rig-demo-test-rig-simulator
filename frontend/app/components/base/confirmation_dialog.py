import logging
from typing import Callable, Optional

import flet as ft
from app.components.base.buttons import FilledProgressButton

__all__ = ("ConfirmationDialog",)

from app.utils.exceptions import ObjectNotFound

logger = logging.getLogger(__name__)


class ConfirmationDialog:
    def __init__(
        self,
        title: ft.Control,
        content: ft.Control,
        on_confirm: Callable[[], ...],
        on_cancel: Optional[Callable[[], ...]] = None,
    ):
        self.title = title
        self.content = content
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self._error_msg_ref = ft.Ref[ft.Text]()
        self._dialog_ref = ft.Ref[ft.AlertDialog]()
        self._cancel_button_ref = ft.Ref[ft.OutlinedButton]()

    def render(self) -> ft.AlertDialog:
        confirm_button = FilledProgressButton(
            text="Confirm", 
            bgcolor="#0064FF", 
            color=ft.Colors.WHITE, 
            on_click=self._on_confirm
        )
        cancel_button = ft.OutlinedButton(
            "Cancel", 
            on_click=self._on_cancel, 
            ref=self._cancel_button_ref
        )
        error_msg = ft.Text(
            ref=self._error_msg_ref,
            visible=False,
            color=ft.Colors.ERROR,
            theme_style=ft.TextThemeStyle.TITLE_SMALL,
        )
        actions = ft.Column(
            [
                error_msg,
                ft.Row(
                    [confirm_button, cancel_button],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.END,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=self.title,
            content=self.content,
            actions=[actions],
            ref=self._dialog_ref,
        )
        return dialog

    def _on_confirm(self, e: ft.ControlEvent):
        self._cancel_button_ref.current.disabled = True
        self._cancel_button_ref.current.update()
        try:
            self.on_confirm()
            e.page.close(self._dialog_ref.current)
        except ObjectNotFound as exc:
            self._error_msg_ref.current.value = str(exc)
            self._error_msg_ref.current.visible = True
            self._error_msg_ref.current.update()
        except Exception:
            logger.exception("Exception failed")
            self._error_msg_ref.current.value = (
                "Request failed, please try again later."
            )
            self._error_msg_ref.current.visible = True
            self._error_msg_ref.current.update()
        finally:
            self._cancel_button_ref.current.disabled = False
            self._cancel_button_ref.current.update()

    def _on_cancel(self, e: ft.ControlEvent):
        if self.on_cancel:
            self.on_cancel()
        e.page.close(self._dialog_ref.current)
