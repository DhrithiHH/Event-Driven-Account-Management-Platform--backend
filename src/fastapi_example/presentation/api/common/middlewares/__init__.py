from .cors import setup_cors_middleware
from .error_handler import setup_error_middleware

__all__ = ("setup_cors_middleware", "setup_error_middleware")
