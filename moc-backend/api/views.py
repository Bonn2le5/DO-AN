from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response


@api_view(["GET"])
@throttle_classes([])  # máy chủ kiểm tra sức khoẻ (Render) gọi liên tục, không giới hạn
def health_check(request):
    return Response({"status": "ok"})
