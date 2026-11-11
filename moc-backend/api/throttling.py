"""Giới hạn tần suất gọi API (rate limiting).

Mức giới hạn đọc từ settings.GIOI_HAN_TAN_SUAT mỗi lần kiểm tra (không chốt lúc import),
nên test bật/tắt được bằng override_settings. Phạm vi không có trong cấu hình = không giới hạn.
Bộ đếm nằm trong cache mặc định (Redis), dùng chung cho mọi tiến trình server.
"""
import logging

from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle

logger = logging.getLogger(__name__)


class ChoQuaKhiCacheLoi:
    """Redis (cache chứa bộ đếm) lỗi thì cho request đi qua thay vì làm cả API trả 500.

    Mất giới hạn tạm thời ít hại hơn sập toàn bộ dịch vụ; lỗi được ghi log để biết Redis có vấn đề.
    """

    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception:
            logger.warning("Giới hạn tần suất %s: không đọc được cache, tạm cho qua", self.scope, exc_info=True)
            return True


class _GioiHanCoBan(ChoQuaKhiCacheLoi, SimpleRateThrottle):
    scope = ""

    def __init__(self):
        # Không gọi super().__init__: lớp cha đọc rate một lần lúc khởi tạo từ DEFAULT_THROTTLE_RATES.
        self.rate = self.get_rate()
        self.num_requests, self.duration = self.parse_rate(self.rate)

    def get_rate(self):
        return getattr(settings, "GIOI_HAN_TAN_SUAT", {}).get(self.scope)

    def dinh_danh(self, request):
        raise NotImplementedError

    def get_cache_key(self, request, view):
        dinh_danh = self.dinh_danh(request)
        if not dinh_danh:
            return None
        return self.cache_format % {"scope": self.scope, "ident": dinh_danh}

    def wait(self):
        # Làm tròn lên để thông báo "thử lại sau N giây" không ra 0.
        con_lai = super().wait()
        return None if con_lai is None else max(1, int(con_lai + 0.999))


class GioiHanKhach(_GioiHanCoBan):
    """Mặc định cho khách chưa đăng nhập, theo IP."""
    scope = "khach"

    def dinh_danh(self, request):
        if request.user and request.user.is_authenticated:
            return None
        return self.get_ident(request)


class GioiHanNguoiDung(_GioiHanCoBan):
    """Mặc định cho tài khoản đã đăng nhập, theo id tài khoản."""
    scope = "nguoi_dung"

    def dinh_danh(self, request):
        if request.user and request.user.is_authenticated:
            return f"nd{request.user.pk}"
        return None


class _TheoIP(_GioiHanCoBan):
    def dinh_danh(self, request):
        return self.get_ident(request)


class _TheoEmail(_GioiHanCoBan):
    """Theo email trong body: chặn dò một tài khoản dù kẻ tấn công đổi IP liên tục."""
    truong_email = ("thu_dien_tu", "email")

    def dinh_danh(self, request):
        data = request.data if hasattr(request.data, "get") else {}
        for truong in self.truong_email:
            email = str(data.get(truong) or "").strip().lower()
            if email:
                return email
        return None


class GioiHanDangNhapIP(_TheoIP):
    scope = "dang_nhap_ip"


class GioiHanDangNhapTaiKhoan(_TheoEmail):
    scope = "dang_nhap_tai_khoan"


class GioiHanDangKy(_TheoIP):
    scope = "dang_ky"


class GioiHanGuiOtp(_TheoEmail):
    scope = "gui_otp"


class GioiHanGuiOtpIP(_TheoIP):
    scope = "gui_otp_ip"


class GioiHanNhapOtp(_TheoEmail):
    scope = "nhap_otp"


class GioiHanNhapOtpIP(_TheoIP):
    scope = "nhap_otp_ip"


class GioiHanDoiMatKhau(_GioiHanCoBan):
    scope = "doi_mat_khau"

    def dinh_danh(self, request):
        return f"nd{request.user.pk}" if request.user and request.user.is_authenticated else self.get_ident(request)


class GioiHanDangNhapAdmin(_TheoIP):
    """Trang đăng nhập /admin của Django: dùng cho cả HttpRequest thường (chỉ đọc META)."""
    scope = "dang_nhap_admin"
