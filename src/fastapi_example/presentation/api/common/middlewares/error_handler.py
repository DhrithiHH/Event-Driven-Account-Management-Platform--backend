import logging

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

log = logging.getLogger(__name__)


class CatchAllExceptionMiddleware:
    """Catch unhandled exceptions inside CORSMiddleware so 500 responses keep CORS headers."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as err:
            log.exception("Unhandled error during HTTP request: %s", err)
            if response_started:
                raise
            response = JSONResponse(
                {
                    "status": 500,
                    "message": "Internal Server Error",
                    "detail": f"{type(err).__name__}: {err}",
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            await response(scope, receive, send)


def setup_error_middleware(app: FastAPI) -> None:
    log.debug("Setting up catch-all error middleware")
    app.add_middleware(CatchAllExceptionMiddleware)
