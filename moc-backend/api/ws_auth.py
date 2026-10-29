"""
Re-export WebSocket JWT auth middleware from config.middleware.
Maintains backward compatibility for imports from api.ws_auth.
"""

from config.middleware import (
    get_user_from_token,
    JWTAuthMiddleware,
    JWTAuthMiddlewareStack,
    TokenAuthMiddleware,
    TokenAuthMiddlewareStack,
)

__all__ = [
    "get_user_from_token",
    "JWTAuthMiddleware",
    "JWTAuthMiddlewareStack",
    "TokenAuthMiddleware",
    "TokenAuthMiddlewareStack",
]
