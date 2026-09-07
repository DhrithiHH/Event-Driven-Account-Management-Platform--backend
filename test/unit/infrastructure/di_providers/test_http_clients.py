import pytest
from dishka import make_async_container

from fastapi_example.application.interfaces.http_clients import IEmailVerifier
from fastapi_example.infrastructure.di_providers.http_clients import HTTPClientsProvider
from fastapi_example.infrastructure.http_clients import AbstractApiEmailVerifier
from fastapi_example.infrastructure.settings import EmailVerifierSettings


@pytest.mark.asyncio
async def test_email_verifier_client_closes_with_app_container() -> None:
    container = make_async_container(
        HTTPClientsProvider(EmailVerifierSettings(api_key="test-key", enabled=True))
    )

    verifier = await container.get(IEmailVerifier)
    assert isinstance(verifier, AbstractApiEmailVerifier)
    assert await container.get(IEmailVerifier) is verifier
    assert not verifier._client.is_closed

    await container.close()

    assert verifier._client.is_closed
