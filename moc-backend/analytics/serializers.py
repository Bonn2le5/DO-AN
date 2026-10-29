from rest_framework import serializers
from api.mixins import DualPayloadMixin
from .models import ThongBao, Notification


class ThongBaoSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "title": "tieu_de",
        "content": "noi_dung",
        "message": "noi_dung",
        "type": "loai",
        "notification_type": "loai",
        "is_read": "da_doc",
    }

    class Meta:
        model = ThongBao
        fields = "__all__"
        read_only_fields = ("nguoi_dung", "doc_luc")


NotificationSerializer = ThongBaoSerializer
