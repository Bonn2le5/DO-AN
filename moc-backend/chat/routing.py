from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"^ws/chat/(?P<conversation_id>[a-zA-Z0-9_-]+)/?$", consumers.ChatConsumer.as_asgi()),
    re_path(r"^ws/hoi-thoai/(?P<conversation_id>[a-zA-Z0-9_-]+)/?$", consumers.ChatConsumer.as_asgi()),
]
