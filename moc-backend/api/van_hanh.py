"""Sự kiện realtime "vận hành cập nhật" cho màn hình nhân viên (sơ đồ bàn, đơn hàng, đặt bàn).

Bắt bằng signal post_save/post_delete nên mọi đường sửa (service, admin Django, IPN thanh toán)
đều phát, không phải nhớ gọi ở từng chỗ. Sự kiện chỉ báo "cái gì đổi ở chi nhánh nào";
trang nhận thì tự tải lại dữ liệu qua REST (đã có phân quyền), nên không lộ dữ liệu qua WebSocket.

Không bắt được QuerySet.update()/bulk_create (không bắn signal); các thao tác đó luôn đi kèm
một lần lưu khác trong cùng nghiệp vụ, hoặc là việc nền (huỷ giữ chỗ quá hạn) chấp nhận chậm.
"""
import logging

from django.db import transaction
from django.db.models.signals import post_delete, post_save

logger = logging.getLogger(__name__)

NHOM_TAT_CA = "staff_orders"  # quản trị viên xem mọi chi nhánh (cùng nhóm với luồng đơn hàng)


def nhom_chi_nhanh(chi_nhanh_id):
    return f"staff_orders_branch_{chi_nhanh_id}"


def _phat(su_kien):
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    try:
        layer = get_channel_layer()
        if layer is None:
            return
        gui = async_to_sync(layer.group_send)
        gui(NHOM_TAT_CA, su_kien)
        if su_kien.get("chi_nhanh_id"):
            gui(nhom_chi_nhanh(su_kien["chi_nhanh_id"]), su_kien)
    except Exception:
        # Redis lỗi: dữ liệu đã lưu, màn hình nhân viên vẫn tự tải lại định kỳ.
        logger.warning("Không phát được sự kiện vận hành %s", su_kien, exc_info=True)


def bao_thay_doi(doi_tuong, instance, xoa=False):
    """Hẹn phát sau khi giao dịch commit (rollback thì không phát)."""
    su_kien = {
        "type": "van_hanh_cap_nhat",
        "doi_tuong": doi_tuong,
        "id": instance.pk,
        "chi_nhanh_id": getattr(instance, "chi_nhanh_id", None),
        "xoa": xoa,
    }
    transaction.on_commit(lambda: _phat(su_kien))


def ket_noi_signal():
    from orders.models import DonHang
    from reservations.models import BanAn, DatBan, PhienPhucVu

    for model, ten in ((BanAn, "ban_an"), (PhienPhucVu, "phien_phuc_vu"), (DatBan, "dat_ban"), (DonHang, "don_hang")):
        post_save.connect(
            lambda sender, instance, _ten=ten, **kw: bao_thay_doi(_ten, instance),
            sender=model, weak=False, dispatch_uid=f"van_hanh_luu_{ten}",
        )
        post_delete.connect(
            lambda sender, instance, _ten=ten, **kw: bao_thay_doi(_ten, instance, xoa=True),
            sender=model, weak=False, dispatch_uid=f"van_hanh_xoa_{ten}",
        )
