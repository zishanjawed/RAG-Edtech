"""
Centralized CORS configuration for all services.

This module provides a unified CORS setup that:
1. Allows all localhost/127.0.0.1 origins (any port) for development
2. Allows specific production domains from environment variable
3. Single place to manage CORS policy across all services

Usage in any service:
    from shared.middleware.cors_config import configure_cors
    configure_cors(app, settings.cors_origins)
"""
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.cors import CORSMiddleware as BaseCORSMiddleware
from typing import List


def is_localhost_origin(origin: str) -> bool:
    """
    Check if origin is localhost or 127.0.0.1 on any port.
    
    Args:
        origin: Origin header value
    
    Returns:
        True if origin is localhost, False otherwise
    
    Examples:
        http://localhost:3000 -> True
        http://localhost:5173 -> True
        http://127.0.0.1:8080 -> True
        https://localhost:3001 -> True
        https://example.com -> False
    """
    if not origin:
        return False
    return bool(re.match(r'^https?://(localhost|127\.0\.0\.1)(:\d+)?$', origin))


class UniversalCORSMiddleware(BaseCORSMiddleware):
    """
    Custom CORS middleware that automatically allows all localhost origins.
    
    This is safe for development and allows frontend to run on any port
    without requiring CORS configuration updates.
    """
    
    def is_allowed_origin(self, origin: str) -> bool:
        """
        Check if origin is allowed.
        
        Priority:
        1. Localhost/127.0.0.1 on any port -> Always allowed
        2. Explicitly listed in allow_origins -> Allowed
        3. Otherwise -> Denied
        """
        # Allow all localhost origins (development)
        if is_localhost_origin(origin):
            return True
        
        # Otherwise use standard CORS behavior (production domains)
        return super().is_allowed_origin(origin)


def configure_cors(app: FastAPI, cors_origins: str = ""):
    """
    Configure CORS for a FastAPI application.
    
    This function should be called BEFORE adding other middleware
    and BEFORE defining routes.
    
    Args:
        app: FastAPI application instance
        cors_origins: Comma-separated list of allowed origins
                     (in addition to automatic localhost support)
    
    Example:
        from shared.middleware.cors_config import configure_cors
        
        app = FastAPI()
        configure_cors(app, settings.cors_origins)
    
    Allowed Origins:
        - All localhost:* (automatic, for development)
        - All 127.0.0.1:* (automatic, for development)
        - Any domains specified in cors_origins parameter
    
    Environment Variable:
        CORS_ORIGINS=https://example.com,https://app.example.com
    """
    # Parse comma-separated origins
    origin_list = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
    
    # Add CORS middleware with custom class
    app.add_middleware(
        UniversalCORSMiddleware,
        allow_origins=origin_list if origin_list else ["*"],  # Fallback to * if no origins specified
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID"],  # Expose our custom headers
    )


# For backwards compatibility - allow direct import
__all__ = ['configure_cors', 'is_localhost_origin', 'UniversalCORSMiddleware']

