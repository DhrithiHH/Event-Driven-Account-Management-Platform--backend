from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_example.presentation.api.v1.controllers.notifications import (
    notifications_router,
)


def test_notification_history_requires_bearer_authentication() -> None:
    app = FastAPI()
    app.include_router(notifications_router)

    response = TestClient(app).get("/api/v1/notifications")

    assert response.status_code == 401
