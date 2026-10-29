from rest_framework import serializers
from api.mixins import DualPayloadMixin
from .models import DanhMucBaiViet, BaiViet, PostCategory, Post


class DanhMucBaiVietSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "name": "ten",
        "slug": "duong_dan",
        "description": "mo_ta",
    }

    class Meta:
        model = DanhMucBaiViet
        fields = "__all__"


class BaiVietSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "title": "tieu_de",
        "slug": "duong_dan",
        "content": "noi_dung",
        "category": "danh_muc",
        "category_id": "danh_muc",
        "thumbnail": "anh_dai_dien",
        "thumbnail_url": "anh_dai_dien",
        "status": "trang_thai",
        "published_at": "dang_luc",
    }
    ten_danh_muc = serializers.CharField(source="danh_muc.ten", read_only=True)
    ten_tac_gia = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="danh_muc.ten", read_only=True)
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = BaiViet
        fields = "__all__"
        read_only_fields = ("tac_gia",)

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, "copy") else dict(data)
        category = data.get("category", data.get("danh_muc"))
        if category not in (None, "") and not str(category).isdigit():
            obj, _ = DanhMucBaiViet.objects.get_or_create(ten=str(category))
            data["danh_muc"] = obj.pk
        return super().to_internal_value(data)

    def get_ten_tac_gia(self, obj):
        return obj.tac_gia.get_full_name() or obj.tac_gia.username if obj.tac_gia else "Nhà hàng"

    get_author_name = get_ten_tac_gia


PostCategorySerializer = DanhMucBaiVietSerializer
PostSerializer = BaiVietSerializer
