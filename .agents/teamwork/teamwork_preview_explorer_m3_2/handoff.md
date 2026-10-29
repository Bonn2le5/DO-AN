# Technical Implementation Design Report: Chat WebSocket Consumer & Order FSM Lifecycle (Milestone 3)

**Author**: `m3_explorer_2` (Chat & Order FSM Implementation Explorer)  
**Target Audience**: Milestone 3 Backend Workers, Lead Orchestrator, Challenger & Auditor  
**Date**: 2026-10-14  

---

## 1. Observation

### 1.1 Existing Models and Schema
- **Chat Models** (`moc-backend/chat/models.py`):
  - `HoiThoai` (lines 6–93): Fields include `khach_hang` (FK `AUTH_USER_MODEL`), `nhan_vien` (FK `AUTH_USER_MODEL`, null=True), `trang_thai` (choices `mo`, `dong`, default `mo`), `tin_nhan_cuoi_luc` (DateTimeField, null=True). Aliases: `customer`, `staff`, `status`, `last_message_at`, `messages`.
  - `TinNhan` (lines 94–206): Fields include `hoi_thoai` (FK `HoiThoai`, related_name `danh_sach_tin_nhan`), `nguoi_gui` (FK `AUTH_USER_MODEL`), `loai_tin_nhan` (choices `van_ban`, `hinh_anh`, `he_thong`, default `van_ban`), `noi_dung` (TextField), `da_doc` (BooleanField, default False), `doc_luc` (DateTimeField, null=True). Aliases: `room`, `sender`, `message_type`, `type`, `content`, `message`, `is_read`, `read_at`.
  - Both inherit from `foods.models.MoHinhThoiGian`, providing `tao_luc` (`created_at`) and `cap_nhat_luc` (`updated_at`).
  - PostgreSQL schema (`moc_schema_tieng_viet.sql`, lines 520–550): `hoi_thoai(id, khach_hang_id, nhan_vien_id, trang_thai, tin_nhan_cuoi_luc, tao_luc, cap_nhat_luc)` and `tin_nhan(id, hoi_thoai_id, nguoi_gui_id, loai_tin_nhan, noi_dung, da_doc, doc_luc, tao_luc, cap_nhat_luc)`.

- **Order Models** (`moc-backend/orders/models.py`):
  - `DonHang` (lines 7–150): 6 states defined in `DonHang.TrangThai` (lines 8–14):
    ```python
    CHO_TIEP_NHAN = "cho_tiep_nhan", "Chờ tiếp nhận"
    DA_XAC_NHAN = "da_xac_nhan", "Đã xác nhận"
    DANG_CHE_BIEN = "dang_che_bien", "Đang chế biến"
    SAN_SANG = "san_sang", "Sẵn sàng"
    HOAN_TAT = "hoan_tat", "Hoàn tất"
    DA_HUY = "da_huy", "Đã hủy"
    ```
    Unique order code `ma_don_hang` (format `MOC<UUID8>`, line 88).
  - `LichSuTrangThaiDon` (lines 393–415): `don_hang` (FK `DonHang`, related_name `lich_su_trang_thai`), `tu_trang_thai` (CharField, null=True), `sang_trang_thai` (CharField), `doi_boi` (FK `AUTH_USER_MODEL`, null=True), `ghi_chu` (CharField, max_length=255, blank=True), `tao_luc` (inherited).

### 1.2 Existing Services & ViewSets
- **Order Service** (`moc-backend/orders/services.py`, lines 103–136):
  `DichVuDonHang.doi_trang_thai(don_hang, trang_thai_moi, nguoi_dung, ghi_chu="")`:
  - Line 106: Only checks `if trang_thai_moi not in DonHang.TrangThai.values: raise ValidationError(...)`.
  - **No state transition matrix validation**: Direct illegal transitions (e.g. `cho_tiep_nhan` -> `hoan_tat` or `da_huy` -> `da_xac_nhan`) are currently not prevented.
  - Lines 113–129: BOM deduction and return hooks are wired via `foods.services.DichVuKho`.
  - Line 131: Creates `LichSuTrangThaiDon`.
  - **No WebSocket channel layer broadcast**: `channel_layer.group_send()` is completely absent.
- **Order ViewSet** (`moc-backend/orders/views.py`, lines 27–35):
  - `@action(detail=True, methods=["patch"], permission_classes=[LaNhanVienNhaHang]) def trang_thai(...)`.
  - Lacks dual route naming (e.g., `cap_nhat_trang_thai`, `chuyen_trang_thai`), requires staff permission so customer cannot cancel pending orders, and does not accept `status` / `trang_thai` interchangeably.
- **Chat Views & URLs** (`moc-backend/chat/views.py` and `moc-backend/api/urls.py`):
  - Registered routes: `/api/chat/rooms/` and `/api/hoi-thoai/`.
  - Missing `/api/chat/conversations/` and active conversation resolution helper `/active/` for customer chat initialization.
- **Routing & Consumers**:
  - `moc-backend/chat/consumers.py` and `moc-backend/orders/consumers.py` do not yet exist.
  - `moc-backend/chat/routing.py` and `moc-backend/orders/routing.py` do not yet exist.

### 1.3 Environment & Package Verification
- Virtualenv location: `/Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python`.
- `channels` version: `4.3.2`.
- `channels_redis` version: `4.3.0`.
- `asgiref` version: `3.11.1`.
- `daphne`: **Not installed**. Attempting `pip install daphne` in the sandbox failed due to lack of external network access (`[Errno 8] nodename nor servname provided, or not known`).
- Verification test: `from channels.testing import WebsocketCommunicator` raised `ModuleNotFoundError: No module named 'daphne'` because `channels.testing.__init__.py` imports `ChannelsLiveServerTestCase` which imports `DaphneProcess`.
- Crucial mitigation tested successfully: Providing a lightweight mock `sys.modules['daphne'] = types.ModuleType('daphne')` with `daphne.testing = types.SimpleNamespace(DaphneProcess=object)` allows `WebsocketCommunicator` to be imported and execute without error. Alternatively, `asgiref.testing.ApplicationCommunicator` (which is standard and installed) works 100% natively without daphne.

---

## 2. Logic Chain

### 2.1 Chat Consumer & Persistence Architecture
1. **Consumer Inheritance**: `AsyncJsonWebsocketConsumer` provides async WebSocket message framing, automatic JSON serialization/deserialization, and connection lifecycle management.
2. **Connection Handshake**:
   - URL: `/ws/chat/<conversation_id>/`.
   - Consumer extracts `conversation_id` and `user` from `self.scope`.
   - If user is anonymous, reject connection with WebSocket close code `4401` (Unauthorized).
   - Lookup conversation in database via `@database_sync_to_async`:
     * If user is staff (`user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False)`), grant access to any conversation.
     * If user is customer, grant access if and only if `room.khach_hang_id == user.id`. Otherwise reject with close code `4403` (Forbidden).
   - If authorized, bind channel to Redis channel layer group `chat_{conversation_id}` and call `await self.accept()`.
3. **Guaranteed DB Persistence Before Broadcast**:
   - To satisfy Acceptance Criteria R3 ("lưu trữ tin nhắn vào PostgreSQL trước khi broadcast"):
     * In `receive_json(self, content)`:
     * Validate message content is non-empty.
     * Execute `@database_sync_to_async` function `save_message`:
       1. Insert `TinNhan(hoi_thoai=room, nguoi_gui=user, noi_dung=text, loai_tin_nhan=msg_type)`.
       2. Update `room.tin_nhan_cuoi_luc = timezone.now()`.
       3. If sender is staff and `room.nhan_vien` is unset, assign `room.nhan_vien = user`.
       4. Return serialized dictionary with both Vietnamese and English keys (`noi_dung`, `content`, `tao_luc`, `created_at`).
     * Only after `save_message` successfully resolves, invoke:
       `await self.channel_layer.group_send(self.room_group_name, {"type": "chat_message", "data": msg_data})`.
4. **Broadcast Handler & Typing Indicator**:
   - Handler `chat_message(self, event)` forwards JSON to client.
   - Action `"typing"` broadcasts `chat_typing` event to the group, but skips echoing back to the sender (`event["sender_id"] != self.user.id`).
5. **REST API Parity**:
   - Register router for `/api/chat/conversations/` alongside `/api/chat/rooms/`.
   - Add action `@action(detail=False, methods=["get"]) def active(self, request)`: Returns the active `HoiThoai(khach_hang=user, trang_thai="mo")` (or creates a new one), giving frontend `ChatWidget.tsx` a deterministic ID for WebSocket connection.

---

### 2.2 Order FSM Lifecycle & Real-time Broadcast Architecture
1. **6-State Finite State Machine (FSM)**:
   - Allowable transition matrix:
     * `cho_tiep_nhan` $\rightarrow$ `{"da_xac_nhan", "da_huy"}`
     * `da_xac_nhan` $\rightarrow$ `{"dang_che_bien", "da_huy"}`
     * `dang_che_bien` $\rightarrow$ `{"san_sang", "da_huy"}`
     * `san_sang` $\rightarrow$ `{"hoan_tat", "da_huy"}`
     * `hoan_tat` $\rightarrow$ $\emptyset$ (terminal)
     * `da_huy` $\rightarrow$ $\emptyset$ (terminal)
   - Aliases support: Map English terms (`pending`, `confirmed`, `cooking`, `ready`, `completed`, `cancelled`) to canonical Vietnamese terms.
2. **Pessimistic Locking & Validation**:
   - `doi_trang_thai` uses `@transaction.atomic` and `DonHang.objects.select_for_update().get(id=don_hang.id)` to avoid race conditions.
   - If transition is not in allowable set, raise `rest_framework.exceptions.ValidationError`.
   - Role enforcement: Customer (`khach_hang`) can only cancel (`da_huy`) if current status is `cho_tiep_nhan`. All other transitions require restaurant staff (`la_nhan_vien_nha_hang` or `is_staff`).
3. **Audit Logging & Inventory Hooks**:
   - Create `LichSuTrangThaiDon(don_hang=dh, tu_trang_thai=trang_thai_cu, sang_trang_thai=trang_thai_moi, doi_boi=nguoi_dung, ghi_chu=clean_note)`.
   - Ensure `ghi_chu` is truncated to 255 chars to prevent `DataError` on `CharField(max_length=255)`.
   - Maintain existing BOM material deduction on `da_xac_nhan` and return on `da_huy`.
4. **Channel Layer Broadcast Integration**:
   - Broadcast must occur after transaction commit via `transaction.on_commit(...)` to prevent phantom notifications if a transaction rolls back.
   - Event `order_status_update` is broadcast to:
     * `order_{don_hang.id}`
     * `order_{don_hang.ma_don_hang}`
     * `staff_orders`
5. **Consumers**:
   - `OrderTrackingConsumer` (`/ws/orders/<order_id>/`):
     * Can accept order by integer `id` or string code `ma_don_hang`.
     * Validates permission (staff, order owner, or public token match).
     * Sends immediate `order_snapshot` on connect so client UI renders current state without waiting for next event.
     * Listens for `order_status_update`.
   - `StaffOrderConsumer` (`/ws/orders/staff/`):
     * Restricts connection to authenticated staff only (`close(code=4403)` otherwise).
     * Listens to `staff_orders` for all `order_status_update` and `order_created` events.
6. **URL Pattern Ordering**:
   - In `orders/routing.py`, `^ws/orders/staff/?$` MUST be defined before `^ws/orders/(?P<order_id>[a-zA-Z0-9_-]+)/?$` so that `"staff"` is not captured as an `order_id`.

---

## 3. Caveats

1. **Absence of Daphne in Virtualenv**:
   - `channels` is installed without `daphne`. Running unit tests with `channels.testing.WebsocketCommunicator` will fail if `channels.testing.__init__` is loaded without mocking `daphne.testing.DaphneProcess`. A test helper stub or custom communicator inheriting from `asgiref.testing.ApplicationCommunicator` must be included in the test suite.
2. **Test Environment Channel Layer**:
   - Redis may not be running during CI/unit tests. All automated tests must execute against `InMemoryChannelLayer` via `@override_settings(CHANNEL_LAYERS=...)`.
3. **String vs Integer Order Identifiers**:
   - URLs might pass `order_id` as database ID `42` or display code `MOC482910`. The lookup and channel group naming must handle both gracefully.
4. **Database Truncation**:
   - `LichSuTrangThaiDon.ghi_chu` has `max_length=255`. Notes longer than 255 chars must be safely sliced before calling `create()`.

---

## 4. Conclusion & Complete Implementation Design

The implementation is broken down into clean, modular files matching the project's layout:

### 4.1 Component 1: `moc-backend/chat/consumers.py`

```python
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import HoiThoai, TinNhan


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket Consumer for 2-way real-time communication between Customer and Restaurant Staff.
    Path: /ws/chat/<conversation_id>/
    """

    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"].get("conversation_id")
        self.user = self.scope.get("user")

        # 1. Enforce Authentication
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return

        # 2. Verify Conversation Access
        has_access, self.room = await self._check_conversation_access(self.conversation_id, self.user)
        if not has_access:
            await self.close(code=4403)
            return

        self.room_group_name = f"chat_{self.conversation_id}"

        # 3. Join Channel Group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # 4. Connection confirmation
        await self.send_json({
            "type": "connection_established",
            "conversation_id": self.conversation_id,
            "user_id": self.user.id,
            "username": getattr(self.user, "ho_ten", None) or self.user.username,
        })

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive_json(self, content, **kwargs):
        action = content.get("action", "send_message")

        if action == "send_message":
            text = (content.get("message") or content.get("noi_dung") or content.get("content") or "").strip()
            if not text:
                await self.send_json({"error": "Nội dung tin nhắn không được để trống."})
                return

            msg_type = content.get("message_type") or content.get("loai_tin_nhan") or TinNhan.LoaiTinNhan.VAN_BAN

            # Save to PostgreSQL BEFORE broadcasting
            msg_payload = await self._save_message(
                conversation_id=self.conversation_id,
                user=self.user,
                noi_dung=text,
                loai_tin_nhan=msg_type
            )

            # Broadcast to channel group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "data": msg_payload
                }
            )

        elif action == "typing":
            is_typing = bool(content.get("is_typing", True))
            sender_name = getattr(self.user, "ho_ten", None) or self.user.username
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_typing",
                    "sender_id": self.user.id,
                    "sender_name": sender_name,
                    "is_typing": is_typing,
                }
            )

        elif action == "mark_read":
            await self._mark_read(self.conversation_id, self.user)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_read_receipt",
                    "reader_id": self.user.id,
                    "conversation_id": self.conversation_id,
                }
            )

    async def chat_message(self, event):
        await self.send_json({
            "type": "chat_message",
            "data": event["data"]
        })

    async def chat_typing(self, event):
        if event.get("sender_id") != self.user.id:
            await self.send_json({
                "type": "chat_typing",
                "data": event
            })

    async def chat_read_receipt(self, event):
        await self.send_json({
            "type": "chat_read_receipt",
            "data": event
        })

    @database_sync_to_async
    def _check_conversation_access(self, conversation_id, user):
        try:
            room = HoiThoai.objects.get(id=conversation_id)
            is_staff = user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False)
            if is_staff or room.khach_hang_id == user.id:
                return True, room
            return False, None
        except (HoiThoai.DoesNotExist, ValueError):
            return False, None

    @database_sync_to_async
    def _save_message(self, conversation_id, user, noi_dung, loai_tin_nhan):
        room = HoiThoai.objects.get(id=conversation_id)
        msg = TinNhan.objects.create(
            hoi_thoai=room,
            nguoi_gui=user,
            noi_dung=noi_dung,
            loai_tin_nhan=loai_tin_nhan,
        )
        now = timezone.now()
        room.tin_nhan_cuoi_luc = now
        is_staff = user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False)
        if is_staff and not room.nhan_vien:
            room.nhan_vien = user
            room.save(update_fields=["tin_nhan_cuoi_luc", "nhan_vien", "cap_nhat_luc"])
        else:
            room.save(update_fields=["tin_nhan_cuoi_luc", "cap_nhat_luc"])

        sender_name = getattr(user, "ho_ten", None) or getattr(user, "first_name", "") or user.username
        return {
            "id": msg.id,
            "conversation_id": room.id,
            "hoi_thoai_id": room.id,
            "sender_id": user.id,
            "nguoi_gui_id": user.id,
            "sender_name": sender_name,
            "is_staff": is_staff,
            "noi_dung": msg.noi_dung,
            "content": msg.noi_dung,
            "message": msg.noi_dung,
            "loai_tin_nhan": msg.loai_tin_nhan,
            "message_type": msg.loai_tin_nhan,
            "da_doc": msg.da_doc,
            "is_read": msg.da_doc,
            "tao_luc": msg.tao_luc.isoformat(),
            "created_at": msg.tao_luc.isoformat(),
        }

    @database_sync_to_async
    def _mark_read(self, conversation_id, user):
        now = timezone.now()
        TinNhan.objects.filter(
            hoi_thoai_id=conversation_id,
            da_doc=False
        ).exclude(nguoi_gui=user).update(da_doc=True, doc_luc=now)
```

### 4.2 Component 2: `moc-backend/chat/routing.py`

```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"^ws/chat/(?P<conversation_id>[a-zA-Z0-9_-]+)/?$", consumers.ChatConsumer.as_asgi()),
]
```

### 4.3 Component 3: Chat REST API Extension (`moc-backend/chat/views.py`)

Add the `active` and `messages` actions to `HoiThoaiViewSet`:
```python
    @action(detail=False, methods=["get"])
    def active(self, request):
        user = request.user
        room = HoiThoai.objects.filter(khach_hang=user, trang_thai=HoiThoai.TrangThai.MO).order_by("-cap_nhat_luc").first()
        if not room:
            room = HoiThoai.objects.create(khach_hang=user, trang_thai=HoiThoai.TrangThai.MO)
        return Response(self.get_serializer(room).data)

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        room = self.get_object()
        tin_nhan_list = room.danh_sach_tin_nhan.order_by("tao_luc")
        return Response(TinNhanSerializer(tin_nhan_list, many=True).data)
```

And in `moc-backend/api/urls.py`, add the alias router:
```python
router.register("chat/conversations", ChatRoomViewSet, basename="chat-conversation")
```

---

### 4.4 Component 4: Order FSM Service (`moc-backend/orders/services.py`)

```python
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import DonHang, ChiTietDonHang, LichSuTrangThaiDon
from promotions.models import KhuyenMai, MaKhuyenMai, LichSuDungKhuyenMai


class DichVuDonHang:
    STATUS_ALIASES = {
        "pending": DonHang.TrangThai.CHO_TIEP_NHAN,
        "confirmed": DonHang.TrangThai.DA_XAC_NHAN,
        "cooking": DonHang.TrangThai.DANG_CHE_BIEN,
        "processing": DonHang.TrangThai.DANG_CHE_BIEN,
        "ready": DonHang.TrangThai.SAN_SANG,
        "completed": DonHang.TrangThai.HOAN_TAT,
        "cancelled": DonHang.TrangThai.DA_HUY,
        "canceled": DonHang.TrangThai.DA_HUY,
    }

    VALID_TRANSITIONS = {
        DonHang.TrangThai.CHO_TIEP_NHAN: {
            DonHang.TrangThai.DA_XAC_NHAN,
            DonHang.TrangThai.DA_HUY,
        },
        DonHang.TrangThai.DA_XAC_NHAN: {
            DonHang.TrangThai.DANG_CHE_BIEN,
            DonHang.TrangThai.DA_HUY,
        },
        DonHang.TrangThai.DANG_CHE_BIEN: {
            DonHang.TrangThai.SAN_SANG,
            DonHang.TrangThai.DA_HUY,
        },
        DonHang.TrangThai.SAN_SANG: {
            DonHang.TrangThai.HOAN_TAT,
            DonHang.TrangThai.DA_HUY,
        },
        DonHang.TrangThai.HOAN_TAT: set(),
        DonHang.TrangThai.DA_HUY: set(),
    }

    @classmethod
    def chuan_hoa_trang_thai(cls, status_str):
        if not status_str:
            return None
        s = str(status_str).lower().strip()
        return cls.STATUS_ALIASES.get(s, s)

    @classmethod
    def kiem_tra_chuyen_trang_thai(cls, trang_thai_cu, trang_thai_moi):
        allowed = cls.VALID_TRANSITIONS.get(trang_thai_cu, set())
        return trang_thai_moi in allowed

    @staticmethod
    def broadcast_order_status_update(don_hang, trang_thai_cu, trang_thai_moi, nguoi_dung, ghi_chu=""):
        channel_layer = get_channel_layer()
        if not channel_layer:
            return

        user_name = (
            getattr(nguoi_dung, "ho_ten", None)
            or getattr(nguoi_dung, "username", "Hệ thống")
            if nguoi_dung else "Hệ thống"
        )
        user_id = nguoi_dung.id if nguoi_dung else None

        payload = {
            "type": "order_status_update",
            "data": {
                "order_id": don_hang.id,
                "order_number": don_hang.ma_don_hang,
                "from_status": trang_thai_cu,
                "to_status": trang_thai_moi,
                "status": trang_thai_moi,
                "changed_by": user_name,
                "changed_by_id": user_id,
                "note": ghi_chu,
                "timestamp": timezone.now().isoformat(),
            }
        }

        async_to_sync(channel_layer.group_send)(f"order_{don_hang.id}", payload)
        async_to_sync(channel_layer.group_send)(f"order_{don_hang.ma_don_hang}", payload)
        async_to_sync(channel_layer.group_send)("staff_orders", payload)

    @classmethod
    @transaction.atomic
    def doi_trang_thai(cls, don_hang, trang_thai_moi_raw, nguoi_dung, ghi_chu=""):
        trang_thai_moi = cls.chuan_hoa_trang_thai(trang_thai_moi_raw)

        if trang_thai_moi not in DonHang.TrangThai.values:
            raise ValidationError({"status": f"Trạng thái '{trang_thai_moi_raw}' không hợp lệ."})

        # Pessimistic row locking
        dh = DonHang.objects.select_for_update().get(id=don_hang.id)
        trang_thai_cu = dh.trang_thai

        if trang_thai_cu == trang_thai_moi:
            raise ValidationError({"status": f"Đơn hàng đã ở trạng thái '{trang_thai_cu}'."})

        # Validate FSM transition rules
        if not cls.kiem_tra_chuyen_trang_thai(trang_thai_cu, trang_thai_moi):
            raise ValidationError({
                "status": f"Không thể chuyển trạng thái đơn hàng từ '{trang_thai_cu}' sang '{trang_thai_moi}'."
            })

        # Role & authorization check
        is_staff = nguoi_dung.is_staff or getattr(nguoi_dung, "la_nhan_vien_nha_hang", False)
        if not is_staff:
            if dh.khach_hang_id != nguoi_dung.id:
                raise PermissionDenied("Bạn không có quyền thay đổi trạng thái đơn hàng này.")
            if trang_thai_moi != DonHang.TrangThai.DA_HUY or trang_thai_cu != DonHang.TrangThai.CHO_TIEP_NHAN:
                raise ValidationError({
                    "status": "Khách hàng chỉ có thể hủy đơn khi đơn hàng đang ở trạng thái chờ tiếp nhận."
                })

        # BOM Inventory Deduction / Return
        if trang_thai_moi == DonHang.TrangThai.DA_XAC_NHAN:
            from foods.services import DichVuKho
            DichVuKho.khau_tru_nguyen_lieu_bom(
                danh_sach_mon=dh.danh_sach_mon.all(),
                loai_tham_chieu="don_hang",
                id_tham_chieu=dh.id,
                nguoi_dung=nguoi_dung,
                ghi_chu=ghi_chu or f"Xuất kho khi xác nhận đơn hàng {dh.ma_don_hang}"
            )
        elif trang_thai_moi == DonHang.TrangThai.DA_HUY and trang_thai_cu in [DonHang.TrangThai.DA_XAC_NHAN, DonHang.TrangThai.DANG_CHE_BIEN]:
            from foods.services import DichVuKho
            DichVuKho.hoan_tra_nguyen_lieu_bom(
                loai_tham_chieu="don_hang",
                id_tham_chieu=dh.id,
                nguoi_dung=nguoi_dung,
                ghi_chu=ghi_chu or f"Hoàn kho do hủy đơn hàng {dh.ma_don_hang}"
            )

        dh.trang_thai = trang_thai_moi
        dh.save(update_fields=["trang_thai", "cap_nhat_luc"])

        clean_note = (ghi_chu or "")[:255]
        LichSuTrangThaiDon.objects.create(
            don_hang=dh,
            tu_trang_thai=trang_thai_cu,
            sang_trang_thai=trang_thai_moi,
            doi_boi=nguoi_dung,
            ghi_chu=clean_note,
        )

        # Trigger broadcast post transaction commit
        transaction.on_commit(
            lambda: cls.broadcast_order_status_update(
                don_hang=dh,
                trang_thai_cu=trang_thai_cu,
                trang_thai_moi=trang_thai_moi,
                nguoi_dung=nguoi_dung,
                ghi_chu=clean_note,
            )
        )

        return dh
```

### 4.5 Component 5: Order Consumers (`moc-backend/orders/consumers.py`)

```python
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import DonHang


class OrderTrackingConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for individual order tracking by customer or staff.
    Path: /ws/orders/<order_id>/
    """

    async def connect(self):
        self.order_id = self.scope["url_route"]["kwargs"].get("order_id")
        self.user = self.scope.get("user")

        self.order_data = await self._get_order(self.order_id, self.user)
        if not self.order_data:
            await self.close(code=4404)
            return

        self.group_id_name = f"order_{self.order_data['id']}"
        self.group_code_name = f"order_{self.order_data['order_number']}"

        await self.channel_layer.group_add(self.group_id_name, self.channel_name)
        await self.channel_layer.group_add(self.group_code_name, self.channel_name)

        await self.accept()

        # Send immediate order snapshot
        await self.send_json({
            "type": "order_snapshot",
            "data": self.order_data,
        })

    async def disconnect(self, close_code):
        if hasattr(self, "group_id_name"):
            await self.channel_layer.group_discard(self.group_id_name, self.channel_name)
        if hasattr(self, "group_code_name"):
            await self.channel_layer.group_discard(self.group_code_name, self.channel_name)

    async def order_status_update(self, event):
        await self.send_json({
            "type": "order_status_update",
            "data": event["data"],
        })

    @database_sync_to_async
    def _get_order(self, order_id_or_code, user):
        try:
            if str(order_id_or_code).isdigit():
                order = DonHang.objects.get(id=int(order_id_or_code))
            else:
                order = DonHang.objects.get(ma_don_hang__iexact=str(order_id_or_code))

            if user and user.is_authenticated:
                is_staff = user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False)
                if not is_staff and order.khach_hang_id != user.id:
                    return None
            return {
                "id": order.id,
                "order_number": order.ma_don_hang,
                "status": order.trang_thai,
                "order_type": order.hinh_thuc,
                "total": float(order.tong_tien),
                "created_at": order.tao_luc.isoformat(),
            }
        except DonHang.DoesNotExist:
            return None


class StaffOrderConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for staff global order monitoring and kitchen display.
    Path: /ws/orders/staff/
    """

    async def connect(self):
        self.user = self.scope.get("user")

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return

        is_staff = self.user.is_staff or getattr(self.user, "la_nhan_vien_nha_hang", False)
        if not is_staff:
            await self.close(code=4403)
            return

        self.room_group_name = "staff_orders"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        await self.send_json({
            "type": "staff_connected",
            "message": "Đã kết nối luồng theo dõi đơn hàng nhân viên",
            "staff_id": self.user.id,
        })

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def order_status_update(self, event):
        await self.send_json({
            "type": "order_status_update",
            "data": event["data"],
        })

    async def order_created(self, event):
        await self.send_json({
            "type": "order_created",
            "data": event["data"],
        })
```

### 4.6 Component 6: Order Routing (`moc-backend/orders/routing.py`)

```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"^ws/orders/staff/?$", consumers.StaffOrderConsumer.as_asgi()),
    re_path(r"^ws/orders/(?P<order_id>[a-zA-Z0-9_-]+)/?$", consumers.OrderTrackingConsumer.as_asgi()),
]
```

---

## 5. Verification Method

### 5.1 Verification Test Suite Architecture

To verify the complete functionality, create two test files in `moc-backend/`:
1. `moc-backend/chat/tests.py`
2. `moc-backend/orders/tests.py`

#### A. Daphne Mock Test Setup Helper
Because `daphne` is omitted in the offline environment, prepend tests with this stub to enable `WebsocketCommunicator`:
```python
import sys, types

if "daphne" not in sys.modules:
    daphne_mod = types.ModuleType("daphne")
    daphne_mod.testing = types.SimpleNamespace(DaphneProcess=object)
    sys.modules["daphne"] = daphne_mod
    sys.modules["daphne.testing"] = daphne_mod.testing

from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
```

#### B. Test Matrix for Chat (`chat/tests.py`)
- `test_chat_authenticated_connection`: Connect customer to own conversation $\rightarrow$ Returns `connection_established`.
- `test_chat_unauthenticated_connection_rejected`: Connect `AnonymousUser` $\rightarrow$ Rejects with close code `4401`.
- `test_chat_unauthorized_customer_rejected`: Customer B connects to Customer A's conversation $\rightarrow$ Rejects with close code `4403`.
- `test_chat_staff_connection_allowed`: Staff connects to Customer A's conversation $\rightarrow$ Accepted.
- `test_chat_message_persistence_and_broadcast`:
  * Communicator A sends `{"action": "send_message", "message": "Chào Mộc Quán"}`.
  * Receiver Communicator B receives `chat_message` event with matching content and sender ID.
  * DB query verifies: `TinNhan.objects.filter(hoi_thoai=room).count() == 1` and `room.tin_nhan_cuoi_luc` is updated.
- `test_chat_empty_message_validation`: Sending `{"message": "   "}` returns error and creates 0 records in DB.
- `test_chat_typing_indicator`: Sender sends typing event $\rightarrow$ peer receives `chat_typing`, sender does not receive echo.
- `test_chat_rest_api_active_and_history`:
  * GET `/api/chat/rooms/active/` or `/api/chat/conversations/active/` creates/retrieves active room.
  * GET `/api/chat/rooms/<id>/messages/` returns message history.

#### C. Test Matrix for Order FSM (`orders/tests.py`)
- `test_order_fsm_valid_lifecycle`:
  * Initial: `cho_tiep_nhan`.
  * Transition 1: `cho_tiep_nhan` $\rightarrow$ `da_xac_nhan` (Staff).
  * Transition 2: `da_xac_nhan` $\rightarrow$ `dang_che_bien` (Kitchen).
  * Transition 3: `dang_che_bien` $\rightarrow$ `san_sang` (Kitchen).
  * Transition 4: `san_sang` $\rightarrow$ `hoan_tat` (Waiter/Delivery).
  * Assert status at each step, assert 4 audit records in `LichSuTrangThaiDon` with correct user and timestamps.
- `test_order_fsm_valid_cancellations`:
  * `cho_tiep_nhan` $\rightarrow$ `da_huy` (Customer or staff).
  * `da_xac_nhan` $\rightarrow$ `da_huy` (Staff).
  * `dang_che_bien` $\rightarrow$ `da_huy` (Staff).
  * `san_sang` $\rightarrow$ `da_huy` (Staff).
- `test_order_fsm_invalid_transitions`:
  * Skip: `cho_tiep_nhan` $\rightarrow$ `san_sang` raises `ValidationError` (HTTP 400).
  * Skip: `cho_tiep_nhan` $\rightarrow$ `hoan_tat` raises `ValidationError` (HTTP 400).
  * Terminal: `hoan_tat` $\rightarrow$ `da_huy` raises `ValidationError` (HTTP 400).
  * Terminal: `da_huy` $\rightarrow$ `da_xac_nhan` raises `ValidationError` (HTTP 400).
  * Same state: `cho_tiep_nhan` $\rightarrow$ `cho_tiep_nhan` raises `ValidationError` (HTTP 400).
- `test_order_customer_cancellation_permissions`:
  * Customer can cancel pending order (`cho_tiep_nhan`).
  * Customer CANNOT cancel confirmed order (`da_xac_nhan`) $\rightarrow$ raises `ValidationError` / `PermissionDenied`.
  * Customer CANNOT move order to `dang_che_bien` $\rightarrow$ raises `PermissionDenied`.
- `test_order_websocket_broadcast`:
  * Transition order in `DichVuDonHang.doi_trang_thai(...)`.
  * Verify in-memory channel layer receives payload on `order_{id}`, `order_{code}`, and `staff_orders`.
- `test_order_tracking_consumer`:
  * Connect to `/ws/orders/<order_id>/` $\rightarrow$ receives `order_snapshot`.
  * Status change broadcast $\rightarrow$ receives `order_status_update`.
- `test_staff_order_consumer`:
  * Non-staff $\rightarrow$ close code `4403`.
  * Staff $\rightarrow$ receives `staff_connected` and subsequent `order_status_update` events.

### 5.2 Independent Verification Commands
To execute the test suite once implemented:
```bash
cd /Users/VuVan/Documents/DO-AN/moc-backend
.venv/bin/python manage.py check
.venv/bin/python manage.py test chat orders --settings=config.settings
```
Expected output:
- `manage.py check` passes with 0 issues.
- `manage.py test chat orders` runs all test cases and reports `OK`.

### 5.3 Invalidation Conditions
- Any message broadcast sent to WebSocket before database commit finishes is a violation.
- Any order transition skipping the 6-state progression without being rejected with HTTP 400 is a violation.
- Any customer being able to alter confirmed orders or non-staff accessing `/ws/orders/staff/` is a violation.
