"""
ASGI config for Mộc Restaurant project.
Exposes the ASGI callable as a module-level variable named ``application``.
Routes HTTP requests to standard Django ASGI and WebSocket requests to Channels URLRouter
with JWT & Session authentication middleware wrapped by AllowedHostsOriginValidator.
"""

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

django_http_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402
from config.middleware import JWTAuthMiddlewareStack  # noqa: E402
import config.routing  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_http_app,
        "websocket": AllowedHostsOriginValidator(
            JWTAuthMiddlewareStack(
                URLRouter(config.routing.websocket_urlpatterns)
            )
        ),
    }
)
