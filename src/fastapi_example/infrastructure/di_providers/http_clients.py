from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from fastapi_example.application.interfaces.http_clients import IEmailVerifier
from fastapi_example.infrastructure.http_clients import (
    AbstractApiEmailVerifier,
    NullEmailVerifier,
)
from fastapi_example.infrastructure.settings import EmailVerifierSettings


class HTTPClientsProvider(Provider):
    def __init__(
        self, email_verifier_settings: EmailVerifierSettings, scope=None, component=None
    ):
        self._email_verifier_settings = email_verifier_settings
        super().__init__(scope, component)

    @provide(scope=Scope.APP)
    async def email_verifier(self) -> AsyncIterator[IEmailVerifier]:
        if not self._email_verifier_settings.enabled:
            yield NullEmailVerifier()
            return

        verifier = AbstractApiEmailVerifier(self._email_verifier_settings.api_key)
        try:
            yield verifier
        finally:
            await verifier.aclose()
