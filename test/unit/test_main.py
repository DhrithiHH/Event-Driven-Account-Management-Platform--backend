import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from fastapi_example import __main__ as main_module


@pytest.mark.asyncio
async def test_async_main_stops_faststream_and_closes_container(monkeypatch) -> None:
    stopped = asyncio.Event()
    container = MagicMock()
    container.close = AsyncMock()

    class FastStreamStub:
        async def run(self) -> None:
            await stopped.wait()

        def exit(self) -> None:
            stopped.set()

    settings = SimpleNamespace(
        application=SimpleNamespace(v1_api=object()),
        infrastructure=SimpleNamespace(server=object()),
    )

    monkeypatch.setattr(main_module, "load_settings", lambda: settings)
    monkeypatch.setattr(main_module, "setup_di_container", lambda _: container)
    monkeypatch.setattr(main_module, "init_app_v1", lambda *_: object())
    monkeypatch.setattr(
        main_module, "init_faststream", AsyncMock(return_value=FastStreamStub())
    )

    async def uvicorn_stub(*_args) -> None:
        return None

    monkeypatch.setattr(main_module, "run_uvicorn_server", uvicorn_stub)

    await main_module.async_main()

    assert stopped.is_set()
    container.close.assert_awaited_once()
