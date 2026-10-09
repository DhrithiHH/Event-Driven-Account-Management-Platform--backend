from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Request, Security, status

from fastapi_example.application.features.notifications.get_events import (
    GetNotificationEventsHandler,
    GetNotificationEventsQuery,
)
from fastapi_example.application.interfaces.services import (
    IRateLimiterService,
    ITokenJWTService,
)
from fastapi_example.presentation.api.common.docs import (
    TooManyRequestsError,
    UnAuthorizedError,
)
from fastapi_example.presentation.api.v1.dependencies import get_bearer_token
from fastapi_example.presentation.api.v1.dto import NotificationEventResponseDTO

notifications_router = APIRouter(
    prefix="/api/v1/notifications", tags=["notifications"], route_class=DishkaRoute
)


@notifications_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[NotificationEventResponseDTO],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": UnAuthorizedError},
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": TooManyRequestsError},
    },
)
async def get_notification_events(
    request: Request,
    token: Annotated[str, Security(get_bearer_token)],
    handler: FromDishka[GetNotificationEventsHandler],
    jwt_service: FromDishka[ITokenJWTService],
    rate_limiter_service: FromDishka[IRateLimiterService],
) -> list[NotificationEventResponseDTO]:
    await rate_limiter_service.check(
        f"ip:{request.client.host}",  # type: ignore[union-attr]
        request.url.path,
        limit=100,
        window=60,
    )
    user_id = jwt_service.get_user_id_from_token(token)
    await rate_limiter_service.check(
        f"user:{user_id}", request.url.path, limit=20, window=60
    )
    events = await handler.execute(GetNotificationEventsQuery(user_id=user_id))
    return [
        NotificationEventResponseDTO.model_validate(event, from_attributes=True)
        for event in events
    ]
