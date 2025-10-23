"""
Theme configuration for the application.
Supports light and dark themes with easy switching.
"""
from dataclasses import dataclass
from typing import Dict, Literal

import flet as ft


@dataclass
class ThemeColors:
    """Theme color definitions"""
    # Primary colors
    primary: str
    primary_variant: str
    on_primary: str
    
    # Background colors
    background: str
    surface: str
    surface_variant: str
    
    # Icons colors
    active_icon: str
    inactive_icon: str
    
    card_background: str
    
    # Text colors
    on_background: str
    on_surface: str
    on_surface_variant: str
    
    # Status colors
    success: str
    error: str
    warning: str
    info: str
    
    # Additional colors
    divider: str
    shadow: str
    
    # Component specific colors
    button_primary_bg: str
    button_primary_text: str
    button_secondary_bg: str
    button_secondary_text: str
    badge_draft_bg: str
    badge_draft_text: str
    badge_progress_bg: str
    badge_progress_text: str
    badge_finished_bg: str
    badge_finished_text: str
    link_color: str
    link_hover_color: str


# Light theme (current colors)
LIGHT_THEME = ThemeColors(
    # Primary colors
    primary="#0064FF",
    primary_variant="#0050CC",
    on_primary="#FFFFFF",
    
    # Background colors
    background="#FFFFFF",
    surface="#F1F1F3",
    surface_variant="#fafafa",
    
    card_background="#fafafa",

    # Text colors
    on_background="#0A0B24",
    on_surface="#0A0B24",
    on_surface_variant="#646471",
    
    active_icon="#0A0B24",
    inactive_icon="#a2a2b0",

    # Status colors
    success="#13A963",
    error="#DC3545",
    warning="#FFC107",
    info="#0064FF",
    
    # Additional colors
    divider="#E0E0E0",
    shadow="#00000029",
    
    # Component specific colors
    button_primary_bg="#0064FF",
    button_primary_text="#FFFFFF",
    button_secondary_bg="#F1F1F3",
    button_secondary_text="#0A0B24",
    badge_draft_bg="#F1F1F3",
    badge_draft_text="#646471",
    badge_progress_bg="#0064FF",
    badge_progress_text="#FFFFFF",
    badge_finished_bg="#13A963",
    badge_finished_text="#FFFFFF",
    link_color="#0064FF",
    link_hover_color="#0050CC",
)


# Dark theme (placeholder colors - to be refined)
DARK_THEME = ThemeColors(
    # Primary colors
    primary="#4D94FF", # primary color
    primary_variant="#0064FF",
    on_primary="gold",
    
    # Background colors
    background="#1a1a1b", # page background
    surface="#2b2b34", # card background
    surface_variant="#2b2b34", # nav banner
    
    card_background="#2b2b34",
    
    # Text colors
    on_background="red",
    on_surface="#646471",
    on_surface_variant="#ffffff",
    
    active_icon="#ffffff",
    inactive_icon="#646471",

    # Status colors
    success="#4CAF50",
    error="#F44336",
    warning="#FF9800",
    info="#4D94FF",
    
    # Additional colors
    divider="#373737",
    shadow="#00000080",
    
    # Component specific colors
    button_primary_bg="#3d89ff",
    button_primary_text="#000000",
    button_secondary_bg="#2C2C2C",
    button_secondary_text="#E0E0E0",
    badge_draft_bg="#363641",
    badge_draft_text="#A0A0A0",
    badge_progress_bg="#4D94FF",
    badge_progress_text="#000000",
    badge_finished_bg="#4CAF50",
    badge_finished_text="#000000",
    link_color="#3d89ff",
    link_hover_color="#66a2ff",
)


ThemeMode = Literal["light", "dark"]


class ThemeManager:
    """Manages theme state and provides theme colors"""
    
    _instance = None
    _theme_mode: ThemeMode = "light"
    _themes: Dict[ThemeMode, ThemeColors] = {
        "light": LIGHT_THEME,
        "dark": DARK_THEME,
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def mode(self) -> ThemeMode:
        """Get current theme mode"""
        return self._theme_mode
    
    @mode.setter
    def mode(self, value: ThemeMode):
        """Set theme mode"""
        if value in self._themes:
            self._theme_mode = value
    
    @property
    def colors(self) -> ThemeColors:
        """Get current theme colors"""
        return self._themes[self._theme_mode]
    
    def toggle(self):
        """Toggle between light and dark themes"""
        self._theme_mode = "dark" if self._theme_mode == "light" else "light"
    
    def get_flet_theme(self) -> ft.Theme:
        """Get Flet theme object for current theme"""
        is_dark = self._theme_mode == "dark"
        colors = self.colors
        
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=colors.primary,
                on_primary=colors.on_primary,
                background=colors.background,
                on_background=colors.on_background,
                surface=colors.surface,
                on_surface=colors.on_surface,
                error=colors.error,
            ),
            # Additional theme properties can be added here
        )


# Global theme manager instance
theme_manager = ThemeManager()
