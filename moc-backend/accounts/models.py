from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import secrets
from branches.models import ChiNhanh


class VaiTro(models.Model):
    ten = models.CharField(max_length=50, unique=True)
    mo_ta = models.TextField(blank=True)
    tao_luc = models.DateTimeField(auto_now_add=True)
    cap_nhat_luc = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = "vai_tro"
        verbose_name = "Vai trò"

    def __str__(self):
        return self.ten


class QuyenHan(models.Model):
    ten = models.CharField(max_length=100, unique=True)
    ma_quyen = models.CharField(max_length=100, unique=True)   # vd: 'don_hang.doi_trang_thai'
    mo_ta = models.TextField(blank=True)
    tao_luc = models.DateTimeField(auto_now_add=True)
    cap_nhat_luc = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = "quyen_han"
        verbose_name = "Quyền hạn"

    def __str__(self):
        return self.ma_quyen


class VaiTroQuyenHan(models.Model):
    vai_tro = models.ForeignKey(VaiTro, related_name="danh_sach_quyen", on_delete=models.CASCADE)
    quyen_han = models.ForeignKey(QuyenHan, related_name="danh_sach_vai_tro", on_delete=models.CASCADE)

    class Meta:
        db_table = "vai_tro_quyen_han"
        unique_together = ("vai_tro", "quyen_han")


class NguoiDung(AbstractUser):
    thu_dien_tu = models.EmailField(unique=True)
    so_dien_thoai = models.CharField(max_length=30, blank=True)
    anh_dai_dien = models.ImageField(upload_to="anh_dai_dien/", blank=True, null=True)
    ngay_sinh = models.DateField(null=True, blank=True)
    chi_nhanh_quan_ly = models.ForeignKey(
        ChiNhanh,
        related_name="nguoi_dung_quan_ly",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    gioi_tinh = models.CharField(
        max_length=10,
        choices=[("nam", "Nam"), ("nu", "Nữ"), ("khac", "Khác")],
        blank=True,
    )
    # Bằng chứng đồng ý Chính sách bảo vệ dữ liệu cá nhân khi đăng ký (khoản 1, 2 Điều 6 NĐ 356/2025):
    # thời điểm và phiên bản chính sách người dùng đã thấy. Tài khoản tạo trước tính năng này để trống.
    dong_y_chinh_sach_luc = models.DateTimeField(null=True, blank=True)
    phien_ban_chinh_sach = models.CharField(max_length=20, blank=True)
    danh_sach_vai_tro = models.ManyToManyField(
        VaiTro, through="NguoiDungVaiTro", related_name="nguoi_dung", blank=True
    )

    USERNAME_FIELD = "thu_dien_tu"
    REQUIRED_FIELDS = ["username"]


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
    def ho_ten(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.first_name or self.username

    @ho_ten.setter
    def ho_ten(self, val):
        val = (val or "").strip()
        parts = val.split(maxsplit=1)
        self.first_name = parts[0] if parts else ""
        self.last_name = parts[1] if len(parts) > 1 else ""


    @property
    def ten_vai_tro(self):
        if not self.pk:
            return set()
        return set(self.danh_sach_vai_tro.values_list("ten", flat=True))

    @property
    def la_nhan_vien_nha_hang(self):
        return self.is_superuser or bool(
            self.ten_vai_tro & {"nhan_vien", "nhan_vien_ban_hang", "quan_ly_chi_nhanh", "quan_tri_vien"}
        )

    @property
    def la_quan_ly_chi_nhanh(self):
        roles = self.ten_vai_tro
        # Accounts created before branch roles were split used nhan_vien for managers.
        return "quan_ly_chi_nhanh" in roles or ("nhan_vien" in roles and bool(self.chi_nhanh_quan_ly_id))

    @property
    def la_nhan_vien_chi_nhanh(self):
        roles = self.ten_vai_tro
        return "nhan_vien_ban_hang" in roles or ("nhan_vien" in roles and not self.chi_nhanh_quan_ly_id)

    @property
    def la_quan_tri_vien(self):
        return self.is_superuser or bool(self.ten_vai_tro & {"quan_tri_vien", "admin"})


class NguoiDungVaiTro(models.Model):
    nguoi_dung = models.ForeignKey(NguoiDung, on_delete=models.CASCADE)
    vai_tro = models.ForeignKey(VaiTro, on_delete=models.CASCADE)

    class Meta:
        db_table = "nguoi_dung_vai_tro"
        unique_together = ("nguoi_dung", "vai_tro")


class XacThucEmail(models.Model):
    """Model lưu OTP xác thực email cho người dùng mới đăng ký."""
    nguoi_dung = models.OneToOneField(
        NguoiDung, on_delete=models.CASCADE, related_name="xac_thuc_email"
    )
    SO_LAN_SAI_TOI_DA = 5

    ma_xac_thuc = models.CharField(max_length=6, blank=True)
    # Số lần nhập sai mã hiện tại; đủ SO_LAN_SAI_TOI_DA thì mã bị vô hiệu, phải xin mã mới.
    so_lan_sai = models.PositiveSmallIntegerField(default=0)
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
        self.so_lan_sai = 0
        self.save()
        return self.ma_xac_thuc

    @property
    def con_hieu_luc(self):
        """Kiểm tra OTP còn hiệu lực."""
        return bool(self.het_han_luc and timezone.now() <= self.het_han_luc)
