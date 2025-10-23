import functools
import inspect
from typing import Optional

import flet as ft

__all__ = ("FilledProgressButton",)


class FilledProgressButton(ft.FilledButton):
    def __init__(self, *args, progress_text: Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._text = kwargs.get("text")
        self._bgcolor = kwargs.get("bgcolor")
        self._color = kwargs.get("color")
        self._progress_text = progress_text

    def disable(self):
        """
        Set "disabled" look manually because flet doesn't do that
        if custom colors are provided.
        """
        self.disabled = True
        self.bgcolor = ft.Colors.GREY_900
        self.color = ft.Colors.GREY_600
        self.text = self._progress_text or self._text
        self.update()

    def enable(self):
        """
        Enable the button back and restore original colors.
        """
        self.disabled = False
        self.bgcolor = self._bgcolor
        self.color = self._color
        self.text = self._text
        self.update()

    @ft.FilledButton.on_click.setter
    def on_click(self, handler):
        if inspect.iscoroutinefunction(handler):

            @functools.wraps(handler)
            async def wrapper(*args, **kwargs):
                self.disable()
                try:
                    await handler(*args, **kwargs)
                finally:
                    self.enable()

            ft.FilledButton.on_click.fset(self, wrapper)

        elif handler:

            @functools.wraps(handler)
            def wrapper(*args, **kwargs):
                self.disable()
                try:
                    handler(*args, **kwargs)
                finally:
                    self.enable()

            ft.FilledButton.on_click.fset(self, wrapper)
        else:
            ft.FilledButton.on_click.fset(self, handler)
