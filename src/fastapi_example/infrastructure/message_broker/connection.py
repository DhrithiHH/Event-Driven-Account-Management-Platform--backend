import logging
import os
import ssl
import tempfile
from pathlib import Path
from typing import Optional

from faststream.kafka import KafkaBroker
from faststream.security import (
    BaseSecurity,
    SASLPlaintext,
    SASLScram256,
    SASLScram512,
)

from fastapi_example.infrastructure.settings import MessageBrokerSettings

log = logging.getLogger(__name__)


def create_broker(settings: MessageBrokerSettings) -> KafkaBroker:
    bootstrap_servers = settings.url
    security_protocol = (settings.security_protocol or "PLAINTEXT").upper()

    cafile = settings.ssl_cafile
    certfile = settings.ssl_certfile
    keyfile = settings.ssl_keyfile

    # Auto-detect certs directory if not explicitly provided
    certs_dir: Optional[Path] = None
    if settings.certs_dir:
        candidate = Path(settings.certs_dir)
        if candidate.exists():
            certs_dir = candidate
    else:
        # Check standard certs directories: .certs/aiven, .certs/kafka, .certs, certs
        repo_root = Path(__file__).parents[4]
        for candidate in [
            repo_root / ".certs" / "aiven",
            repo_root / ".certs" / "kafka",
            repo_root / ".certs",
            repo_root / "certs",
        ]:
            if candidate.exists() and (candidate / "ca.pem").exists():
                certs_dir = candidate
                break

    if certs_dir:
        if not cafile and (certs_dir / "ca.pem").exists():
            cafile = str(certs_dir / "ca.pem")
        if not certfile and (certs_dir / "service.cert").exists():
            certfile = str(certs_dir / "service.cert")
        if not keyfile and (certs_dir / "service.key").exists():
            keyfile = str(certs_dir / "service.key")

    # If raw PEM certificate content is provided via env vars, write to temporary files
    if settings.ssl_ca_data and not cafile:
        f = tempfile.NamedTemporaryFile("w", delete=False, suffix="_ca.pem")
        f.write(settings.ssl_ca_data)
        f.close()
        cafile = f.name
    if settings.ssl_cert_data and not certfile:
        f = tempfile.NamedTemporaryFile("w", delete=False, suffix="_service.cert")
        f.write(settings.ssl_cert_data)
        f.close()
        certfile = f.name
    if settings.ssl_key_data and not keyfile:
        f = tempfile.NamedTemporaryFile("w", delete=False, suffix="_service.key")
        f.write(settings.ssl_key_data)
        f.close()
        keyfile = f.name

    # Auto-switch to SSL if certs are present and protocol was left as default PLAINTEXT
    if (cafile or certfile) and security_protocol == "PLAINTEXT":
        security_protocol = "SSL"
        log.info("Detected Kafka certificates; switching security protocol to SSL.")

    security = None

    if security_protocol in ("SSL", "SASL_SSL"):
        ssl_context = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH,
            cafile=cafile if (cafile and os.path.exists(cafile)) else None,
        )
        if certfile and keyfile and os.path.exists(certfile) and os.path.exists(keyfile):
            ssl_context.load_cert_chain(
                certfile=certfile,
                keyfile=keyfile,
                password=settings.ssl_key_password,
            )

        if security_protocol == "SSL":
            security = BaseSecurity(ssl_context=ssl_context)
        elif security_protocol == "SASL_SSL":
            mechanism = (settings.sasl_mechanism or "SCRAM-SHA-256").upper()
            username = settings.sasl_username or ""
            password = settings.sasl_password or ""
            if mechanism == "SCRAM-SHA-512":
                security = SASLScram512(
                    username=username, password=password, ssl_context=ssl_context
                )
            elif mechanism == "PLAIN":
                security = SASLPlaintext(
                    username=username, password=password, ssl_context=ssl_context
                )
            else:
                security = SASLScram256(
                    username=username, password=password, ssl_context=ssl_context
                )

    elif security_protocol in ("SASL_PLAINTEXT", "SASL"):
        mechanism = (settings.sasl_mechanism or "PLAIN").upper()
        username = settings.sasl_username or ""
        password = settings.sasl_password or ""
        if mechanism == "SCRAM-SHA-512":
            security = SASLScram512(username=username, password=password, use_ssl=False)
        elif mechanism == "SCRAM-SHA-256":
            security = SASLScram256(username=username, password=password, use_ssl=False)
        else:
            security = SASLPlaintext(
                username=username, password=password, use_ssl=False
            )

    log.info(
        "Initializing Kafka broker for %s with security=%s",
        bootstrap_servers,
        security.__class__.__name__ if security else "None",
    )
    return KafkaBroker(bootstrap_servers, security=security)
