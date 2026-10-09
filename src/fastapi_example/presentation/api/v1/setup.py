import logging
from typing import Any

from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from fastapi_example.application.settings import V1APISettings

from .controllers import (
    auth_router,
    notifications_router,
    setup_controllers,
    users_router,
)
from .handlers import setup_handlers
from .middlewares import setup_middlewares

log = logging.getLogger(__name__)


def init_app_v1(
    v1_settings: V1APISettings, di_container: AsyncContainer, **kwargs: Any
) -> FastAPI:
    log.debug("Initialize V1 API")
    app = FastAPI(**v1_settings.app.model_dump(), **kwargs)

    setup_dishka(di_container, app)
    setup_controllers(app, users_router, auth_router, notifications_router)
    setup_handlers(app)
    setup_middlewares(app, v1_settings)

    return app
