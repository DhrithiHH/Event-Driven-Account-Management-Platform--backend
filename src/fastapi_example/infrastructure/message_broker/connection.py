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


def _find_file(path_str: Optional[str], default_filename: str) -> Optional[str]:
    """Find certificate file across local paths, working dir, repo root, and Render /etc/secrets."""
    if path_str and os.path.isabs(path_str) and os.path.exists(path_str):
        return path_str

    repo_root = Path(__file__).resolve().parents[4]
    candidates: list[Path] = []

    if path_str:
        p = Path(path_str)
        candidates.extend([
            Path.cwd() / p,
            repo_root / p,
            Path("/etc/secrets") / p,
            Path("/etc/secrets") / p.name,
            p,
        ])

    candidates.extend([
        repo_root / ".certs" / "aiven" / default_filename,
        Path.cwd() / ".certs" / "aiven" / default_filename,
        Path("/etc/secrets/.certs/aiven") / default_filename,
        Path("/etc/secrets/aiven") / default_filename,
        Path("/etc/secrets") / default_filename,
    ])

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            log.info("Found certificate file for %s at: %s", default_filename, candidate)
            return str(candidate.resolve())

    return path_str if (path_str and os.path.exists(path_str)) else None


def create_broker(settings: MessageBrokerSettings) -> KafkaBroker:
    bootstrap_servers = settings.url
    security_protocol = (settings.security_protocol or "PLAINTEXT").upper()

    cafile = _find_file(settings.ssl_cafile, "ca.pem")
    certfile = _find_file(settings.ssl_certfile, "service.cert")
    keyfile = _find_file(settings.ssl_keyfile, "service.key")

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
