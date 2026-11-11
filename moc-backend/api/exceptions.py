from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler


def xu_ly_ngoai_le(exc, context):
    """Thông báo tiếng Việt khi bị giới hạn tần suất (HTTP 429); lỗi khác giữ nguyên của DRF."""
    response = exception_handler(exc, context)
    if isinstance(exc, Throttled) and response is not None:
        cau = "Bạn thao tác quá nhiều lần."
        if exc.wait:
            cau += f" Vui lòng thử lại sau {int(exc.wait)} giây."
        response.data = {"detail": cau, "thu_lai_sau": int(exc.wait) if exc.wait else None}
    return response
