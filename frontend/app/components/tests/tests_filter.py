from collections import defaultdict
from typing import Callable

import flet as ft
from app.models import Test
from flet.core.dropdown import DropdownOption
from app.theme import theme_manager


class TestsFilter:
    def __init__(
        self,
        fields: dict[str, str],
        values: dict[str, str],
        tests: list[Test],
        on_filter_change: Callable[[ft.ControlEvent, dict[str, str]], ...],
    ):
        self._tests = tests
        self._fields = fields
        self._on_filter_change = on_filter_change
        # Only include fields with actual values in the state
        self._state = {k: v for k, v in values.items() if v}
        self._controls: dict[str, ft.Dropdown] = {}

    def _on_change(self, e: ft.ControlEvent, field: str, value: str):
        print(f"Filter change: field={field}, value={value}")
        # Update state with new value or remove if empty
        new_state = {**self._state}
        if value:
            new_state[field] = value
        else:
            new_state.pop(field, None)
        
        print(f"Old state: {self._state}")
        print(f"New state: {new_state}")
        
        if new_state != self._state:
            self._on_filter_change(e, new_state)
            self._state = new_state

    def _reset(self, e: ft.ControlEvent, field: str):
        print(f"Resetting filter: {field}")
        control = self._controls.get(field)
        if control is None:
            return

        # Remove the field from state
        new_state = {**self._state}
        new_state.pop(field, None)
        
        print(f"Reset - Old state: {self._state}")
        print(f"Reset - New state: {new_state}")
        
        # Update state first
        self._state = new_state
        
        # Clear the dropdown by setting value to None and forcing page update
        control.value = None
        e.page.update()
        
        # Then trigger the filter change
        self._on_filter_change(e, new_state)

    def render(self) -> ft.Control:
        options: dict[str, list[DropdownOption]] = defaultdict(list)

        for field in self._fields.keys():
            seen = set()
            for test in self._tests:
                value = getattr(test, field)
                if value in seen or value is None:
                    continue
                seen.add(value)
                options[field].append(ft.DropdownOption(key=value, content=ft.Text(value, color=theme_manager.colors.on_surface_variant)))

        filters_row = ft.ResponsiveRow(
            expand=True,
            expand_loose=True,
        )
        for field, label in self._fields.items():
            # Determine if dropdown has a value (activated state)
            has_value = bool(self._state.get(field))
                        
            filter_input = ft.Dropdown(
                hint_text=label,
                color=theme_manager.colors.on_surface_variant,
                border_color=theme_manager.colors.divider,
                focused_border_color=theme_manager.colors.primary,
                bgcolor=theme_manager.colors.surface,
                filled=False,  # Enable background color
                text_style=ft.TextStyle(
                    color=theme_manager.colors.on_surface if has_value else theme_manager.colors.on_surface_variant
                ),
                options=options[field],
                enable_filter=True,
                enable_search=True,
                helper_text=label,
                helper_style=ft.TextStyle(color=theme_manager.colors.on_surface_variant),
                expand=True,
                data=field,
                value=self._state.get(field) or None,  # Ensure None if no value
                on_blur=lambda e, f=field: self._on_change(
                    e, field=f, value=e.control.value
                ),
                on_change=lambda e, f=field: self._on_change(
                    e, field=f, value=e.control.value
                ),
                col=3,
                editable=True,
            )
            leading_icon = ft.IconButton(
                ft.Icons.CLOSE,
                icon_size=16,
                data=field,
                on_click=lambda e, f=field: self._reset(e, f),
            )
            filter_input.leading_icon = leading_icon
            filters_row.controls.append(filter_input)
            self._controls[field] = filter_input
        return filters_row
