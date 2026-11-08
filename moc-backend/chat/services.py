from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils import timezone
from .models import HoiThoai, TinNhan

STAFF_GROUP = "staff_inbox"


def is_staff_user(user):
    return bool(user.is_superuser or getattr(user, "la_quan_tri_vien", False) or getattr(user, "la_quan_ly_chi_nhanh", False))


def serialize_message(msg, client_id=None):
    u = msg.nguoi_gui
    return {
        "id": msg.id,
        "conversation_id": msg.hoi_thoai_id,
        "sender_id": u.id,
        "sender_name": getattr(u, "ho_ten", None) or u.get_full_name() or u.username,
        "is_staff": is_staff_user(u),
        "content": msg.noi_dung,
        "message_type": msg.loai_tin_nhan,
        "is_read": msg.da_doc,
        "created_at": msg.tao_luc.isoformat(),
        "client_id": client_id,
    }


@transaction.atomic
def save_message(*, room_id, user, text, msg_type="van_ban", client_id=None):
    # Tin hệ thống không được gửi từ người dùng; khách chỉ gửi văn bản.
    allowed = ("van_ban", "hinh_anh") if is_staff_user(user) else ("van_ban",)
    if msg_type not in allowed:
        msg_type = "van_ban"
    room = HoiThoai.objects.select_for_update().get(id=room_id)
    msg = TinNhan.objects.create(hoi_thoai=room, nguoi_gui=user, noi_dung=text, loai_tin_nhan=msg_type)
    room.tin_nhan_cuoi_luc = msg.tao_luc
    fields = ["tin_nhan_cuoi_luc", "cap_nhat_luc"]
    if is_staff_user(user) and room.nhan_vien_id is None:
        room.nhan_vien = user
        fields.append("nhan_vien")
    room.save(update_fields=fields)
    return room, serialize_message(msg, client_id)


def broadcast_message(room, payload):
    """Dùng trong code sync (REST view)."""
    send = async_to_sync(get_channel_layer().group_send)
    send(f"chat_{room.id}", {"type": "chat_message", **payload})
    inbox = {"type": "inbox_update", "conversation_id": room.id,
             "customer_id": room.khach_hang_id, "last_message": payload}
    send(STAFF_GROUP, inbox)
    send(f"user_{room.khach_hang_id}", inbox)


def broadcast_read(room, reader, last_id=None):
    async_to_sync(get_channel_layer().group_send)(f"chat_{room.id}", {
        "type": "chat_read_receipt", "conversation_id": room.id,
        "reader_id": reader.id, "last_read_message_id": last_id,
        "read_at": timezone.now().isoformat(),
    })
