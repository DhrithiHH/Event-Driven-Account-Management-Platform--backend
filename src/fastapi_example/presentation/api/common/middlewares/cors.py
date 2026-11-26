import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi_example.application.settings import CORSSettings

log = logging.getLogger(__name__)


def setup_cors_middleware(app: FastAPI, settings: CORSSettings) -> None:
    log.debug("Setting up CORS middleware")
    origins = settings.parsed_origins if hasattr(settings, "parsed_origins") else settings.origins
    methods = settings.parsed_methods if hasattr(settings, "parsed_methods") else settings.methods
    headers = settings.parsed_headers if hasattr(settings, "parsed_headers") else settings.headers

    has_wildcard = "*" in origins or not origins
    explicit_origins = [o for o in origins if o != "*"]
    allow_origin_regex = r"^https?://.*" if has_wildcard else None

    app.add_middleware(
        CORSMiddleware,
        allow_origins=explicit_origins if not has_wildcard else [],
        allow_origin_regex=allow_origin_regex,
        allow_credentials=True,
        allow_methods=methods,
        allow_headers=headers,
    )
