from rest_framework import serializers
from .models import DanhMucBaiViet, BaiViet, PostCategory, Post


class DanhMucBaiVietSerializer(serializers.ModelSerializer):

    class Meta:
        model = DanhMucBaiViet
        fields = "__all__"


class BaiVietSerializer(serializers.ModelSerializer):
    ten_danh_muc = serializers.CharField(source="danh_muc.ten", read_only=True)
    ten_tac_gia = serializers.SerializerMethodField()

    class Meta:
        model = BaiViet
        fields = "__all__"
        read_only_fields = ("tac_gia",)

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, "copy") else dict(data)
        category = data.get("danh_muc")
        if category not in (None, "") and not str(category).isdigit():
            obj, _ = DanhMucBaiViet.objects.get_or_create(ten=str(category))
            data["danh_muc"] = obj.pk
        return super().to_internal_value(data)

    def get_ten_tac_gia(self, obj):
        return obj.tac_gia.get_full_name() or obj.tac_gia.username if obj.tac_gia else "Nhà hàng"


PostCategorySerializer = DanhMucBaiVietSerializer
PostSerializer = BaiVietSerializer
