from rest_framework import serializers
from api.mixins import DualPayloadMixin
from foods.models import MonAn, Food
from foods.serializers import MonAnSerializer, FoodSerializer
from .models import TuongTacMonAn, GoiYMonAn, FoodInteraction, Recommendation
from .services import TRONG_SO_TUONG_TAC, ALIAS_TRONG_SO, MODEL_VERSION_COLD_START


class TuongTacMonAnSerializer(DualPayloadMixin, serializers.ModelSerializer):
    """
    Serializer cho tương tác món ăn với cơ chế tự động điền trọng số
    và hỗ trợ đa dạng định dạng trường tiếng Anh & tiếng Việt.
    """
    FIELD_ALIASES = {
        "food": "mon_an",
        "food_id": "mon_an",
        "interaction_type": "loai_tuong_tac",
        "type": "loai_tuong_tac",
        "weight": "trong_so",
    }

    class Meta:
        model = TuongTacMonAn
        fields = ("id", "mon_an", "loai_tuong_tac", "trong_so", "tao_luc")
        read_only_fields = ("tao_luc",)

    def validate(self, attrs):
        # Chuẩn hóa loại tương tác nếu nhận được bí danh tiếng Anh hoặc viết tắt
        loai = attrs.get("loai_tuong_tac", "")
        alias_norm = {
            "view": "xem",
            "thich": "yeu_thich",
            "like": "yeu_thich",
            "favorite": "yeu_thich",
            "gio_hang": "them_gio_hang",
            "cart": "them_gio_hang",
            "add_cart": "them_gio_hang",
            "dat_hang": "dat_mon",
            "order": "dat_mon",
            "review": "danh_gia",
            "rating": "danh_gia",
        }
        if loai in alias_norm:
            attrs["loai_tuong_tac"] = alias_norm[loai]
            loai = attrs["loai_tuong_tac"]

        # Nếu không truyền trọng số hoặc trọng số là 1 mặc định, tự động gán theo nghiệp vụ
        if "trong_so" not in attrs or attrs["trong_so"] == 1:
            attrs["trong_so"] = TRONG_SO_TUONG_TAC.get(loai, 1)

        return super().validate(attrs)


class GoiYMonAnSerializer(DualPayloadMixin, serializers.ModelSerializer):
    """
    Serializer cho kết quả gợi ý món ăn.
    Bao gồm thông tin chi tiết món ăn và cờ is_cold_start.
    """
    FIELD_ALIASES = {
        "food": "mon_an",
        "food_id": "mon_an",
        "score": "diem_tuong_dong",
        "reason": "ly_do_goi_y",
        "model_version": "phien_ban_model",
    }

    chi_tiet_mon = MonAnSerializer(source="mon_an", read_only=True)
    chi_tiet_mon_an = MonAnSerializer(source="mon_an", read_only=True)
    food_detail = MonAnSerializer(source="mon_an", read_only=True)
    score = serializers.FloatField(source="diem_tuong_dong", read_only=True)
    reason = serializers.CharField(source="ly_do_goi_y", read_only=True)
    is_cold_start = serializers.SerializerMethodField()

    class Meta:
        model = GoiYMonAn
        fields = (
            "id",
            "nguoi_dung",
            "mon_an",
            "diem_tuong_dong",
            "score",
            "ly_do_goi_y",
            "reason",
            "phien_ban_model",
            "is_cold_start",
            "chi_tiet_mon",
            "chi_tiet_mon_an",
            "food_detail",
            "tao_luc",
        )
        read_only_fields = ("tao_luc",)

    def get_is_cold_start(self, obj):
        return (
            getattr(obj, "phien_ban_model", "") == MODEL_VERSION_COLD_START
            or getattr(obj, "ly_do_goi_y", "") == "Phổ biến hôm nay"
        )


InteractionSerializer = TuongTacMonAnSerializer
RecommendationSerializer = GoiYMonAnSerializer
