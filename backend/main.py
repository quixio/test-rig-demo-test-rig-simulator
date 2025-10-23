import sys

import uvicorn

from api.app import create_app
from api.settings import get_settings


def main() -> int:
    settings = get_settings()
    uvicorn.run(
        app=create_app(),
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
