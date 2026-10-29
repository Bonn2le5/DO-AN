"""
WebSocket Consumer for 2-way real-time communication between Customer and Restaurant Staff.
Path: /ws/chat/<conversation_id>/
"""

import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import transaction
from django.utils import timezone
from .models import HoiThoai, TinNhan


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    Handles live chat WebSocket connections for customer-staff messaging.
    Guarantees DB persistence into PostgreSQL before broadcasting to the channel group.
    """

    async def connect(self):
        self.conversation_id = (
            self.scope["url_route"]["kwargs"].get("conversation_id")
            or self.scope["url_route"]["kwargs"].get("room_id")
        )
        self.user = self.scope.get("user")

        # 1. Enforce Authentication (reject 4401 if anonymous)
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return

        # 2. Enforce Conversation Access:
        # Staff has access to all conversations; customer only if room.khach_hang_id == user.id (reject 4403 if forbidden)
        has_access, self.room, self.is_staff = await self._check_conversation_access(self.conversation_id, self.user)
        if not has_access:
            await self.close(code=4403)
            return

        self.room_group_name = f"chat_{self.conversation_id}"

        # 3. Join Channel Group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        # 4. Connection confirmation
        sender_name = getattr(self.user, "ho_ten", None) or self.user.get_full_name() or self.user.username
        await self.send_json({
            "type": "connection_established",
            "conversation_id": self.room.id,
            "room_id": str(self.room.id),
            "user_id": self.user.id,
            "username": sender_name,
            "is_staff": self.is_staff,
            "message": "Kết nối phòng chat thành công.",
        })

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive_json(self, content, **kwargs):
        action = content.get("action")
        if not action:
            if any(k in content for k in ("message", "content", "noi_dung", "text")):
                action = "send_message"
            elif "is_typing" in content:
                action = "typing"

        if action in ["send_message", "message", "gui_tin_nhan"]:
            text = (
                content.get("content")
                or content.get("message")
                or content.get("noi_dung")
                or content.get("text")
                or ""
            ).strip()

            # Validate non-empty content
            if not text:
                await self.send_json({
                    "type": "error",
                    "code": "EMPTY_CONTENT",
                    "message": "Nội dung tin nhắn không được để trống.",
                    "error": "Nội dung tin nhắn không được để trống.",
                })
                return

            # Validate content length
            if len(text) > 5000:
                await self.send_json({
                    "type": "error",
                    "code": "MESSAGE_TOO_LONG",
                    "message": "Nội dung tin nhắn vượt quá giới hạn 5000 ký tự.",
                    "error": "Nội dung tin nhắn vượt quá giới hạn 5000 ký tự.",
                })
                return

            msg_type = (
                content.get("message_type")
                or content.get("loai_tin_nhan")
                or content.get("type")
                or TinNhan.LoaiTinNhan.VAN_BAN
            )
            if msg_type not in ["van_ban", "hinh_anh", "he_thong"]:
                msg_type = "van_ban"

            # Atomically save to PostgreSQL BEFORE broadcasting
            msg_payload = await self._save_message(
                conversation_id=self.room.id,
                user=self.user,
                noi_dung=text,
                loai_tin_nhan=msg_type,
            )

            # Broadcast chat_message to channel group
            broadcast_event = {
                "type": "chat_message",
                "data": msg_payload,
                **msg_payload,
            }
            await self.channel_layer.group_send(
                self.room_group_name,
                broadcast_event,
            )

        elif action == "typing":
            is_typing = bool(content.get("is_typing", True))
            sender_name = getattr(self.user, "ho_ten", None) or self.user.get_full_name() or self.user.username
            is_staff = getattr(self, "is_staff", False)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_typing",
                    "conversation_id": self.room.id,
                    "room_id": str(self.room.id),
                    "sender_id": self.user.id,
                    "user_id": self.user.id,
                    "sender_name": sender_name,
                    "user_name": sender_name,
                    "is_staff": is_staff,
                    "is_typing": is_typing,
                },
            )

        elif action in ["mark_read", "read_receipt"]:
            last_id = content.get("last_read_message_id")
            await self._mark_read(self.room.id, self.user, last_id)
            sender_name = getattr(self.user, "ho_ten", None) or self.user.get_full_name() or self.user.username

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_read_receipt",
                    "conversation_id": self.room.id,
                    "room_id": str(self.room.id),
                    "reader_id": self.user.id,
                    "reader_name": sender_name,
                    "last_read_message_id": last_id,
                    "read_at": timezone.now().isoformat(),
                },
            )

    async def chat_message(self, event):
        """Receive message from room group and forward to WebSocket client."""
        await self.send_json(event)

    async def chat_typing(self, event):
        """Broadcasts chat_typing to group excluding sender."""
        if event.get("sender_id") != self.user.id:
            await self.send_json(event)

    async def chat_read_receipt(self, event):
        """Broadcasts chat_read_receipt to group."""
        await self.send_json(event)

    @database_sync_to_async
    def _check_conversation_access(self, conversation_id, user):
        try:
            if str(conversation_id).isdigit():
                room = HoiThoai.objects.filter(id=int(conversation_id)).first()
            else:
                room = None

            if not room:
                return False, None, False

            is_staff = bool(user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False))
            if is_staff or room.khach_hang_id == user.id:
                return True, room, is_staff
            return False, None, is_staff
        except Exception:
            return False, None, False

    @database_sync_to_async
    def _save_message(self, conversation_id, user, noi_dung, loai_tin_nhan):
        with transaction.atomic():
            room = HoiThoai.objects.select_for_update().get(id=conversation_id)
            msg = TinNhan.objects.create(
                hoi_thoai=room,
                nguoi_gui=user,
                noi_dung=noi_dung,
                loai_tin_nhan=loai_tin_nhan,
            )
            now = timezone.now()
            room.tin_nhan_cuoi_luc = now
            is_staff = user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False)

            # Auto-assign staff if unassigned
            if is_staff and room.nhan_vien_id is None:
                room.nhan_vien = user
                room.save(update_fields=["tin_nhan_cuoi_luc", "nhan_vien", "cap_nhat_luc"])
            else:
                room.save(update_fields=["tin_nhan_cuoi_luc", "cap_nhat_luc"])

            sender_name = getattr(user, "ho_ten", None) or user.get_full_name() or user.username
            sender_role = getattr(getattr(user, "vai_tro", None), "ma", "")

            return {
                "id": msg.id,
                "conversation_id": room.id,
                "room_id": str(room.id),
                "hoi_thoai_id": room.id,
                "sender_id": user.id,
                "nguoi_gui_id": user.id,
                "sender_name": sender_name,
                "sender_role": sender_role,
                "is_staff": is_staff,
                "content": msg.noi_dung,
                "noi_dung": msg.noi_dung,
                "message": msg.noi_dung,
                "message_type": msg.loai_tin_nhan,
                "loai_tin_nhan": msg.loai_tin_nhan,
                "is_read": msg.da_doc,
                "da_doc": msg.da_doc,
                "created_at": msg.tao_luc.isoformat(),
                "tao_luc": msg.tao_luc.isoformat(),
            }

    @database_sync_to_async
    def _mark_read(self, conversation_id, user, last_id=None):
        now = timezone.now()
        qs = TinNhan.objects.filter(
            hoi_thoai_id=conversation_id,
            da_doc=False,
        ).exclude(nguoi_gui=user)
        if last_id is not None and str(last_id).isdigit():
            qs = qs.filter(id__lte=int(last_id))
        qs.update(da_doc=True, doc_luc=now)
