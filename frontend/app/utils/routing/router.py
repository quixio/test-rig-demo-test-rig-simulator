import logging
import re
from typing import Optional
from urllib.parse import parse_qs, urlparse

import flet as ft
import repath

from ..exceptions import ObjectNotFound
from .handlers import Route404Handler, RouteHandler, default_handler_404
from .models import Request

__all__ = ("Router",)

logger = logging.getLogger(__name__)


class Router:
    def __init__(self, handler_404: Optional[Route404Handler] = None):
        self._handlers: dict[str, RouteHandler] = {}
        self._handler_404 = handler_404 or default_handler_404

    @property
    def handlers(self) -> dict[str, RouteHandler]:
        return self._handlers

    def register(self, path: str):
        def wrapper(handler: RouteHandler):
            self._handlers[path] = handler

        return wrapper

    def refresh(self, page: ft.Page):
        """
        A hacky way refresh the current page and its content.

        Flet doesn't trigger a route change if the url is the same.
        """

        # FIXME: A hack to make Flet to propagate the "on_route_change" event in v0.28.3.
        page._Page__last_route = ""
        page.go(page.route)
        return

    def get_view_for_url(self, route: str) -> ft.Control:
        parsed = urlparse(route)
        query = parse_qs(parsed.query)

        for path, handler in self._handlers.items():
            pattern = repath.pattern(path)
            match = re.match(pattern, parsed.path)
            if match:
                logger.debug(f"Open view {handler} for route {route}")
                path_params = match.groupdict()
                request = Request(
                    url=route, path=parsed.path, query=query, params=path_params
                )
                try:
                    return handler(request)
                except ObjectNotFound as exc:
                    return self._handler_404(request, str(exc))
        else:
            request = Request(url=route, path=parsed.path, query=query)
            return self._handler_404(request)
