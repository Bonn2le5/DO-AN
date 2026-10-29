from decimal import Decimal
from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from api.permissions import LaNhanVienHoacChiDoc
from .models import DanhMuc, NguyenLieu, MonAn, TheMonAn, LichSuXuatNhapKho
from .serializers import DanhMucSerializer, NguyenLieuSerializer, MonAnSerializer, TheMonAnSerializer, LichSuKhoSerializer


class DanhMucViewSet(viewsets.ModelViewSet):
    queryset = DanhMuc.objects.all()
    serializer_class = DanhMucSerializer
    permission_classes = [LaNhanVienHoacChiDoc]
    lookup_field = "duong_dan"


class TheMonAnViewSet(viewsets.ModelViewSet):
    queryset = TheMonAn.objects.all()
    serializer_class = TheMonAnSerializer
    permission_classes = [LaNhanVienHoacChiDoc]
    lookup_field = "duong_dan"


class NguyenLieuViewSet(viewsets.ModelViewSet):
    queryset = NguyenLieu.objects.all()
    serializer_class = NguyenLieuSerializer
    permission_classes = [LaNhanVienHoacChiDoc]


class LichSuKhoViewSet(viewsets.ModelViewSet):
    queryset = LichSuXuatNhapKho.objects.select_related("nguyen_lieu")
    serializer_class = LichSuKhoSerializer
    permission_classes = [LaNhanVienHoacChiDoc]

    @transaction.atomic
    def perform_create(self, serializer):
        nguyen_lieu = serializer.validated_data["nguyen_lieu"]
        nl = NguyenLieu.objects.select_for_update().get(id=nguyen_lieu.id)
        so_luong = Decimal(str(serializer.validated_data["so_luong"]))
        loai_gd = serializer.validated_data["loai_giao_dich"]

        ton_truoc = nl.ton_kho_hien_tai
        if loai_gd == LichSuXuatNhapKho.LoaiGiaoDich.NHAP:
            ton_sau = ton_truoc + so_luong
        elif loai_gd == LichSuXuatNhapKho.LoaiGiaoDich.XUAT:
            if ton_truoc < so_luong:
                raise ValidationError(
                    {"so_luong": f"Tồn kho hiện tại ({ton_truoc} {nl.don_vi}) không đủ để xuất {so_luong} {nl.don_vi}."}
                )
            ton_sau = ton_truoc - so_luong
        elif loai_gd == LichSuXuatNhapKho.LoaiGiaoDich.DIEU_CHINH:
            ton_sau = so_luong
        else:
            raise ValidationError({"loai_giao_dich": f"Loại giao dịch '{loai_gd}' không hợp lệ."})

        nl.ton_kho_hien_tai = ton_sau
        nl.save(update_fields=["ton_kho_hien_tai", "cap_nhat_luc"])

        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(
            tao_boi=user,
            ton_kho_truoc=ton_truoc,
            ton_kho_sau=ton_sau,
        )


class MonAnViewSet(viewsets.ModelViewSet):
    serializer_class = MonAnSerializer
    permission_classes = [LaNhanVienHoacChiDoc]
    lookup_field = "duong_dan"

    def get_queryset(self):
        bo_loc = MonAn.objects.select_related("danh_muc").prefetch_related("hinh_anh", "nguyen_lieu", "the_mon_an")
        tham_so = self.request.query_params

        # Ẩn món không hoạt động với khách thường
        if not self.request.user.is_authenticated or not self.request.user.la_nhan_vien_nha_hang:
            bo_loc = bo_loc.filter(hien_thi=True)

        if tham_so.get("danh_muc"):
            bo_loc = bo_loc.filter(
                Q(danh_muc__duong_dan=tham_so["danh_muc"]) | Q(danh_muc_id=tham_so["danh_muc"])
            )
        if tham_so.get("tim_kiem"):
            tu_khoa = tham_so["tim_kiem"]
            bo_loc = bo_loc.filter(
                Q(ten__icontains=tu_khoa) |
                Q(mo_ta_ngan__icontains=tu_khoa) |
                Q(the_mon_an__ten__icontains=tu_khoa) |
                Q(nguyen_lieu__ten__icontains=tu_khoa)
            ).distinct()
        if tham_so.get("la_mon_chay") in ("true", "1"):
            bo_loc = bo_loc.filter(la_mon_chay=True)
        if tham_so.get("con_hang") in ("true", "1"):
            bo_loc = bo_loc.filter(con_hang=True)
        if tham_so.get("gia_toi_da"):
            bo_loc = bo_loc.filter(don_gia__lte=tham_so["gia_toi_da"])
        if tham_so.get("co_cay") in ("true", "1"):
            bo_loc = bo_loc.filter(do_cay__gte=1)

        thu_tu = {
            "pho_bien": "-so_luot_danh_gia",
            "danh_gia": "-diem_danh_gia",
            "gia_tang": "don_gia",
            "gia_giam": "-don_gia",
            "moi_nhat": "-tao_luc",
        }.get(tham_so.get("sap_xep"), "-tao_luc")

        return bo_loc.order_by(thu_tu)

    @action(detail=True, methods=["get"])
    def mon_lien_quan(self, request, duong_dan=None):
        mon_hien_tai = self.get_object()
        danh_sach = self.get_queryset().filter(
            danh_muc=mon_hien_tai.danh_muc
        ).exclude(pk=mon_hien_tai.pk)[:int(request.query_params.get("gioi_han", 3))]
        return Response(MonAnSerializer(danh_sach, many=True, context={"request": request}).data)


# Backward-compatible viewset aliases
CategoryViewSet = DanhMucViewSet
TagViewSet = TheMonAnViewSet
IngredientViewSet = NguyenLieuViewSet
FoodViewSet = MonAnViewSet
InventoryHistoryViewSet = LichSuKhoViewSet
