from rest_framework import serializers
from .models import ThongBao, Notification


class ThongBaoSerializer(serializers.ModelSerializer):

    class Meta:
        model = ThongBao
        fields = "__all__"
        read_only_fields = ("nguoi_dung", "doc_luc")


NotificationSerializer = ThongBaoSerializer
