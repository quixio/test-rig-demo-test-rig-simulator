from typing import Optional


class Request:
    __slots__ = ("params", "query", "url", "path")

    def __init__(
        self,
        url: str,
        path: str,
        query: dict[str, list[str]],
        params: Optional[dict[str, str]] = None,
    ):
        self.params: dict[str, str] = params or {}
        self.query = query
        self.url = url
        self.path = path

    def __repr__(self):
        return f"<Request url={self.url} path={self.path} params={self.params} query={self.query}>"
