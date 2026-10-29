import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import TuongTacMonAn, GoiYMonAn

logger = logging.getLogger(__name__)


@receiver(post_save, sender=TuongTacMonAn)
@receiver(post_delete, sender=TuongTacMonAn)
def xoa_cache_goi_y_khi_co_tuong_tac(sender, instance, **kwargs):
    """
    Tự động vô hiệu hóa cache GoiYMonAn khi người dùng có tương tác mới
    hoặc cập nhật/xóa tương tác món ăn (đặt món, đánh giá, xem, yêu thích, thêm giỏ).
    Đảm bảo lượt truy vấn gợi ý tiếp theo sẽ phản ánh khẩu vị cập nhật mới nhất.
    """
    if kwargs.get("raw", False):
        return

    nguoi_dung_id = getattr(instance, "nguoi_dung_id", None)
    if nguoi_dung_id:
        so_luong_xoa, _ = GoiYMonAn.objects.filter(nguoi_dung_id=nguoi_dung_id).delete()
        if so_luong_xoa > 0:
            logger.debug(
                "Đã xóa %s bản ghi gợi ý cache của người dùng ID %s do thay đổi tương tác.",
                so_luong_xoa,
                nguoi_dung_id,
            )
