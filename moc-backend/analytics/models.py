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

    _LEGACY_MAP = {
        "user": "nguoi_dung",
        "user_id": "nguoi_dung_id",
        "type": "loai",
        "notification_type": "loai",
        "title": "tieu_de",
        "message": "noi_dung",
        "content": "noi_dung",
        "is_read": "da_doc",
        "read_at": "doc_luc",
    }

    class Meta:
        db_table = "thong_bao"
        verbose_name = "Thông báo"
        indexes = [models.Index(fields=["nguoi_dung", "da_doc", "-tao_luc"])]

    @property
    def user(self):
        return self.nguoi_dung

    @user.setter
    def user(self, val):
        self.nguoi_dung = val

    @property
    def user_id(self):
        return self.nguoi_dung_id

    @user_id.setter
    def user_id(self, val):
        self.nguoi_dung_id = val

    @property
    def type(self):
        return self.loai

    @type.setter
    def type(self, val):
        self.loai = val

    @property
    def title(self):
        return self.tieu_de

    @title.setter
    def title(self, val):
        self.tieu_de = val

    @property
    def message(self):
        return self.noi_dung

    @message.setter
    def message(self, val):
        self.noi_dung = val

    @property
    def content(self):
        return self.noi_dung

    @content.setter
    def content(self, val):
        self.noi_dung = val

    @property
    def is_read(self):
        return self.da_doc

    @is_read.setter
    def is_read(self, val):
        self.da_doc = bool(val)

    @property
    def read_at(self):
        return self.doc_luc

    @read_at.setter
    def read_at(self, val):
        self.doc_luc = val


# Backward-compatible model aliases
Notification = ThongBao


class AdminSetting(models.Model):
    key = models.CharField(max_length=40, unique=True, default="restaurant")
    value = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "admin_setting"
