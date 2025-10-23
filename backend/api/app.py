from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import mongo, influx
from .routes.files import router as files_router
from .routes.links import router as links_router
from .routes.logbook import router as logbook_router
from .routes.tests import router as tests_router
from .settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Handles startup and shutdown events for the application.
    Connects to MongoDB on startup and closes the connection on shutdown.
    """
    settings = get_settings()
    mongo.connect(settings.mongo)
    influx.connect(settings.influx)
    yield
    mongo.disconnect()


def create_app() -> FastAPI:
    application = FastAPI(
        title="Test Manager API",
        docs_url="/",
        lifespan=lifespan,
    )

    application.include_router(tests_router, tags=["tests"], prefix="/api/v1")
    application.include_router(logbook_router, tags=["logbook"], prefix="/api/v1")
    application.include_router(files_router, tags=["files"], prefix="/api/v1")
    application.include_router(links_router, tags=["links"], prefix="/api/v1")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application
