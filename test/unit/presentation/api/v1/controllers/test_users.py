from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_example.presentation.api.common.handlers import setup_exception_handlers
from fastapi_example.presentation.api.v1.controllers.users import users_router


def test_update_user_rejects_empty_payload_before_endpoint_execution() -> None:
    app = FastAPI()
    setup_exception_handlers(app)
    app.include_router(users_router)

    response = TestClient(app).patch(
        "/api/v1/users",
        headers={"Authorization": "Bearer token"},
        json={},
    )

    assert response.status_code == 400
    assert response.json() == {
        "status": 400,
        "detail": [
            "Value error, At least one of username or email must be provided"
        ],
        "additional": [{"error": "At least one of username or email must be provided"}],
    }
