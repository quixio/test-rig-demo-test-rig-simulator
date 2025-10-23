from typing import List, Optional, Tuple
import flet as ft

__all__ = ("ExternalLinksBar",)


class ExternalLinksBar:
    """A component that displays a horizontal bar of external links as buttons."""
    
    def __init__(
        self,
        links: List[Tuple[str, str]],
        title: Optional[str] = None,
    ):
        """
        Initialize the external links bar.
        
        Args:
            links: List of (url, label) tuples
            title: Optional title to display before the links
        """
        self._links = links
        self._title = title
    
    def render(self) -> ft.Control:
        """Render the external links bar."""
        if not self._links:
            return ft.Container()
        
        link_controls = []
        
        # Add title if provided
        if self._title:
            link_controls.append(
                ft.Text(
                    self._title,
                    weight=ft.FontWeight.BOLD,
                    color="#646471",
                )
            )
        
        # Add buttons for each link
        for url, label in self._links:
            link_controls.append(
                ft.OutlinedButton(
                    text=label,
                    on_click=lambda e, url=url: e.page.launch_url(url),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=4),
                    ),
                )
            )
        
        return ft.Container(
            content=ft.Row(
                controls=link_controls,
                spacing=10,
                wrap=True,
                alignment=ft.MainAxisAlignment.START,
            ),
        )
