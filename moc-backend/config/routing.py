"""
Central WebSocket routing for Nhà hàng Mộc.
Combines routes from chat and orders applications.
"""

import chat.routing
import orders.routing

websocket_urlpatterns = (
    chat.routing.websocket_urlpatterns +
    orders.routing.websocket_urlpatterns
)
