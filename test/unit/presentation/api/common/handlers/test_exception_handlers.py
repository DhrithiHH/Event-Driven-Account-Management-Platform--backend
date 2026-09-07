from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from fastapi_example.presentation.api.common.handlers.exception_handlers import (
    validation_exception_handler,
)


def make_request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "scheme": "http",
            "path": "/api/v1/users",
            "headers": [],
            "server": ("testserver", 80),
        }
    )


async def test_validation_error_without_context_returns_bad_request() -> None:
    error = RequestValidationError(
        [
            {
                "type": "missing",
                "loc": ("body", "username"),
                "msg": "Field required",
                "input": {},
            }
        ]
    )

    response = await validation_exception_handler(make_request(), error)

    assert response.status_code == 400
    assert response.body == b'{"status":400,"detail":["Field required"],"additional":[null]}'


async def test_validation_error_with_context_returns_bad_request() -> None:
    error = RequestValidationError(
        [
            {
                "type": "greater_than",
                "loc": ("body", "age"),
                "msg": "Input should be greater than 18",
                "input": 18,
                "ctx": {"gt": 18},
            }
        ]
    )

    response = await validation_exception_handler(make_request(), error)

    assert response.status_code == 400
    assert (
        response.body
        == b'{"status":400,"detail":["Input should be greater than 18"],"additional":[{"gt":18}]}'
    )


async def test_validation_error_with_exception_context_returns_bad_request() -> None:
    error = RequestValidationError(
        [
            {
                "type": "value_error",
                "loc": ("body",),
                "msg": "Value error, invalid update",
                "input": {},
                "ctx": {"error": ValueError("invalid update")},
            }
        ]
    )

    response = await validation_exception_handler(make_request(), error)

    assert response.status_code == 400
    assert (
        response.body
        == b'{"status":400,"detail":["Value error, invalid update"],"additional":[{"error":"invalid update"}]}'
    )
