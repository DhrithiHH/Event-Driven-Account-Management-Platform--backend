import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL, make_url

log = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="DB_", extra="ignore"
    )
    drivername: str = "postgresql+asyncpg"
    host: Optional[str] = "localhost"
    port: Optional[int] = 5432
    username: Optional[str] = "postgres"
    password: Optional[str] = ""
    database: Optional[str] = "postgres"
    custom_url: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("url", "custom_url", "db_url", "database_url"),
    )
    ssl: Optional[bool] = None
    sslmode: Optional[str] = None

    @property
    def url_str(self) -> str:
        raw_url = self.custom_url or os.getenv("DATABASE_URL")
        if raw_url:
            cleaned = raw_url.strip().strip("'").strip('"')
            if cleaned.startswith("postgres://"):
                cleaned = "postgresql+asyncpg://" + cleaned[len("postgres://") :]
            elif cleaned.startswith("postgresql://"):
                cleaned = "postgresql+asyncpg://" + cleaned[len("postgresql://") :]
            elif not cleaned.startswith("postgresql+asyncpg://"):
                cleaned = f"postgresql+asyncpg://{cleaned}"

            # Normalize sslmode for asyncpg
            if "sslmode=" in cleaned:
                cleaned = (
                    cleaned.replace("sslmode=require", "ssl=require")
                    .replace("sslmode=prefer", "ssl=prefer")
                    .replace("sslmode=disable", "ssl=disable")
                )
            elif self.ssl or self.sslmode:
                sep = "&" if "?" in cleaned else "?"
                mode = self.sslmode or ("require" if self.ssl else "prefer")
                cleaned = f"{cleaned}{sep}ssl={mode}"
            return cleaned

        base = (
            f"{self.drivername}://"
            f"{self.username or ''}:"
            f"{self.password or ''}@"
            f"{self.host or 'localhost'}:"
            f"{self.port or 5432}/"
            f"{self.database or ''}"
        )
        if self.ssl or (self.sslmode and self.sslmode != "disable"):
            mode = self.sslmode or "require"
            base = f"{base}?ssl={mode}"
        return base

    @property
    def url_obj(self) -> URL:
        return make_url(self.url_str)


class UvicornServerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="UVICORN_SERVER_",
        extra="ignore",
    )

    host: Optional[str] = "0.0.0.0"
    port: Optional[int] = Field(
        default=8080,
        validation_alias=AliasChoices("port", "uvicorn_server_port", "PORT"),
    )


class JWTSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="JWT_", extra="ignore"
    )
    algorithm: str = "RS256"
    expiration: int = 30
    private_key_content: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "private_key", "private_key_content", "jwt_private_key"
        ),
    )
    public_key_content: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "public_key", "public_key_content", "jwt_public_key"
        ),
    )
    certs_dir: Optional[str] = None

    @property
    def private_key(self) -> str:
        if self.private_key_content:
            return self.private_key_content
        return self._get_or_create_key_file("jwt-private.pem", is_private=True)

    @property
    def public_key(self) -> str:
        if self.public_key_content:
            return self.public_key_content
        return self._get_or_create_key_file("jwt-public.pem", is_private=False)

    def _get_key_file(self, filename: str) -> str:
        certs_dir = self._get_certs_path()
        key_path = certs_dir / filename
        if not key_path.exists():
            self._ensure_rsa_keys(certs_dir)
        if not key_path.exists():
            raise FileNotFoundError(f"JWT key file not found: {key_path}")

        return key_path.read_text(encoding="utf-8")

    def _get_or_create_key_file(self, filename: str, is_private: bool) -> str:
        return self._get_key_file(filename)

    def _get_certs_path(self) -> Path:
        if self.certs_dir:
            return Path(self.certs_dir)
        return Path(__file__).parents[3] / ".certs"

    @staticmethod
    def _ensure_rsa_keys(certs_dir: Path) -> None:
        private_path = certs_dir / "jwt-private.pem"
        public_path = certs_dir / "jwt-public.pem"
        if private_path.exists() and public_path.exists():
            return

        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa

            certs_dir.mkdir(parents=True, exist_ok=True)
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ).decode("utf-8")
            public_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("utf-8")

            if not private_path.exists():
                private_path.write_text(private_pem, encoding="utf-8")
            if not public_path.exists():
                public_path.write_text(public_pem, encoding="utf-8")
            log.info("Auto-generated RSA JWT keypair in %s", certs_dir)
        except Exception as exc:
            log.warning("Could not auto-generate RSA JWT keypair: %s", exc)


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="REDIS_",
        extra="ignore",
    )
    host: Optional[str] = "localhost"
    port: Optional[int] = 6379
    password: Optional[str] = None
    custom_url: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("url", "custom_url", "redis_url"),
    )
    ssl: bool = False

    @property
    def url(self) -> str:
        if self.custom_url:
            return self.custom_url
        env_url = os.getenv("REDIS_URL")
        if env_url:
            return env_url
        scheme = "rediss" if self.ssl else "redis"
        password = f":{self.password}@" if self.password else ""
        return f"{scheme}://{password}{self.host or 'localhost'}:{self.port or 6379}"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        extra="ignore",
    )
    title: Optional[str] = "FastAPI"
    version: Optional[str] = "0.1.0"
    docs_url: Optional[str] = "/docs"
    redoc_url: Optional[str] = "/redoc"


class CORSSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="CORS_", extra="ignore"
    )
    methods: list[str] = ["*"]
    headers: list[str] = ["*"]
    origins: list[str] = ["*"]


class EmailVerifierSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="EMAIL_VERIFIER_",
        extra="ignore",
    )
    api_key: str = ""
    enabled: bool = True


class MessageBrokerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="MESSAGE_BROKER_",
        extra="ignore",
    )
    host: Optional[str] = "localhost"
    port: Optional[int] = 9092
    bootstrap_servers: Optional[str] = None
    custom_url: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "MESSAGE_BROKER_BOOTSTRAP_SERVERS",
            "MESSAGE_BROKER_URL",
            "KAFKA_BOOTSTRAP_SERVERS",
            "KAFKA_URL",
            "url",
            "bootstrap_servers",
        ),
    )
    security_protocol: str = "PLAINTEXT"
    ssl_cafile: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    ssl_key_password: Optional[str] = None
    ssl_ca_data: Optional[str] = None
    ssl_cert_data: Optional[str] = None
    ssl_key_data: Optional[str] = None
    sasl_mechanism: Optional[str] = "SCRAM-SHA-256"
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    certs_dir: Optional[str] = None

    @property
    def url(self) -> str:
        return (
            self.bootstrap_servers
            or self.custom_url
            or os.getenv("MESSAGE_BROKER_BOOTSTRAP_SERVERS")
            or os.getenv("MESSAGE_BROKER_URL")
            or os.getenv("KAFKA_BOOTSTRAP_SERVERS")
            or os.getenv("KAFKA_URL")
            or f"{self.host or 'localhost'}:{self.port or 9092}"
        )


class SMTPSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SMTP_",
        extra="ignore",
    )
    host: str = "localhost"
    port: int = 1025
    use_tls: bool = False
    starttls: bool = False
    sender: str = "root@localhost"
    username: Optional[str] = None
    password: Optional[str] = None


@dataclass
class InfrastructureSettings:
    database: DatabaseSettings
    server: UvicornServerSettings
    jwt: JWTSettings
    redis: RedisSettings
    app: AppSettings
    cors: CORSSettings
    email_verifier: EmailVerifierSettings
    message_broker: MessageBrokerSettings
    smtp: SMTPSettings


def load_infrastructure_settings(
    database_settings: Optional[DatabaseSettings] = None,
    server_settings: Optional[UvicornServerSettings] = None,
    jwt_settings: Optional[JWTSettings] = None,
    redis_settings: Optional[RedisSettings] = None,
    app_settings: Optional[AppSettings] = None,
    cors_settings: Optional[CORSSettings] = None,
    email_verifier_settings: Optional[EmailVerifierSettings] = None,
    message_broker_settings: Optional[MessageBrokerSettings] = None,
    smtp_settings: Optional[SMTPSettings] = None,
) -> InfrastructureSettings:
    log.debug("Loading infrastructure settings.")
    return InfrastructureSettings(
        database=database_settings or DatabaseSettings(),  # type: ignore[call-arg]
        server=server_settings or UvicornServerSettings(),
        jwt=jwt_settings or JWTSettings(),
        redis=redis_settings or RedisSettings(),  # type: ignore[call-arg]
        app=app_settings or AppSettings(),
        cors=cors_settings or CORSSettings(),
        email_verifier=email_verifier_settings or EmailVerifierSettings(),  # type: ignore[call-arg]
        message_broker=message_broker_settings or MessageBrokerSettings(),
        smtp=smtp_settings or SMTPSettings(),
    )
