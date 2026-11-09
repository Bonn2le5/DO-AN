from django.conf import settings
from django.db import models
from foods.models import MoHinhThoiGian


class ThongBao(MoHinhThoiGian):
    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="danh_sach_thong_bao", on_delete=models.CASCADE
    )
    loai = models.CharField(max_length=50)
    tieu_de = models.CharField(max_length=200)
    noi_dung = models.TextField()
    loai_tham_chieu = models.CharField(max_length=30, blank=True)
    id_tham_chieu = models.BigIntegerField(null=True, blank=True)
    da_doc = models.BooleanField(default=False)
    doc_luc = models.DateTimeField(null=True, blank=True)


    class Meta:
        db_table = "thong_bao"
        verbose_name = "Thông báo"
        indexes = [models.Index(fields=["nguoi_dung", "da_doc", "-tao_luc"])]


# Backward-compatible model aliases
Notification = ThongBao


class AdminSetting(models.Model):
    key = models.CharField(max_length=40, unique=True, default="restaurant")
    value = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "admin_setting"
