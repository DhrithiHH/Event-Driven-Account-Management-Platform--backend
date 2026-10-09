import logging

from dishka import AsyncContainer, make_async_container

from fastapi_example.application.di_providers.features import (
    AuthFeaturesProvider,
    NotificationsFeaturesProvider,
    UsersFeaturesProvider,
)
from fastapi_example.application.di_providers.services import (
    AuthServiceProvider,
    EmailNotificationsServiceProvider,
    RateLimiterServiceProvider,
)
from fastapi_example.infrastructure.di_providers import (
    CacheProvider,
    CacheRepositoriesProvider,
    CommunicationProvider,
    DatabaseProvider,
    DBMappersProvider,
    DBRepositoriesProvider,
    HasherProvider,
    HTTPClientsProvider,
    MessageBrokerProducersProvider,
    MessageBrokerProvider,
)

from .settings import Settings

log = logging.getLogger(__name__)


def setup_di_container(
    settings: Settings,
) -> AsyncContainer:
    log.debug("Setting up DI container.")
    container = make_async_container(
        DatabaseProvider(settings.infrastructure.database),
        DBMappersProvider(),
        DBRepositoriesProvider(),
        HasherProvider(),
        AuthServiceProvider(settings.infrastructure.jwt),
        CacheProvider(settings.infrastructure.redis),
        CacheRepositoriesProvider(),
        RateLimiterServiceProvider(),
        UsersFeaturesProvider(),
        AuthFeaturesProvider(),
        NotificationsFeaturesProvider(),
        HTTPClientsProvider(settings.infrastructure.email_verifier),
        MessageBrokerProvider(settings.infrastructure.message_broker),
        CommunicationProvider(settings.infrastructure.smtp),
        MessageBrokerProducersProvider(),
        EmailNotificationsServiceProvider(settings.application.email_notifications),
    )

    return container
