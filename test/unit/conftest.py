from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from fastapi_example.application.interfaces.http_clients import EmailVerificationResult
from fastapi_example.infrastructure.settings import JWTSettings


@pytest.fixture
def jwt_settings() -> Iterator[JWTSettings]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_key_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    with (
        patch.object(
            JWTSettings,
            "private_key",
            new_callable=PropertyMock,
            return_value=private_key_pem,
        ),
        patch.object(
            JWTSettings,
            "public_key",
            new_callable=PropertyMock,
            return_value=public_key_pem,
        ),
    ):
        yield JWTSettings(algorithm="RS256", expiration=30)


@pytest.fixture
def mock_transaction_manager():
    mock = MagicMock()
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def mock_users_repository():
    return AsyncMock()


@pytest.fixture
def mock_cache_repository():
    return AsyncMock()


@pytest.fixture
def mock_hasher():
    mock = MagicMock()
    mock.hash_password = MagicMock(return_value="hashed_password")
    mock.verify_password = MagicMock(return_value=True)
    return mock


@pytest.fixture
def mock_email_verifier():
    mock = AsyncMock()
    mock.check = AsyncMock(
        return_value=EmailVerificationResult(
            is_valid_format=True,
            is_deliverable=True,
            is_disposable=False,
            details="ok",
        )
    )
    return mock


@pytest.fixture
def mock_email_notifications():
    mock = AsyncMock()
    mock.enqueue = AsyncMock(return_value=None)
    return mock
