import math
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from api.permissions import LaNhanVienHoacChiDoc
from .models import ChiNhanh, Branch
from .serializers import ChiNhanhSerializer, BranchSerializer
from .services import find_nearest_branches


class ChiNhanhViewSet(viewsets.ModelViewSet):
    queryset = ChiNhanh.objects.all()
    serializer_class = ChiNhanhSerializer
    permission_classes = [LaNhanVienHoacChiDoc]

    def get_queryset(self):
        q = ChiNhanh.objects.all()
        user = self.request.user
        is_staff = user.is_authenticated and getattr(user, "la_nhan_vien_nha_hang", False)
        return q if is_staff else q.filter(con_hoat_dong=True)

    def list(self, request, *args, **kwargs):
        # Support proximity ordering in standard list endpoint if lat & lng are supplied
        lat = request.query_params.get("lat") or request.query_params.get("latitude") or request.query_params.get("vi_do")
        lng = request.query_params.get("lng") or request.query_params.get("longitude") or request.query_params.get("kinh_do")

        if lat is not None or lng is not None:
            if lat is None or lng is None:
                return Response(
                    {"detail": "Vui lòng cung cấp cả lat (vĩ độ) và lng (kinh độ)."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                lat_f = float(lat)
                lng_f = float(lng)
            except ValueError:
                return Response({"detail": "Tọa độ lat và lng phải là số thực."}, status=status.HTTP_400_BAD_REQUEST)

            if not (-90.0 <= lat_f <= 90.0 and -180.0 <= lng_f <= 180.0):
                return Response(
                    {"detail": "Tọa độ không hợp lệ (-90 <= lat <= 90, -180 <= lng <= 180)."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            radius = request.query_params.get("radius") or request.query_params.get("radius_km") or request.query_params.get("ban_kinh")
            radius_f = None
            if radius is not None and str(radius).strip() != "":
                try:
                    radius_f = float(radius)
                    if not (radius_f > 0) or math.isnan(radius_f) or math.isinf(radius_f):
                        return Response({"detail": "Bán kính phải lớn hơn 0."}, status=status.HTTP_400_BAD_REQUEST)
                except ValueError:
                    return Response({"detail": "Bán kính radius phải là số thực."}, status=status.HTTP_400_BAD_REQUEST)

            limit = request.query_params.get("limit") or request.query_params.get("so_luong")
            limit_i = None
            if limit is not None and str(limit).strip() != "":
                try:
                    limit_i = int(limit)
                    if limit_i <= 0:
                        return Response({"detail": "Tham số limit phải lớn hơn 0."}, status=status.HTTP_400_BAD_REQUEST)
                except ValueError:
                    return Response({"detail": "Tham số limit phải là số nguyên."}, status=status.HTTP_400_BAD_REQUEST)

            branches = find_nearest_branches(lat_f, lng_f, radius_km=radius_f, limit=limit_i, only_active=True)
            serializer = self.get_serializer(branches, many=True)
            return Response(serializer.data)

        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="nearest")
    def nearest(self, request):
        """
        Find nearest branch to client coordinates.
        Query Params:
        - lat / latitude / vi_do: float (required)
        - lng / longitude / kinh_do: float (required)
        - radius / radius_km / ban_kinh: float (optional)
        - limit / so_luong: int (optional)
        - all / list: bool (optional, return list if true)
        """
        lat = request.query_params.get("lat") or request.query_params.get("latitude") or request.query_params.get("vi_do")
        lng = request.query_params.get("lng") or request.query_params.get("longitude") or request.query_params.get("kinh_do")

        if lat is None or lng is None:
            return Response(
                {"detail": "Vui lòng cung cấp tọa độ lat (vĩ độ) và lng (kinh độ)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lat_f = float(lat)
            lng_f = float(lng)
        except ValueError:
            return Response({"detail": "Tọa độ lat và lng phải là số thực."}, status=status.HTTP_400_BAD_REQUEST)

        if not (-90.0 <= lat_f <= 90.0 and -180.0 <= lng_f <= 180.0):
            return Response(
                {"detail": "Tọa độ không hợp lệ (-90 <= lat <= 90, -180 <= lng <= 180)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        radius = request.query_params.get("radius") or request.query_params.get("radius_km") or request.query_params.get("ban_kinh")
        radius_f = None
        if radius is not None and str(radius).strip() != "":
            try:
                radius_f = float(radius)
                if not (radius_f > 0) or math.isnan(radius_f) or math.isinf(radius_f):
                    return Response({"detail": "Bán kính phải lớn hơn 0."}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return Response({"detail": "Bán kính radius phải là số thực."}, status=status.HTTP_400_BAD_REQUEST)

        limit = request.query_params.get("limit") or request.query_params.get("so_luong")
        limit_i = None
        if limit is not None and str(limit).strip() != "":
            try:
                limit_i = int(limit)
                if limit_i <= 0:
                    return Response({"detail": "Tham số limit phải lớn hơn 0."}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return Response({"detail": "Tham số limit phải là số nguyên."}, status=status.HTTP_400_BAD_REQUEST)

        return_all = str(request.query_params.get("all", "")).lower() in ("true", "1", "yes")

        effective_limit = limit_i if return_all else 1
        if return_all and limit_i is None:
            effective_limit = None

        branches = find_nearest_branches(lat_f, lng_f, radius_km=radius_f, limit=effective_limit, only_active=True)

        if not branches:
            msg = f"Không tìm thấy chi nhánh nào trong bán kính {radius_f} km." if radius_f else "Không tìm thấy chi nhánh nào đang hoạt động."
            return Response({"detail": msg}, status=status.HTTP_404_NOT_FOUND)

        if return_all:
            serializer = self.get_serializer(branches, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(branches[0])
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="tim-gan-nhat")
    def tim_gan_nhat(self, request):
        return self.nearest(request)


BranchViewSet = ChiNhanhViewSet
