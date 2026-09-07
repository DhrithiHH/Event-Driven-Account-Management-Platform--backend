import asyncio
import logging

import uvicorn
from fastapi import FastAPI

from fastapi_example.infrastructure.settings import UvicornServerSettings

log = logging.getLogger(__name__)


async def run_uvicorn_server(
    app: FastAPI,
    settings: UvicornServerSettings,
    shutdown_event: asyncio.Event,
) -> None:
    log.debug("Running Uvicorn server.")
    config = uvicorn.Config(app, **settings.model_dump())
    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve())
    shutdown_task = asyncio.create_task(shutdown_event.wait())

    try:
        done, _ = await asyncio.wait(
            (server_task, shutdown_task), return_when=asyncio.FIRST_COMPLETED
        )
        if shutdown_task in done and not server_task.done():
            server.should_exit = True

        await server_task
    finally:
        for task in (server_task, shutdown_task):
            if not task.done():
                task.cancel()
        await asyncio.gather(server_task, shutdown_task, return_exceptions=True)
