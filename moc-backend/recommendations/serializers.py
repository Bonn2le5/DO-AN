from rest_framework import serializers
from foods.models import MonAn
from foods.serializers import MonAnSerializer
from .models import TuongTacMonAn, GoiYMonAn, SuKienGoiY
from .services import TRONG_SO_TUONG_TAC, ALIAS_TRONG_SO, MODEL_VERSION_COLD_START, LOAI_TUONG_TAC_TU_CLIENT


class TuongTacMonAnSerializer(serializers.ModelSerializer):
    """
    Serializer cho tương tác món ăn với cơ chế tự động điền trọng số
    và hỗ trợ đa dạng định dạng trường tiếng Anh & tiếng Việt.
    """

    class Meta:
        model = TuongTacMonAn
        fields = ("id", "mon_an", "loai_tuong_tac", "trong_so", "tao_luc")
        # Trọng số do server gán theo loại tương tác — client không được tự đặt
        read_only_fields = ("trong_so", "tao_luc")

    def validate(self, attrs):
        # Chuẩn hóa loại tương tác nếu nhận được bí danh tiếng Anh hoặc viết tắt
        loai = attrs.get("loai_tuong_tac", "")
        alias_norm = {
            "view": "xem",
            "thich": "yeu_thich",
            "like": "yeu_thich",
            "favorite": "yeu_thich",
            "dat_hang": "dat_mon",
            "order": "dat_mon",
            "review": "danh_gia",
            "rating": "danh_gia",
        }
        if loai in alias_norm:
            attrs["loai_tuong_tac"] = alias_norm[loai]
            loai = attrs["loai_tuong_tac"]

        # dat_mon / danh_gia chỉ được ghi từ đơn đặt và đánh giá thật phía server
        if loai not in LOAI_TUONG_TAC_TU_CLIENT:
            raise serializers.ValidationError(
                {"loai_tuong_tac": "Chỉ được ghi tương tác 'xem' hoặc 'yeu_thich'."}
            )
        attrs["trong_so"] = TRONG_SO_TUONG_TAC[loai]

        return super().validate(attrs)


class GoiYMonAnSerializer(serializers.ModelSerializer):
    """
    Serializer cho kết quả gợi ý món ăn.
    Bao gồm thông tin chi tiết món ăn và cờ is_cold_start.
    """

    chi_tiet_mon = MonAnSerializer(source="mon_an", read_only=True)
    chi_tiet_mon_an = MonAnSerializer(source="mon_an", read_only=True)
    is_cold_start = serializers.SerializerMethodField()

    class Meta:
        model = GoiYMonAn
        fields = (
            "id",
            "nguoi_dung",
            "mon_an",
            "diem_tuong_dong",
            "ly_do_goi_y",
            "phien_ban_model",
            "is_cold_start",
            "chi_tiet_mon",
            "chi_tiet_mon_an",
            "tao_luc",
        )
        # Trọng số do server gán theo loại tương tác — client không được tự đặt
        read_only_fields = ("trong_so", "tao_luc")

    def get_is_cold_start(self, obj):
        return (
            getattr(obj, "phien_ban_model", "") == MODEL_VERSION_COLD_START
            or getattr(obj, "ly_do_goi_y", "") == "Phổ biến hôm nay"
        )


class SuKienGoiYSerializer(serializers.Serializer):
    loai_su_kien = serializers.ChoiceField(choices=SuKienGoiY.LoaiSuKien.choices)
    vi_tri = serializers.ChoiceField(choices=SuKienGoiY.ViTri.choices, default=SuKienGoiY.ViTri.TRANG_CHU)
    mon_an_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), min_length=1, max_length=50)
    phien_ban_model = serializers.CharField(max_length=30, required=False, allow_blank=True)
