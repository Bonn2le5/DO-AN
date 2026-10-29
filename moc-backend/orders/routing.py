from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Staff global order stream MUST be defined BEFORE order_id to avoid matching "staff" as an order_id
    re_path(r"^ws/orders/staff/?$", consumers.StaffOrderConsumer.as_asgi()),
    re_path(r"^ws/don-hang/nhan-vien/?$", consumers.StaffOrderConsumer.as_asgi()),

    # Single order tracking routes (supports numeric ID or ma_don_hang code)
    re_path(r"^ws/orders/(?P<order_id>[a-zA-Z0-9_-]+)/?$", consumers.OrderTrackingConsumer.as_asgi()),
    re_path(r"^ws/don-hang/(?P<order_id>[a-zA-Z0-9_-]+)/?$", consumers.OrderTrackingConsumer.as_asgi()),
]
