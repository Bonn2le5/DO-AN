from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import secrets
from foods.models import LegacyKwargsMixin


class VaiTro(LegacyKwargsMixin, models.Model):
    ten = models.CharField(max_length=50, unique=True)
    mo_ta = models.TextField(blank=True)
    tao_luc = models.DateTimeField(auto_now_add=True)
    cap_nhat_luc = models.DateTimeField(auto_now=True)

    _LEGACY_MAP = {
        "name": "ten",
        "description": "mo_ta",
        "created_at": "tao_luc",
        "updated_at": "cap_nhat_luc",
    }

    class Meta:
        db_table = "vai_tro"
        verbose_name = "Vai trò"

    def __str__(self):
        return self.ten

    @property
    def name(self):
        return self.ten

    @name.setter
    def name(self, val):
        self.ten = val

    @property
    def description(self):
        return self.mo_ta

    @description.setter
    def description(self, val):
        self.mo_ta = val


class QuyenHan(LegacyKwargsMixin, models.Model):
    ten = models.CharField(max_length=100, unique=True)
    ma_quyen = models.CharField(max_length=100, unique=True)   # vd: 'don_hang.doi_trang_thai'
    mo_ta = models.TextField(blank=True)
    tao_luc = models.DateTimeField(auto_now_add=True)
    cap_nhat_luc = models.DateTimeField(auto_now=True)

    _LEGACY_MAP = {
        "name": "ten",
        "codename": "ma_quyen",
        "description": "mo_ta",
        "created_at": "tao_luc",
        "updated_at": "cap_nhat_luc",
    }

    class Meta:
        db_table = "quyen_han"
        verbose_name = "Quyền hạn"

    def __str__(self):
        return self.ma_quyen

    @property
    def name(self):
        return self.ten

    @name.setter
    def name(self, val):
        self.ten = val

    @property
    def codename(self):
        return self.ma_quyen

    @codename.setter
    def codename(self, val):
        self.ma_quyen = val

    @property
    def description(self):
        return self.mo_ta

    @description.setter
    def description(self, val):
        self.mo_ta = val


class VaiTroQuyenHan(models.Model):
    vai_tro = models.ForeignKey(VaiTro, related_name="danh_sach_quyen", on_delete=models.CASCADE)
    quyen_han = models.ForeignKey(QuyenHan, related_name="danh_sach_vai_tro", on_delete=models.CASCADE)

    class Meta:
        db_table = "vai_tro_quyen_han"
        unique_together = ("vai_tro", "quyen_han")


class NguoiDung(LegacyKwargsMixin, AbstractUser):
    thu_dien_tu = models.EmailField(unique=True)
    so_dien_thoai = models.CharField(max_length=30, blank=True)
    anh_dai_dien = models.ImageField(upload_to="anh_dai_dien/", blank=True, null=True)
    ngay_sinh = models.DateField(null=True, blank=True)
    gioi_tinh = models.CharField(
        max_length=10,
        choices=[("nam", "Nam"), ("nu", "Nữ"), ("khac", "Khác")],
        blank=True,
    )
    danh_sach_vai_tro = models.ManyToManyField(
        VaiTro, through="NguoiDungVaiTro", related_name="nguoi_dung", blank=True
    )

    USERNAME_FIELD = "thu_dien_tu"
    REQUIRED_FIELDS = ["username"]

    _LEGACY_MAP = {
        "phone": "so_dien_thoai",
        "phone_number": "so_dien_thoai",
        "avatar": "anh_dai_dien",
        "email": "thu_dien_tu",
        "birth_date": "ngay_sinh",
        "gender": "gioi_tinh",
    }

    class Meta:
        db_table = "nguoi_dung"
        verbose_name = "Người dùng"

    def clean(self):
        super().clean()
        if self.thu_dien_tu and not self.email:
            self.email = self.thu_dien_tu
        elif self.email and not self.thu_dien_tu:
            self.thu_dien_tu = self.email

    def save(self, *args, **kwargs):
        if self.thu_dien_tu and not self.email:
            self.email = self.thu_dien_tu
        elif self.email and not self.thu_dien_tu:
            self.thu_dien_tu = self.email
        elif self.thu_dien_tu and self.email and self.thu_dien_tu != self.email:
            self.email = self.thu_dien_tu
        super().save(*args, **kwargs)

    @property
    def name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.first_name or self.username

    @name.setter
    def name(self, val):
        val = (val or "").strip()
        if val:
            parts = val.split(maxsplit=1)
            self.first_name = parts[0]
            self.last_name = parts[1] if len(parts) > 1 else ""
        else:
            self.first_name = ""
            self.last_name = ""

    @property
    def ho_ten(self):
        return self.name

    @ho_ten.setter
    def ho_ten(self, val):
        self.name = val

    @property
    def phone(self):
        return self.so_dien_thoai

    @phone.setter
    def phone(self, val):
        self.so_dien_thoai = val or ""

    @property
    def avatar(self):
        return self.anh_dai_dien

    @avatar.setter
    def avatar(self, val):
        self.anh_dai_dien = val

    @property
    def ten_vai_tro(self):
        if not self.pk:
            return set()
        return set(self.danh_sach_vai_tro.values_list("ten", flat=True))

    @property
    def la_nhan_vien_nha_hang(self):
        return self.is_superuser or bool(self.ten_vai_tro & {"nhan_vien", "quan_tri_vien"})

    @property
    def la_quan_tri_vien(self):
        return self.is_superuser or "quan_tri_vien" in self.ten_vai_tro

    @property
    def is_restaurant_staff(self):
        return self.la_nhan_vien_nha_hang

    @property
    def is_restaurant_admin(self):
        return self.la_quan_tri_vien


class NguoiDungVaiTro(models.Model):
    nguoi_dung = models.ForeignKey(NguoiDung, on_delete=models.CASCADE)
    vai_tro = models.ForeignKey(VaiTro, on_delete=models.CASCADE)

    class Meta:
        db_table = "nguoi_dung_vai_tro"
        unique_together = ("nguoi_dung", "vai_tro")


# Backward-compatible model aliases
User = NguoiDung
Role = VaiTro
Permission = QuyenHan
RolePermission = VaiTroQuyenHan
UserRole = NguoiDungVaiTro


class XacThucEmail(models.Model):
    """Model lưu OTP xác thực email cho người dùng mới đăng ký."""
    nguoi_dung = models.OneToOneField(
        NguoiDung, on_delete=models.CASCADE, related_name="xac_thuc_email"
    )
    ma_xac_thuc = models.CharField(max_length=6, blank=True)
    da_xac_thuc = models.BooleanField(default=False)
    tao_luc = models.DateTimeField(auto_now_add=True)
    het_han_luc = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "xac_thuc_email"
        verbose_name = "Xác thực Email"

    def __str__(self):
        return f"XacThucEmail({self.nguoi_dung.thu_dien_tu}, verified={self.da_xac_thuc})"

    def tao_ma(self):
        """Tạo mã OTP 6 chữ số và đặt thời hạn 15 phút."""
        self.ma_xac_thuc = str(secrets.randbelow(900000) + 100000)
        self.het_han_luc = timezone.now() + timezone.timedelta(minutes=15)
        self.save()
        return self.ma_xac_thuc

    @property
    def con_hieu_luc(self):
        """Kiểm tra OTP còn hiệu lực."""
        return bool(self.het_han_luc and timezone.now() <= self.het_han_luc)
