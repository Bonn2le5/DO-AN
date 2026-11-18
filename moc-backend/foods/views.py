import os
import re
from decimal import Decimal, InvalidOperation
import csv
import io
import ipaddress
import socket
import zipfile
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, build_opener, Request
from uuid import uuid4
from PIL import Image, UnidentifiedImageError
from django.conf import settings
from django.core.files.base import ContentFile
from openpyxl import load_workbook
from django.db import transaction
from django.db.models import Q, Count, Prefetch, ProtectedError
from django.utils.text import slugify
from rest_framework import viewsets
from rest_framework.decorators import action, parser_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from api.permissions import LaNhanVienHoacChiDoc, LaNhanVienNhaHang
from .models import DanhMuc, NguyenLieu, MonAn, HinhAnhMonAn, TheMonAn, LichSuXuatNhapKho, DinhMucNguyenLieu, TonKhoChiNhanh
from .services import DichVuKho
from .serializers import DanhMucSerializer, NguyenLieuSerializer, MonAnSerializer, TheMonAnSerializer, LichSuKhoSerializer, DinhMucNguyenLieuSerializer, TonKhoChiNhanhSerializer


def _validate_food_image(payload):
    if len(payload) > 5 * 1024 * 1024:
        raise ValueError("Ảnh không được lớn hơn 5 MB.")
    try:
        image = Image.open(io.BytesIO(payload))
        image.verify()
        extension = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}.get(image.format)
        if not extension:
            raise ValueError("Ảnh phải ở định dạng JPG, PNG hoặc WebP.")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Dữ liệu không phải ảnh JPG, PNG hoặc WebP hợp lệ.") from exc
    return payload, extension


def _load_local_image(path_str):
    clean = str(path_str).strip().lstrip("/")
    candidates = [
        os.path.join(getattr(settings, "MEDIA_ROOT", ""), clean),
        os.path.join(getattr(settings, "BASE_DIR", ""), clean),
        os.path.join(getattr(settings, "BASE_DIR", ""), "media", clean),
        os.path.join(getattr(settings, "BASE_DIR", ""), "..", "moc-frontend", "public", clean),
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate) and os.path.isfile(candidate):
            with open(candidate, "rb") as f:
                return _validate_food_image(f.read())
    return None


def _download_food_image(url):
    url_str = str(url).strip()
    # Thử nạp từ file local trước nếu không có http/https
    if not (url_str.startswith("http://") or url_str.startswith("https://")):
        local = _load_local_image(url_str)
        if local:
            return local
        raise ValueError(f"Không tìm thấy file ảnh cục bộ '{url_str}'.")

    parsed = urlparse(url_str)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("URL ảnh phải là liên kết HTTP/HTTPS hợp lệ.")

    # Luôn chặn địa chỉ nội bộ/loopback (kể cả khi DEBUG) để tránh SSRF.
    if parsed.port and parsed.port not in (80, 443):
        raise ValueError("URL ảnh dùng cổng không được hỗ trợ.")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ValueError("URL ảnh phải trỏ đến máy chủ công khai.")
    except (OSError, ValueError) as exc:
        raise ValueError("Không xác minh được máy chủ của URL ảnh.") from exc

    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    request = Request(url_str, headers={"User-Agent": "MocRestaurant-ImageImport/1.0"})
    try:
        with build_opener(NoRedirect()).open(request, timeout=8) as response:
            content_type = response.headers.get_content_type()
            if content_type not in ("image/jpeg", "image/png", "image/webp"):
                raise ValueError("URL phải trả về ảnh JPG, PNG hoặc WebP.")
            payload = response.read(5 * 1024 * 1024 + 1)
    except (URLError, HTTPError, TimeoutError, OSError) as exc:
        raise ValueError("Không tải được ảnh từ URL (kiểm tra URL có thể truy cập).") from exc
    return _validate_food_image(payload)


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


def _la_quan_tri(user):
    return bool(user.is_superuser or getattr(user, "la_quan_tri_vien", False))


def _pham_vi_chi_nhanh(request, bat_buoc_mot=False):
    """
    Chi nhánh người dùng được xem kho.
    - ?chi_nhanh=<id>: đúng chi nhánh đó (nhân viên/quản lý chỉ được chi nhánh mình).
    - Không truyền: quản trị viên xem mọi chi nhánh, còn lại xem chi nhánh được phân công.
    """
    from branches.models import ChiNhanh
    user = request.user
    rieng = getattr(user, "chi_nhanh_quan_ly_id", None)
    raw = request.query_params.get("chi_nhanh") or (request.data.get("chi_nhanh") if request.method not in ("GET", "HEAD") else None)
    if raw not in (None, ""):
        try:
            cn = int(raw)
        except (TypeError, ValueError):
            raise ValidationError({"chi_nhanh": "Chi nhánh không hợp lệ."})
        if not _la_quan_tri(user) and cn != rieng:
            raise PermissionDenied("Bạn chỉ được thao tác kho của chi nhánh được phân công.")
        if not ChiNhanh.objects.filter(id=cn).exists():
            raise ValidationError({"chi_nhanh": "Không tìm thấy chi nhánh."})
        return [cn]
    if _la_quan_tri(user):
        if bat_buoc_mot:
            raise ValidationError({"chi_nhanh": "Chọn chi nhánh cho phiếu kho."})
        return list(ChiNhanh.objects.values_list("id", flat=True))
    if not rieng:
        if bat_buoc_mot:
            raise PermissionDenied("Tài khoản chưa được gán chi nhánh.")
        return []
    return [rieng]


class NguyenLieuViewSet(viewsets.ModelViewSet):
    serializer_class = NguyenLieuSerializer
    permission_classes = [LaNhanVienHoacChiDoc]

    def get_queryset(self):
        return NguyenLieu.objects.annotate(
            so_mon_dinh_muc=Count("dinhmucnguyenlieu", distinct=True)
        ).prefetch_related(
            Prefetch("ton_kho_chi_nhanh", queryset=TonKhoChiNhanh.objects.select_related("chi_nhanh"))
        ).order_by("-con_hoat_dong", "ten")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        user = self.request.user
        if user and user.is_authenticated and getattr(user, "la_nhan_vien_nha_hang", False):
            if self.request.method in ("GET", "HEAD"):
                from branches.models import ChiNhanh
                ids = set(_pham_vi_chi_nhanh(self.request))
                ctx["chi_nhanh_ids"] = ids
                ctx["chi_nhanh_ten"] = dict(ChiNhanh.objects.filter(id__in=ids).values_list("id", "ten"))
            else:
                ctx["chi_nhanh_ids"] = None
        else:
            ctx["chi_nhanh_ids"] = set()  # khách xem danh mục, không xem tồn kho
        return ctx

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError({
                "nguyen_lieu": "Nguyên liệu đã có lịch sử kho hoặc định mức món nên không thể xoá. Hãy tắt 'Đang sử dụng'."
            })


class TonKhoChiNhanhViewSet(viewsets.ModelViewSet):
    """Tồn kho từng chi nhánh: xem, và sửa mức tồn tối thiểu của chi nhánh mình."""
    serializer_class = TonKhoChiNhanhSerializer
    permission_classes = [LaNhanVienNhaHang]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        qs = TonKhoChiNhanh.objects.select_related("nguyen_lieu", "chi_nhanh").filter(
            chi_nhanh_id__in=_pham_vi_chi_nhanh(self.request)
        )
        if self.request.query_params.get("nguyen_lieu"):
            qs = qs.filter(nguyen_lieu_id=self.request.query_params["nguyen_lieu"])
        return qs.order_by("nguyen_lieu__ten", "chi_nhanh_id")


class LichSuKhoViewSet(viewsets.ModelViewSet):
    """Lịch sử xuất nhập kho theo chi nhánh: chỉ xem và lập phiếu mới, không sửa/xoá để giữ vết."""
    serializer_class = LichSuKhoSerializer
    permission_classes = [LaNhanVienNhaHang]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = LichSuXuatNhapKho.objects.select_related("nguyen_lieu", "tao_boi", "chi_nhanh").order_by("-tao_luc", "-id")
        # Mọi thao tác đọc (danh sách và chi tiết) chỉ thấy phiếu của chi nhánh được xem.
        if self.action not in ("create", "chuyen_kho"):
            qs = qs.filter(chi_nhanh_id__in=_pham_vi_chi_nhanh(self.request))
        params = self.request.query_params
        if params.get("nguyen_lieu"):
            qs = qs.filter(nguyen_lieu_id=params["nguyen_lieu"])
        if params.get("loai_giao_dich"):
            qs = qs.filter(loai_giao_dich=params["loai_giao_dich"])
        return qs[:500] if self.action == "list" else qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        chi_nhanh_id = _pham_vi_chi_nhanh(request, bat_buoc_mot=True)[0]
        phieu = DichVuKho.lap_phieu(
            nguyen_lieu_id=serializer.validated_data["nguyen_lieu"].id,
            chi_nhanh_id=chi_nhanh_id,
            loai_giao_dich=serializer.validated_data["loai_giao_dich"],
            so_luong=serializer.validated_data["so_luong"],
            ghi_chu=serializer.validated_data.get("ghi_chu", ""),
            nguoi_dung=request.user,
        )
        return Response(self.get_serializer(phieu).data, status=201)

    @action(detail=False, methods=["post"], url_path="chuyen-kho")
    def chuyen_kho(self, request):
        """Chuyển nguyên liệu từ chi nhánh gửi (của người lập, trừ quản trị viên) sang chi nhánh nhận."""
        data = request.data
        try:
            nguyen_lieu_id = int(data.get("nguyen_lieu"))
            den = int(data.get("den_chi_nhanh"))
            tu = int(data.get("tu_chi_nhanh") or getattr(request.user, "chi_nhanh_quan_ly_id", 0) or 0)
            so_luong = Decimal(str(data.get("so_luong")))
        except (TypeError, ValueError, InvalidOperation):
            raise ValidationError({"so_luong": "Thiếu nguyên liệu, chi nhánh hoặc số lượng hợp lệ."})
        if not tu:
            raise ValidationError({"tu_chi_nhanh": "Chọn chi nhánh gửi."})
        if not _la_quan_tri(request.user) and tu != getattr(request.user, "chi_nhanh_quan_ly_id", None):
            raise PermissionDenied("Bạn chỉ được chuyển kho đi từ chi nhánh được phân công.")
        if not NguyenLieu.objects.filter(id=nguyen_lieu_id).exists():
            raise ValidationError({"nguyen_lieu": "Không tìm thấy nguyên liệu."})
        xuat, nhap = DichVuKho.chuyen_kho(
            nguyen_lieu_id=nguyen_lieu_id, tu_chi_nhanh_id=tu, den_chi_nhanh_id=den,
            so_luong=so_luong, ghi_chu=str(data.get("ghi_chu") or ""), nguoi_dung=request.user,
        )
        return Response({"xuat": self.get_serializer(xuat).data, "nhap": self.get_serializer(nhap).data}, status=201)


class DinhMucNguyenLieuViewSet(viewsets.ModelViewSet):
    """Định mức nguyên liệu cho từng món (BOM) — dùng để trừ kho khi gửi bếp."""
    serializer_class = DinhMucNguyenLieuSerializer
    permission_classes = [LaNhanVienNhaHang]

    def get_queryset(self):
        qs = DinhMucNguyenLieu.objects.select_related("mon_an", "nguyen_lieu").order_by("mon_an__ten")
        params = self.request.query_params
        if params.get("nguyen_lieu"):
            qs = qs.filter(nguyen_lieu_id=params["nguyen_lieu"])
        if params.get("mon_an"):
            qs = qs.filter(mon_an_id=params["mon_an"])
        return qs


class MonAnViewSet(viewsets.ModelViewSet):
    serializer_class = MonAnSerializer
    permission_classes = [LaNhanVienHoacChiDoc]
    lookup_field = "duong_dan"

    @action(detail=False, methods=["post"], url_path="import-file")
    @parser_classes([MultiPartParser, FormParser])
    def import_file(self, request):
        return self.nhap_file(request)

    @action(detail=False, methods=["post"], url_path="nhap-file")
    @parser_classes([MultiPartParser, FormParser])
    def nhap_file(self, request):
        upload = request.FILES.get("file")
        if not upload:
            raise ValidationError({"file": "Vui lòng chọn file CSV, Excel (.xlsx) hoặc ZIP chứa bảng và ảnh."})
        if upload.size > 30 * 1024 * 1024:
            raise ValidationError({"file": "File không được lớn hơn 30 MB."})
        filename = upload.name.lower()
        is_zip_upload = filename.endswith(".zip")
        archive_images = {}
        try:
            source = upload.read()
            if filename.endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(source)) as archive:
                    members = [
                        info for info in archive.infolist()
                        if not info.is_dir()
                        and not info.filename.startswith("__MACOSX/")
                        and not "/._" in info.filename
                        and not info.filename.rsplit("/", 1)[-1].startswith("._")
                        and info.filename.rsplit("/", 1)[-1] != ".DS_Store"
                    ]
                    if len(members) > 201 or sum(info.file_size for info in members) > 30 * 1024 * 1024:
                        raise ValidationError({"file": "ZIP được chứa tối đa 200 file và tổng dung lượng giải nén 30 MB."})
                    sheets = [info for info in members if info.filename.lower().endswith((".csv", ".xlsx"))]
                    if len(sheets) != 1:
                        raise ValidationError({"file": "ZIP phải chứa đúng một file .csv hoặc .xlsx cùng các ảnh."})
                    for info in members:
                        basename = info.filename.replace("\\", "/").rsplit("/", 1)[-1]
                        if basename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                            if basename in archive_images:
                                raise ValidationError({"file": f"ZIP có nhiều ảnh trùng tên '{basename}'."})
                            archive_images[basename] = archive.read(info)
                    sheet_info = sheets[0]
                    sheet_bytes = archive.read(sheet_info)
                    filename = sheet_info.filename.lower()
            else:
                sheet_bytes = source
            if filename.endswith(".csv"):
                content = sheet_bytes.decode("utf-8-sig")
                try:
                    dialect = csv.Sniffer().sniff(content[:2048], delimiters=",;\t")
                except csv.Error:
                    dialect = csv.excel
                rows = list(csv.DictReader(io.StringIO(content), dialect=dialect))
            elif filename.endswith(".xlsx"):
                workbook = load_workbook(io.BytesIO(sheet_bytes), read_only=True, data_only=True)
                sheet = workbook.active
                values = list(sheet.iter_rows(values_only=True))
                headers = [str(value or "").strip() for value in values[0]] if values else []
                rows = [dict(zip(headers, row)) for row in values[1:] if any(v is not None for v in row)]
            else:
                raise ValidationError({"file": "Chỉ hỗ trợ file .csv hoặc .xlsx."})
        except (UnicodeDecodeError, ValueError, OSError, zipfile.BadZipFile) as exc:
            raise ValidationError({"file": "Không đọc được file. Hãy kiểm tra định dạng và nội dung."}) from exc

        aliases = {
            "tên món": "name", "ten mon": "name", "tên": "name", "ten": "name", "name": "name",
            "danh mục": "category", "danh muc": "category", "category": "category",
            "giá": "price", "gia": "price", "price": "price",
            "mô tả": "description", "mo ta": "description", "description": "description",
            "tồn kho": "stock", "ton kho": "stock", "stock": "stock",
            "độ cay": "spicy", "do cay": "spicy", "spicy": "spicy",
            "món chay": "vegetarian", "mon chay": "vegetarian", "vegetarian": "vegetarian",
            "đang bán": "available", "dang ban": "available", "available": "available",
            "url hình ảnh": "image_url", "url hinh anh": "image_url", "image url": "image_url",
            "image_url": "image_url", "url ảnh": "image_url", "url anh": "image_url",
        }
        errors, normalized = [], []
        for row_number, raw in enumerate(rows, start=2):
            row = {aliases.get(str(key or "").strip().lower(), str(key or "").strip().lower()): value for key, value in raw.items()}
            name = str(row.get("name") or "").strip()
            category_name = str(row.get("category") or "").strip()
            try:
                if not name:
                    raise ValueError("Thiếu tên món.")
                if len(name) > 180:
                    raise ValueError("Tên món tối đa 180 ký tự.")

                if not category_name:
                    category_name = "Món chính"
                category = DanhMuc.objects.filter(Q(ten__iexact=category_name) | Q(duong_dan__iexact=category_name)).first()
                if category is None:
                    cat_slug = slugify(category_name) or "danh-muc"
                    base_cat_slug = cat_slug
                    suffix = 2
                    while DanhMuc.objects.filter(duong_dan=cat_slug).exists():
                        cat_slug = f"{base_cat_slug}-{suffix}"
                        suffix += 1
                    category = DanhMuc.objects.create(
                        ten=category_name,
                        duong_dan=cat_slug,
                        con_hoat_dong=True
                    )

                price_raw = str(row.get("price") or "").strip()
                if not price_raw:
                    raise ValueError("Thiếu giá bán.")
                price_clean = re.sub(r"[^\d.,]", "", price_raw)
                if "." in price_clean and "," in price_clean:
                    if price_clean.rfind(",") > price_clean.rfind("."):
                        price_clean = price_clean.replace(".", "").replace(",", ".")
                    else:
                        price_clean = price_clean.replace(",", "")
                elif "." in price_clean:
                    parts = price_clean.split(".")
                    if len(parts) > 1 and len(parts[-1]) == 3:
                        price_clean = price_clean.replace(".", "")
                elif "," in price_clean:
                    parts = price_clean.split(",")
                    if len(parts) > 1 and len(parts[-1]) == 3:
                        price_clean = price_clean.replace(",", "")
                    else:
                        price_clean = price_clean.replace(",", ".")
                try:
                    price = Decimal(price_clean)
                except Exception:
                    raise ValueError(f"Giá '{price_raw}' không hợp lệ.")
                if price <= 0 or price > Decimal("9999999999.99"):
                    raise ValueError("Giá phải lớn hơn 0 và hợp lệ.")

                stock_raw = row.get("stock")
                if stock_raw not in (None, "") and str(stock_raw).strip() != "":
                    try:
                        stock = int(float(str(stock_raw).strip()))
                    except (ValueError, TypeError):
                        raise ValueError(f"Tồn kho '{stock_raw}' không hợp lệ.")
                else:
                    stock = None
                if stock is not None and stock < 0:
                    raise ValueError("Tồn kho không được âm.")

                spicy_raw = row.get("spicy")
                if spicy_raw not in (None, "") and str(spicy_raw).strip() != "":
                    try:
                        spicy = int(float(str(spicy_raw).strip()))
                    except (ValueError, TypeError):
                        raise ValueError(f"Độ cay '{spicy_raw}' không hợp lệ.")
                else:
                    spicy = 0
                if spicy not in range(4):
                    raise ValueError("Độ cay chỉ nhận giá trị 0 đến 3.")

                def parse_bool(value, default):
                    if value in (None, "") or str(value).strip() == "":
                        return default
                    if isinstance(value, bool):
                        return value
                    try:
                        num_val = float(value)
                        if num_val == 1.0:
                            return True
                        if num_val == 0.0:
                            return False
                    except (ValueError, TypeError):
                        pass
                    text = str(value).strip().lower()
                    if text in ("1", "true", "yes", "có", "co", "đang bán", "dang ban", "x", "v"):
                        return True
                    if text in ("0", "false", "no", "không", "khong", "k", "ngừng bán", "ngung ban"):
                        return False
                    raise ValueError("Món chay/đang bán phải có giá trị Có hoặc Không.")

                description = str(row.get("description") or "").strip()
                food = MonAn(
                    ten=name, danh_muc=category, don_gia=price,
                    mo_ta_ngan=description, mo_ta_chi_tiet=description,
                    ton_kho_cache=stock, do_cay=spicy,
                    la_mon_chay=parse_bool(row.get("vegetarian"), False),
                    con_hang=parse_bool(row.get("available"), True),
                )
                image_url = row.get("image_url")
                if image_url:
                    image_reference = str(image_url).strip()
                    image_name = image_reference.replace("\\", "/").rsplit("/", 1)[-1]
                    if image_name in archive_images:
                        food._import_image, food._import_image_extension = _validate_food_image(archive_images[image_name])
                    elif is_zip_upload:
                        raise ValueError(f"Không tìm thấy ảnh '{image_name}' trong ZIP.")
                    else:
                        food._import_image, food._import_image_extension = _download_food_image(image_reference)
                normalized.append(food)
            except (ValueError, InvalidOperation, TypeError) as exc:
                errors.append({"row": row_number, "message": str(exc) or "Dữ liệu không hợp lệ."})
        if not rows:
            raise ValidationError({"file": "File chưa có dữ liệu món ăn."})
        seen = set()
        for idx, food in enumerate(normalized, start=2):
            key = food.ten.casefold()
            if key in seen:
                errors.append({"row": idx, "message": f"Món '{food.ten}' bị lặp trong file."})
            seen.add(key)
        if errors:
            raise ValidationError({"errors": errors, "message": "Có lỗi dữ liệu; chưa thêm món nào."})
        with transaction.atomic():
            for food in normalized:
                existing = MonAn.objects.filter(ten__iexact=food.ten).first()
                if existing:
                    existing.danh_muc = food.danh_muc
                    existing.don_gia = food.don_gia
                    existing.mo_ta_ngan = food.mo_ta_ngan
                    existing.mo_ta_chi_tiet = food.mo_ta_chi_tiet
                    existing.ton_kho_cache = food.ton_kho_cache
                    existing.do_cay = food.do_cay
                    existing.la_mon_chay = food.la_mon_chay
                    existing.con_hang = food.con_hang
                    existing.save()
                    target_food = existing
                else:
                    base_slug = slugify(food.ten)[:50] or "mon-an"
                    slug, suffix = base_slug, 2
                    while MonAn.objects.filter(duong_dan=slug).exists():
                        slug = f"{base_slug[:55]}-{suffix}"
                        suffix += 1
                    food.duong_dan = slug
                    food.save()
                    target_food = food
                if hasattr(food, "_import_image"):
                    image = target_food.hinh_anh.filter(la_anh_chinh=True).first()
                    if not image:
                        image = HinhAnhMonAn(mon_an=target_food, la_anh_chinh=True, thu_tu=0)
                    image.anh.save(f"mon-an-{target_food.pk}-{uuid4().hex[:8]}.{food._import_image_extension}", ContentFile(food._import_image), save=True)
        return Response({"created": len(normalized), "message": f"Đã nhập thành công {len(normalized)} món ăn."})

    def get_queryset(self):
        bo_loc = MonAn.objects.select_related("danh_muc").prefetch_related("hinh_anh", "nguyen_lieu", "the_mon_an")
        tham_so = self.request.query_params

        # Ẩn món không hoạt động với khách thường
        if not self.request.user.is_authenticated or not self.request.user.la_nhan_vien_nha_hang:
            bo_loc = bo_loc.filter(hien_thi=True)

        danh_muc_param = tham_so.get("danh_muc") or tham_so.get("category")
        if danh_muc_param:
            if str(danh_muc_param).isdigit():
                bo_loc = bo_loc.filter(danh_muc_id=int(danh_muc_param))
            else:
                bo_loc = bo_loc.filter(danh_muc__duong_dan=danh_muc_param)
        tu_khoa = tham_so.get("tim_kiem") or tham_so.get("search")
        if tu_khoa:
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


class TinhTrangMonViewSet(viewsets.ViewSet):
    """Báo món tạm hết / mở bán lại theo chi nhánh, có hiệu lực trong ngày.

    GET  /tinh-trang-mon/?chi_nhanh=<id>   -> {"chi_nhanh", "ngay", "mon_an": [id...]}
    POST /tinh-trang-mon/ {mon_an, het, chi_nhanh?}
    Nhân viên và quản lý chỉ thao tác chi nhánh của mình; admin phải chỉ rõ chi nhánh.
    """

    permission_classes = [LaNhanVienHoacChiDoc]

    def _branch(self, request, required=True):
        from rest_framework.exceptions import PermissionDenied, ValidationError
        from branches.models import ChiNhanh
        user = request.user
        requested = request.data.get("chi_nhanh") if request.method == "POST" else request.query_params.get("chi_nhanh")
        is_admin = user.is_authenticated and (user.is_superuser or getattr(user, "la_quan_tri_vien", False))
        is_staff = user.is_authenticated and getattr(user, "la_nhan_vien_nha_hang", False)
        own = getattr(user, "chi_nhanh_quan_ly_id", None) if is_staff else None
        if is_staff and not is_admin and not own and request.method == "POST":
            raise PermissionDenied("Tài khoản chưa được gán chi nhánh nên không báo tình trạng món được.")
        if own and not is_admin:
            if requested not in (None, "") and str(requested) != str(own):
                raise PermissionDenied("Bạn chỉ được báo tình trạng món của chi nhánh mình.")
            return own
        if requested in (None, ""):
            if required:
                raise ValidationError({"chi_nhanh": "Cần chọn chi nhánh."})
            return None
        if not str(requested).isdigit() or not ChiNhanh.objects.filter(pk=requested).exists():
            raise ValidationError({"chi_nhanh": "Chi nhánh không tồn tại."})
        return int(requested)

    def list(self, request):
        from .services import hom_nay_vn, mon_tam_het_ids
        branch_id = self._branch(request)
        return Response({"chi_nhanh": branch_id, "ngay": hom_nay_vn().isoformat(), "mon_an": sorted(mon_tam_het_ids(branch_id))})

    def create(self, request):
        from rest_framework.exceptions import ValidationError
        from .models import MonAnTamHet
        from .services import hom_nay_vn, mon_tam_het_ids
        branch_id = self._branch(request)
        mon = MonAn.objects.filter(pk=request.data.get("mon_an")).first()
        if not mon:
            raise ValidationError({"mon_an": "Không tìm thấy món."})
        het = str(request.data.get("het", True)).lower() not in ("false", "0", "")
        today = hom_nay_vn()
        if het:
            MonAnTamHet.objects.get_or_create(mon_an=mon, chi_nhanh_id=branch_id, ngay=today, defaults={"nguoi_bao": request.user})
        else:
            MonAnTamHet.objects.filter(mon_an=mon, chi_nhanh_id=branch_id, ngay=today).delete()
        return Response({"chi_nhanh": branch_id, "ngay": today.isoformat(), "mon_an": sorted(mon_tam_het_ids(branch_id))})
