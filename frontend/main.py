import logging
import os
import sys

import flet as ft
from flet.fastapi import app as flet_app
from flet.core.page import Page

from app import views
from app.env import (
    TESTMANAGER_HOST,
    TESTMANAGER_PORT,
    TESTMANAGER_LOGLEVEL,
    is_quix_environment,
    get_default_theme,
)
from app.theme import theme_manager
from app.components.base.theme_switcher import ThemeSwitcher

flet_logger = logging.getLogger("flet")
flet_logger.setLevel(logging.INFO)

logger = logging.getLogger("app")
logger.setLevel(TESTMANAGER_LOGLEVEL)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(TESTMANAGER_LOGLEVEL)
formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


MAX_WIDTH = 1300

# TODO: Logs
# TODO: Debug mode to avoid returning tracebacks and exceptions
# TODO: Display 500

# Initialize theme from environment variable
theme_manager.mode = get_default_theme() if get_default_theme() in ["light", "dark"] else "light"

# Create router instance - import it from views where it's already configured
from app.views import router


async def main(page: Page):
    page.title = "Test Manager"
    page.fonts = {
        "Inter Regular": "/fonts/Inter-Regular.ttf",
        "Inter SemiBold": "/fonts/Inter-SemiBold.ttf",
    }
    
    # Set theme based on theme manager
    page.theme_mode = ft.ThemeMode.DARK if theme_manager.mode == "dark" else ft.ThemeMode.LIGHT
    page.bgcolor = theme_manager.colors.background
    
    # Create custom theme with our colors
    page.theme = ft.Theme(
        # Turn off mobile-like transition animations everywhere
        page_transitions=ft.PageTransitionsTheme(
            android=ft.PageTransitionTheme.NONE,
            ios=ft.PageTransitionTheme.NONE,
            linux=ft.PageTransitionTheme.NONE,
            windows=ft.PageTransitionTheme.NONE,
            macos=ft.PageTransitionTheme.NONE,
        ),
        color_scheme=ft.ColorScheme(
            primary=theme_manager.colors.primary,
            on_primary=theme_manager.colors.on_primary,
            background=theme_manager.colors.background,
            on_background=theme_manager.colors.on_background,
            surface=theme_manager.colors.surface,
            on_surface=theme_manager.colors.on_surface,
            error=theme_manager.colors.error,
        ),
        scaffold_bgcolor=theme_manager.colors.background,
        navigation_rail_theme=ft.NavigationRailTheme(bgcolor=theme_manager.colors.surface_variant),
        appbar_theme=ft.AppBarTheme(bgcolor=theme_manager.colors.surface_variant),
        font_family="Inter Regular"
    )
    
    # Check if running in Quix environment
    # First check environment variable
    is_quix_env = is_quix_environment()
    
    # For web apps, check query string using page route
    if page.route and '?' in page.route:
        query_string = page.route.split('?', 1)[1]
        from urllib.parse import parse_qs
        query_params = parse_qs(query_string)
        is_quix_env = is_quix_env or 'true' in query_params.get('isIframe', [])
    
    # Store query string to preserve it during navigation
    query_string = ""
    if page.route and '?' in page.route:
        query_string = '?' + page.route.split('?', 1)[1]
    
    # Create navigation buttons for the AppBar
    def create_nav_button(label: str, icon: ft.Icons, route: str, is_selected: bool = False):
        # Use theme colors
        icon_color = theme_manager.colors.primary if is_selected else theme_manager.colors.on_surface_variant
        text_color = theme_manager.colors.primary if is_selected else theme_manager.colors.on_surface_variant
        
        return ft.TextButton(
            content=ft.Row(
                [
                    ft.Icon(icon, size=20, color=icon_color),
                    ft.Text(label, size=16, weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL, color=text_color),
                ],
                spacing=5,
            ),
            on_click=lambda e: page.go(route + query_string),
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                } if not is_selected else {
                    ft.ControlState.DEFAULT: ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                },
                padding=ft.padding.symmetric(horizontal=15, vertical=10),
            ),
        )
    
    # Store navigation buttons in page data for updating selection
    page.nav_buttons = {
        "/": lambda selected: create_nav_button("Home", ft.Icons.HOME, "/", selected),
        "/tests": lambda selected: create_nav_button("Tests", ft.Icons.SCIENCE, "/tests", selected),
    }
    
    def update_nav_selection(current_route: str):
        nav_items = []
        # Prioritize longer matches
        routes = sorted(page.nav_buttons.keys(), key=len, reverse=True)
        selected_route = None
        for route in routes:
            if current_route.startswith(route):
                selected_route = route
                break
        
        for route in ["/", "/tests"]:  # Maintain order
            is_selected = route == selected_route
            nav_items.append(page.nav_buttons[route](is_selected))
        
        return nav_items
    
    # Initial navigation items
    nav_items = update_nav_selection(page.route)
    
    # Create theme switcher
    def on_theme_change(new_mode):
        # Refresh the page to apply new theme colors
        page.theme_mode = ft.ThemeMode.DARK if new_mode == "dark" else ft.ThemeMode.LIGHT
        page.bgcolor = theme_manager.colors.background
        page.theme.color_scheme.primary = theme_manager.colors.primary
        page.theme.color_scheme.on_primary = theme_manager.colors.on_primary
        page.theme.color_scheme.background = theme_manager.colors.background
        page.theme.color_scheme.on_background = theme_manager.colors.on_background
        page.theme.color_scheme.surface = theme_manager.colors.surface
        page.theme.color_scheme.on_surface = theme_manager.colors.on_surface
        page.theme.scaffold_bgcolor = theme_manager.colors.background
        page.theme.navigation_rail_theme.bgcolor = theme_manager.colors.surface_variant
        page.theme.appbar_theme.bgcolor = theme_manager.colors.surface_variant
        
        # Update logo based on theme
        if not is_quix_env and appbar.leading:
            appbar.leading = ft.Container(
                ft.Image("logo.svg" if new_mode == "dark" else "logo_dark.svg"), 
                padding=10, 
                on_click=lambda e: e.page.go("/")
            )
            page.update()
        
        # Refresh current route to update colors
        on_route_change(page.route)
    
    theme_switcher = ThemeSwitcher(on_theme_change=on_theme_change)
    
    # Create AppBar with conditional logo
    appbar = ft.AppBar(
        leading_width=100 if not is_quix_env else 0,
        leading=ft.Container(
            ft.Image("logo.svg" if theme_manager.mode == "dark" else "logo_dark.svg"), 
            padding=10, 
            on_click=lambda e: e.page.go("/")
        ) if not is_quix_env else None,
        title=ft.Row(
            nav_items,
            spacing=10,
        ),
        title_spacing=20 if not is_quix_env else 10,
        actions=[
            theme_switcher.render(),
        ],
    )
    page.appbar = appbar

    def on_route_change(route: str):
        # Check if we need to update is_quix_env based on query string
        nonlocal is_quix_env, query_string
        
        # Update query string if present
        if '?' in route:
            query_string = '?' + route.split('?', 1)[1]
            if 'isIframe=true' in query_string:
                is_quix_env = True
                # Update the logo visibility if needed
                if appbar.leading_width != (0 if is_quix_env else 100):
                    appbar.leading_width = 0 if is_quix_env else 100
                    appbar.leading = None if is_quix_env else ft.Container(
                        ft.Image("logo.svg" if theme_manager.mode == "dark" else "logo_dark.svg"), 
                        padding=10, 
                        on_click=lambda e: e.page.go("/" + query_string)
                    )
                    appbar.title_spacing = 10 if is_quix_env else 20
                    page.update()
        else:
            ft.Container(
                        ft.Image("logo.svg" if theme_manager.mode == "dark" else "logo_dark.svg"), 
                        padding=10, 
                        on_click=lambda e: e.page.go("/" + query_string)
                    )
        
        # Get a view to render (strip query params for routing)
        route_path = route.split('?')[0] if '?' in route else route
        view = router.get_view_for_url(route_path)

        # Wrap the view into the layout to limit max width but keep
        # internal positioning flexible
        view = ft.Column(
            [ft.Container(view, padding=40, width=MAX_WIDTH)],
            expand=11,
            expand_loose=True,
            scroll=ft.ScrollMode.AUTO,
        )

        # Update navigation selection in AppBar
        nav_items = update_nav_selection(route)
        appbar.title = ft.Row(
            nav_items,
            spacing=10,
        )

        # Since we removed the navigation rail, the root is just the view
        root = view

        # Update the current view
        page.views.clear()
        view = ft.View(route, [root], padding=0, appbar=appbar)
        page.views.append(view)
        page.update()

    page.on_route_change = lambda e: on_route_change(e.route)
    page.on_connect = lambda e: on_route_change(e.page.route)
    page.go(page.route)


if __name__ == "__main__":
    os.environ["FLET_FORCE_WEB_SERVER"] = "true"

    ft.app(
        target=main,
        host=TESTMANAGER_HOST,
        port=TESTMANAGER_PORT,
        assets_dir="assets",
    )
