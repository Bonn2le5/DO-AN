"""
JWT Authentication Middleware for Django Channels WebSockets.
Extracts JWT token from query string (?token=...) or Authorization header.
Decodes token with SimpleJWT and attaches authenticated NguoiDung to scope['user'].
"""

import urllib.parse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def get_user_from_token(token_string):
    """
    Decodes SimpleJWT access token and loads the active user from DB.
    Returns AnonymousUser() if token is invalid, expired, or user not found.
    """
    if not token_string:
        return AnonymousUser()
    try:
        access_token = AccessToken(token_string)
        user_id = access_token.payload.get("user_id")
        if not user_id:
            return AnonymousUser()
        User = get_user_model()
        user = User.objects.filter(id=user_id, is_active=True).first()
        return user or AnonymousUser()
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Middleware that authenticates WebSocket connections via JWT token passed in
    the query string (?token=...) or the Authorization Bearer header.
    """

    async def __call__(self, scope, receive, send):
        token_str = None

        # 1. Check Query String ?token=<jwt>
        query_string = scope.get("query_string", b"").decode("utf-8")
        if query_string:
            query_params = urllib.parse.parse_qs(query_string)
            tokens = query_params.get("token", [])
            if tokens:
                token_str = tokens[0]

        # 2. Check Authorization Header (for API / Test Clients)
        if not token_str and "headers" in scope:
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode("utf-8")
            if auth_header.startswith("Bearer "):
                token_str = auth_header[7:].strip()
            elif b"token" in headers:
                token_str = headers[b"token"].decode("utf-8")
            elif b"sec-websocket-protocol" in headers:
                sec_proto = headers[b"sec-websocket-protocol"].decode("utf-8")
                if sec_proto.startswith("Bearer "):
                    token_str = sec_proto[7:].strip()

        # 3. Resolve user asynchronously
        if token_str:
            scope["user"] = await get_user_from_token(token_str)
        elif "user" not in scope or scope["user"] is None:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """Combines standard Django Session Auth + SimpleJWT Token Auth."""
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))


# Backward compatibility aliases
TokenAuthMiddleware = JWTAuthMiddleware
TokenAuthMiddlewareStack = JWTAuthMiddlewareStack
