from functools import lru_cache
from typing import Callable, Literal, Optional

from fastapi import Depends, Header, HTTPException
from quixportal.auth import Auth

from .settings import Settings, get_settings


@lru_cache(maxsize=1)
def auth() -> Auth:
    return Auth()


def validate_token(
    permission: Literal["Read", "Update"],
) -> Callable[[Auth, Settings, Optional[str]], None]:
    def inner(
        auth: Auth = Depends(auth),
        settings: Settings = Depends(get_settings),
        authorization: Optional[str] = Header(default=None),
    ) -> None:
        if not settings.api_auth_active:
            return None

        if authorization is None:
            raise HTTPException(status_code=403, detail="Not Allowed")

        if authorization.startswith(("bearer ", "Bearer ")):
            token = authorization[7:]
        else:
            token = authorization

        if not auth.validate_permissions(
            token, "Workspace", settings.workspace_id, permission
        ):
            raise HTTPException(status_code=403, detail="Not Allowed")

        return None

    return inner


update_permission = validate_token("Update")
read_permission = validate_token("Read")
