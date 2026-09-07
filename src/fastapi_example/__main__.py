import asyncio
import logging
import sys

from .core import load_settings, setup_di_container
from .infrastructure.servers import run_uvicorn_server
from .presentation.api.v1 import init_app_v1
from .presentation.faststream import init_faststream


async def async_main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    settings = load_settings()
    di_container = setup_di_container(settings)

    try:
        api = init_app_v1(
            settings.application.v1_api,
            di_container,
        )
        faststream = await init_faststream(di_container)
        await run_services(
            faststream,
            api,
            settings.infrastructure.server,
        )
    finally:
        await di_container.close()


async def run_services(faststream, api, server_settings) -> None:
    shutdown_event = asyncio.Event()
    faststream_task = asyncio.create_task(faststream.run())
    uvicorn_task = asyncio.create_task(
        run_uvicorn_server(api, server_settings, shutdown_event)
    )

    try:
        await asyncio.wait(
            (faststream_task, uvicorn_task), return_when=asyncio.FIRST_COMPLETED
        )
    finally:
        shutdown_event.set()
        faststream.exit()
        results = await asyncio.gather(
            faststream_task, uvicorn_task, return_exceptions=True
        )

    for result in results:
        if isinstance(result, BaseException) and not isinstance(
            result, asyncio.CancelledError
        ):
            raise result


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
