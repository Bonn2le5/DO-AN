"""
WebSocket Consumers for Real-Time Order Lifecycle Tracking and Staff Kitchen Displays.
Paths:
  - /ws/orders/<order_id>/ : Individual order tracking for customer or staff.
  - /ws/orders/staff/      : Global order stream for restaurant staff and kitchen monitors.
"""

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import DonHang


class OrderTrackingConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for tracking individual order lifecycle updates.
    Accepts numeric order ID or string code (ma_don_hang).
    Enforces authorization: Customer must own the order; staff has global access.
    """

    async def connect(self):
        self.order_id_param = self.scope["url_route"]["kwargs"].get("order_id")
        self.user = self.scope.get("user")

        # 1. Enforce Authentication (reject 4401 if anonymous)
        if not self.user or not self.user.is_authenticated or isinstance(self.user, AnonymousUser):
            await self.close(code=4401)
            return

        # 2. Check Order Existence & Authorization
        has_access, result = await self._get_order_and_check_access(self.order_id_param, self.user)
        if not has_access:
            # 4404 if not found, 4403 if forbidden for another customer
            close_code = 4404 if result is None else 4403
            await self.close(code=close_code)
            return

        self.order_data = result
        self.group_id_name = f"order_{self.order_data['id']}"
        self.group_code_name = f"order_{self.order_data['order_number']}"

        # 3. Join Channel Groups
        await self.channel_layer.group_add(self.group_id_name, self.channel_name)
        await self.channel_layer.group_add(self.group_code_name, self.channel_name)

        await self.accept()

        # 4. Send immediate order snapshot
        snapshot_payload = {
            "type": "order_snapshot",
            "order_id": self.order_data["id"],
            "order_number": self.order_data["order_number"],
            "order_code": self.order_data["order_number"],
            "ma_don_hang": self.order_data["order_number"],
            "current_status": self.order_data["status"],
            "status": self.order_data["status"],
            "status_display": self.order_data["status_display"],
            "order_type": self.order_data["order_type"],
            "hinh_thuc": self.order_data["order_type"],
            "total": self.order_data["total"],
            "total_amount": self.order_data["total_amount"],
            "tong_tien": self.order_data["total_amount"],
            "customer_name": self.order_data["customer_name"],
            "created_at": self.order_data["created_at"],
            "data": self.order_data,
        }
        await self.send_json(snapshot_payload)

    async def disconnect(self, close_code):
        if hasattr(self, "group_id_name"):
            await self.channel_layer.group_discard(self.group_id_name, self.channel_name)
        if hasattr(self, "group_code_name"):
            await self.channel_layer.group_discard(self.group_code_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        action = content.get("action")
        if action in ["get_status", "refresh", "snapshot"]:
            await self.send_json({
                "type": "order_snapshot",
                "order_id": self.order_data["id"],
                "order_number": self.order_data["order_number"],
                "status": self.order_data["status"],
                "data": self.order_data,
            })

    async def order_status_update(self, event):
        """Forward real-time status update to client."""
        await self.send_json(event)

    @database_sync_to_async
    def _get_order_and_check_access(self, order_id_or_code, user):
        lookup = None
        if str(order_id_or_code).isdigit():
            lookup = DonHang.objects.filter(id=int(order_id_or_code)).first()
        if not lookup:
            lookup = DonHang.objects.filter(ma_don_hang__iexact=str(order_id_or_code)).first()

        if not lookup:
            return False, None

        is_staff = user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False)
        if not is_staff and lookup.khach_hang_id != user.id:
            return False, "forbidden"

        order_info = {
            "id": lookup.id,
            "order_number": lookup.ma_don_hang,
            "ma_don_hang": lookup.ma_don_hang,
            "status": lookup.trang_thai,
            "status_display": lookup.get_trang_thai_display(),
            "order_type": lookup.hinh_thuc,
            "total": float(lookup.tong_tien),
            "total_amount": str(lookup.tong_tien),
            "customer_name": lookup.ten_khach,
            "created_at": lookup.tao_luc.isoformat(),
            "updated_at": lookup.cap_nhat_luc.isoformat(),
        }
        return True, order_info


class StaffOrderConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for restaurant staff global order monitoring and kitchen displays.
    Path: /ws/orders/staff/
    """

    async def connect(self):
        self.user = self.scope.get("user")

        # 1. Enforce Authentication (reject 4401 if anonymous)
        if not self.user or not self.user.is_authenticated or isinstance(self.user, AnonymousUser):
            await self.close(code=4401)
            return

        # 2. Enforce Staff Privilege (reject 4403 if not restaurant staff)
        is_staff = await self._is_restaurant_staff(self.user)
        if not is_staff:
            await self.close(code=4403)
            return

        self.room_group_name = "staff_orders"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        await self.send_json({
            "type": "staff_connected",
            "staff_order_stream_subscribed": True,
            "message": "Đã kết nối luồng quản lý đơn hàng toàn hệ thống.",
            "user_id": self.user.id,
            "role": "nhan_vien",
        })

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def order_status_update(self, event):
        """Forward real-time order status update to staff client."""
        await self.send_json(event)

    async def order_created(self, event):
        """Forward real-time new order event to staff client."""
        await self.send_json(event)

    @database_sync_to_async
    def _is_restaurant_staff(self, user):
        if not user or not user.is_authenticated:
            return False
        return bool(user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False))


# Backward-compatible consumer aliases
OrderConsumer = OrderTrackingConsumer
StaffOrderStreamConsumer = StaffOrderConsumer
