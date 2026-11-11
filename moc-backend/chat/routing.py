from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"^ws/chat/inbox/?$", consumers.HopThuConsumer.as_asgi()),
    re_path(r"^ws/hoi-thoai/hop-thu/?$", consumers.HopThuConsumer.as_asgi()),
    re_path(r"^ws/chat/(?P<conversation_id>\d+)/?$", consumers.HoiThoaiConsumer.as_asgi()),
    re_path(r"^ws/hoi-thoai/(?P<conversation_id>\d+)/?$", consumers.HoiThoaiConsumer.as_asgi()),
]
