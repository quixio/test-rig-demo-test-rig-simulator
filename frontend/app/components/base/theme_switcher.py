"""
Theme switcher component for toggling between light and dark themes.
"""
import flet as ft

from app.theme import theme_manager


class ThemeSwitcher:
    """A toggle button for switching between light and dark themes"""
    
    def __init__(self, on_theme_change=None):
        self.on_theme_change = on_theme_change
    
    def render(self) -> ft.Control:
        def toggle_theme(e):
            theme_manager.toggle()
            
            # Update the page theme
            if e.page:
                e.page.theme_mode = ft.ThemeMode.DARK if theme_manager.mode == "dark" else ft.ThemeMode.LIGHT
                e.page.bgcolor = theme_manager.colors.background
                e.page.update()
            
            # Update the icon
            e.control.icon = ft.Icons.DARK_MODE if theme_manager.mode == "light" else ft.Icons.LIGHT_MODE
            e.control.tooltip = "Switch to dark theme" if theme_manager.mode == "light" else "Switch to light theme"
            if e.control.page:
                e.control.update()
            
            # Call custom callback if provided
            if self.on_theme_change:
                self.on_theme_change(theme_manager.mode)
        
        return ft.IconButton(
            icon=ft.Icons.DARK_MODE if theme_manager.mode == "light" else ft.Icons.LIGHT_MODE,
            tooltip="Switch to dark theme" if theme_manager.mode == "light" else "Switch to light theme",
            on_click=toggle_theme,
            icon_color={
                ft.ControlState.DEFAULT: theme_manager.colors.on_surface_variant,
                ft.ControlState.HOVERED: theme_manager.colors.primary,
            },
        )
