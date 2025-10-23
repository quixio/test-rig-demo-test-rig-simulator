from typing import Any, Callable, Optional

import flet as ft
from app.utils.exceptions import ValidationError

__all__ = ("Form",)


class Form:
    # TODO: Docs
    def __init__(
        self,
        fields: dict[str, ft.Control],
        on_submit: Callable[[dict[str, Any]], Optional[str]],
        submit_button: Optional[ft.Control] = None,
    ):
        self._fields = fields
        self._on_submit = on_submit
        self._submit_button = submit_button or ft.FilledButton(
            text="Save", on_click=self._submit, bgcolor="#0064FF", color=ft.Colors.WHITE
        )
        self._form_error_control = ft.Text(color=ft.Colors.RED)

    def render(self) -> ft.Control:
        return ft.Column(
            controls=[
                *self._fields.values(),
                self._form_error_control,
                self._submit_button,
            ],
        )

    def _submit(self, e: ft.ControlEvent):
        # Collect the submitted form data
        data = {}
        for label, field in self._fields.items():
            data[label] = field.value

        # Reset the form error messages
        self._reset_errors()

        # Update the "submit" button text and disable it to indicate the progress
        original_text = e.control.text
        original_icon = e.control.icon
        e.control.text = "Saving..."
        e.control.icon = ft.ProgressRing()
        e.control.disabled = True
        e.control.update()

        try:
            # Submit the form
            redirect_url = self._on_submit(data)
            if redirect_url:
                e.page.go(redirect_url)

        except ValidationError as exc:
            # Handle validation errors
            self._set_error(field=exc.field, message=exc.message)
        except Exception as exc:
            # Handle other unexpected errors
            self._set_error(field=None, message=f"Request failed: {str(exc)}")
        finally:
            # Enable the "submit" button back
            e.control.text = original_text
            e.control.icon = original_icon
            e.control.disabled = False
            e.control.update()

    def _reset_errors(self):
        self._form_error_control.value = None
        self._form_error_control.update()
        for field in self._fields.values():
            field.error_text = None
            field.update()

    def _set_error(self, message: str, field: Optional[str]):
        if field is None:
            self._form_error_control.value = message
            self._form_error_control.update()
        elif (form_field := self._fields.get(field)) is None:
            self._form_error_control.value = f'Field "{field}": {message}'
            self._form_error_control.update()
        else:
            form_field.error_text = message
            form_field.update()
