from rest_framework import serializers
from api.mixins import DualPayloadMixin
from .models import HoiThoai, TinNhan, ChatRoom, ChatMessage


class TinNhanSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "room": "hoi_thoai",
        "room_id": "hoi_thoai",
        "conversation": "hoi_thoai",
        "conversation_id": "hoi_thoai",
        "message": "noi_dung",
        "content": "noi_dung",
        "message_type": "loai_tin_nhan",
        "type": "loai_tin_nhan",
        "is_read": "da_doc",
    }
    sender_name = serializers.SerializerMethodField()
    is_staff = serializers.SerializerMethodField()

    class Meta:
        model = TinNhan
        fields = "__all__"
        # Message creation happens through a conversation-scoped endpoint, which
        # supplies both relations after validation. Clients must not need to send
        # these IDs (or be able to spoof the sender/conversation).
        read_only_fields = ("hoi_thoai", "nguoi_gui")

    def get_sender_name(self, obj):
        return obj.nguoi_gui.get_full_name() or obj.nguoi_gui.username

    def get_is_staff(self, obj):
        return bool(obj.nguoi_gui.is_staff or getattr(obj.nguoi_gui, "la_nhan_vien_nha_hang", False))


class HoiThoaiSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = HoiThoai
        fields = "__all__"
        read_only_fields = ("khach_hang", "nhan_vien")

    def get_customer_name(self, obj):
        return obj.khach_hang.get_full_name() or obj.khach_hang.username


class HoiThoaiListSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    last_message = serializers.CharField(read_only=True, default="")
    unread_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = HoiThoai
        fields = ("id", "customer_name", "trang_thai", "tin_nhan_cuoi_luc",
                  "last_message", "unread_count")

    def get_customer_name(self, obj):
        return obj.khach_hang.get_full_name() or obj.khach_hang.username


ChatMessageSerializer = TinNhanSerializer
ChatRoomSerializer = HoiThoaiSerializer
