import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .models import HoiThoai, TinNhan

STAFF_GROUP = "staff_inbox"
logger = logging.getLogger(__name__)


def is_admin_user(user):
    return bool(user.is_superuser or getattr(user, "la_quan_tri_vien", False))


def is_staff_user(user):
    """Người của nhà hàng (admin, quản lý, nhân viên): tin nhắn của họ hiện là phía nhà hàng."""
    return bool(is_admin_user(user) or getattr(user, "la_nhan_vien_nha_hang", False))


def staff_branch_id(user):
    """Chi nhánh mà nhân viên/quản lý phụ trách chat; None với admin và khách."""
    if is_admin_user(user) or not getattr(user, "la_nhan_vien_nha_hang", False):
        return None
    return getattr(user, "chi_nhanh_quan_ly_id", None)


def scope_rooms(qs, user):
    """Admin thấy mọi hội thoại; nhân viên/quản lý chỉ thấy hội thoại của chi nhánh mình;
    khách chỉ thấy hội thoại của chính họ."""
    if is_admin_user(user):
        return qs
    if getattr(user, "la_nhan_vien_nha_hang", False):
        # Kèm hội thoại nhân viên tự mở với tư cách khách (khung chat trên website).
        branch_id = staff_branch_id(user)
        return qs.filter(Q(chi_nhanh_id=branch_id) | Q(khach_hang=user)) if branch_id else qs.filter(khach_hang=user)
    return qs.filter(khach_hang=user)


def can_access_room(user, room):
    if is_admin_user(user) or room.khach_hang_id == user.id:
        return True
    if getattr(user, "la_nhan_vien_nha_hang", False):
        branch_id = staff_branch_id(user)
        return bool(branch_id) and room.chi_nhanh_id == branch_id
    return room.khach_hang_id == user.id


def branch_group(branch_id):
    return f"{STAFF_GROUP}_{branch_id}"


def inbox_groups(room):
    """Nhóm websocket nhận cập nhật hộp thư: admin luôn nhận, chi nhánh phụ trách nhận, và chính khách."""
    groups = [STAFF_GROUP, f"user_{room.khach_hang_id}"]
    if room.chi_nhanh_id:
        groups.append(branch_group(room.chi_nhanh_id))
    return groups


def chi_nhanh_mac_dinh(user):
    """Chi nhánh cho hội thoại mới: lượt đặt bàn sắp tới gần nhất, nếu không có thì lượt gần đây nhất."""
    from reservations.models import DatBan
    from foods.services import hom_nay_vn
    qs = DatBan.objects.filter(nguoi_dung=user).exclude(trang_thai=DatBan.TrangThai.DA_HUY)
    upcoming = qs.filter(ngay_dat__gte=hom_nay_vn()).order_by("ngay_dat", "gio_bat_dau").values_list("chi_nhanh_id", flat=True).first()
    return upcoming or qs.order_by("-ngay_dat", "-gio_bat_dau").values_list("chi_nhanh_id", flat=True).first()


def sender_role(user):
    """Vai trò hiển thị cạnh tin nhắn, để nhân viên biết ai trong nhà hàng đã trả lời."""
    if is_admin_user(user):
        return "admin"
    if getattr(user, "la_quan_ly_chi_nhanh", False):
        return "quan_ly"
    if getattr(user, "la_nhan_vien_nha_hang", False):
        return "nhan_vien"
    return "khach"


def serialize_message(msg, client_id=None):
    u = msg.nguoi_gui
    return {
        "id": msg.id,
        "conversation_id": msg.hoi_thoai_id,
        "sender_id": u.id,
        "sender_name": getattr(u, "ho_ten", None) or u.get_full_name() or u.username,
        "is_staff": is_staff_user(u),
        "sender_role": sender_role(u),
        "content": msg.noi_dung,
        "message_type": msg.loai_tin_nhan,
        "is_read": msg.da_doc,
        "created_at": msg.tao_luc.isoformat(),
        "client_id": client_id,
    }


TIN_KET_THUC = "Cuộc tư vấn đã kết thúc"
TIN_MO_LAI = "Khách nhắn lại, cuộc tư vấn được mở lại"


def _tin_he_thong(room, user, text):
    """Tin hệ thống (hiện thành dòng phân cách giữa khung chat) đánh dấu mốc của cuộc tư vấn."""
    msg = TinNhan.objects.create(hoi_thoai=room, nguoi_gui=user, noi_dung=text, loai_tin_nhan=TinNhan.LoaiTinNhan.HE_THONG)
    room.tin_nhan_cuoi_luc = msg.tao_luc
    payload = serialize_message(msg)
    # Phát sau khi lưu xong, trước tin của khách (nếu có) để hai bên thấy đúng thứ tự.
    transaction.on_commit(lambda: broadcast_message(room, payload))
    return payload


@transaction.atomic
def dong_hoi_thoai(room_id, user):
    """Nhà hàng đóng hội thoại: chuyển trạng thái và ghi dòng "Cuộc tư vấn đã kết thúc"."""
    room = HoiThoai.objects.select_for_update().get(id=room_id)
    if room.trang_thai == HoiThoai.TrangThai.DONG:
        return room
    room.trang_thai = HoiThoai.TrangThai.DONG
    _tin_he_thong(room, user, TIN_KET_THUC)
    room.save(update_fields=["trang_thai", "tin_nhan_cuoi_luc", "cap_nhat_luc"])
    return room


@transaction.atomic
def save_message(*, room_id, user, text, msg_type="van_ban", client_id=None):
    # Tin hệ thống không được gửi từ người dùng; khách chỉ gửi văn bản.
    allowed = ("van_ban", "hinh_anh") if is_staff_user(user) else ("van_ban",)
    if msg_type not in allowed:
        msg_type = "van_ban"
    room = HoiThoai.objects.select_for_update().get(id=room_id)
    fields = ["tin_nhan_cuoi_luc", "cap_nhat_luc"]
    if room.trang_thai == HoiThoai.TrangThai.DONG and not is_staff_user(user):
        # Khách nhắn tiếp sau khi đã kết thúc tư vấn: mở lại để nhà hàng trả lời được.
        room.trang_thai = HoiThoai.TrangThai.MO
        fields.append("trang_thai")
        _tin_he_thong(room, user, TIN_MO_LAI)
    msg = TinNhan.objects.create(hoi_thoai=room, nguoi_gui=user, noi_dung=text, loai_tin_nhan=msg_type)
    room.tin_nhan_cuoi_luc = msg.tao_luc
    if is_staff_user(user) and room.nhan_vien_id is None:
        room.nhan_vien = user
        fields.append("nhan_vien")
    room.save(update_fields=fields)
    return room, serialize_message(msg, client_id)


def _gui_nhom(nhom, su_kien):
    """Phát sự kiện realtime; channel layer (Redis) lỗi thì chỉ ghi log.
    Tin nhắn đã lưu DB, client lấy bù qua ?after_id khi kết nối lại."""
    try:
        async_to_sync(get_channel_layer().group_send)(nhom, su_kien)
    except Exception:
        logger.warning("Không phát được sự kiện %s tới nhóm %s", su_kien.get("type"), nhom, exc_info=True)


def broadcast_message(room, payload):
    """Dùng trong code sync (REST view)."""
    _gui_nhom(f"chat_{room.id}", {"type": "chat_message", **payload})
    inbox = {"type": "inbox_update", "conversation_id": room.id, "status": room.trang_thai,
             "customer_id": room.khach_hang_id, "branch_id": room.chi_nhanh_id, "last_message": payload}
    for nhom in inbox_groups(room):
        _gui_nhom(nhom, inbox)


def broadcast_reassigned(room):
    """Báo cho các kết nối đang mở phòng này: consumer tự kiểm tra lại quyền và ngắt người mất quyền."""
    _gui_nhom(f"chat_{room.id}", {"type": "room_reassigned", "conversation_id": room.id, "branch_id": room.chi_nhanh_id})


def broadcast_read(room, reader, last_id=None):
    _gui_nhom(f"chat_{room.id}", {
        "type": "chat_read_receipt", "conversation_id": room.id,
        "reader_id": reader.id, "last_read_message_id": last_id,
        "read_at": timezone.now().isoformat(),
    })
