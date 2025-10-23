from typing import Optional


class ObjectNotFound(Exception): ...


class ValidationError(Exception):
    def __init__(self, field: Optional[str], message: str):
        self.field = field
        self.message = message
