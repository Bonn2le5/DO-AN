from django.conf import settings
from django.db import models
from foods.models import MoHinhThoiGian


class HoiThoai(MoHinhThoiGian):
    class TrangThai(models.TextChoices):
        MO = "mo", "Mở"
        DONG = "dong", "Đóng"

    khach_hang = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="danh_sach_hoi_thoai", on_delete=models.CASCADE
    )
    nhan_vien = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="hoi_thoai_phu_trach",
        null=True, blank=True, on_delete=models.SET_NULL
    )
    trang_thai = models.CharField(max_length=10, choices=TrangThai.choices, default=TrangThai.MO)
    tin_nhan_cuoi_luc = models.DateTimeField(null=True, blank=True)

    _LEGACY_MAP = {
        "customer": "khach_hang",
        "customer_id": "khach_hang_id",
        "staff": "nhan_vien",
        "staff_id": "nhan_vien_id",
        "status": "trang_thai",
        "last_message_at": "tin_nhan_cuoi_luc",
    }

    class Meta:
        db_table = "hoi_thoai"
        verbose_name = "Hội thoại"

    @property
    def customer(self):
        return self.khach_hang

    @customer.setter
    def customer(self, val):
        self.khach_hang = val

    @property
    def customer_id(self):
        return self.khach_hang_id

    @customer_id.setter
    def customer_id(self, val):
        self.khach_hang_id = val

    @property
    def staff(self):
        return self.nhan_vien

    @staff.setter
    def staff(self, val):
        self.nhan_vien = val

    @property
    def staff_id(self):
        return self.nhan_vien_id

    @staff_id.setter
    def staff_id(self, val):
        self.nhan_vien_id = val

    @property
    def status(self):
        return self.trang_thai

    @status.setter
    def status(self, val):
        self.trang_thai = val

    @property
    def last_message_at(self):
        return self.tin_nhan_cuoi_luc

    @last_message_at.setter
    def last_message_at(self, val):
        self.tin_nhan_cuoi_luc = val

    @property
    def messages(self):
        return self.danh_sach_tin_nhan

    @messages.setter
    def messages(self, val):
        if self.pk and hasattr(self.danh_sach_tin_nhan, "set"):
            self.danh_sach_tin_nhan.set(val)
        else:
            self._uncommitted_messages = val


class TinNhan(MoHinhThoiGian):
    class LoaiTinNhan(models.TextChoices):
        VAN_BAN = "van_ban", "Văn bản"
        HINH_ANH = "hinh_anh", "Hình ảnh"
        HE_THONG = "he_thong", "Hệ thống"

    hoi_thoai = models.ForeignKey(HoiThoai, related_name="danh_sach_tin_nhan", on_delete=models.CASCADE)
    nguoi_gui = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    loai_tin_nhan = models.CharField(
        max_length=10, choices=LoaiTinNhan.choices, default=LoaiTinNhan.VAN_BAN
    )
    noi_dung = models.TextField()
    da_doc = models.BooleanField(default=False)
    doc_luc = models.DateTimeField(null=True, blank=True)

    _LEGACY_MAP = {
        "room": "hoi_thoai",
        "room_id": "hoi_thoai_id",
        "sender": "nguoi_gui",
        "sender_id": "nguoi_gui_id",
        "message_type": "loai_tin_nhan",
        "type": "loai_tin_nhan",
        "content": "noi_dung",
        "message": "noi_dung",
        "is_read": "da_doc",
        "read_at": "doc_luc",
    }

    class Meta:
        db_table = "tin_nhan"
        verbose_name = "Tin nhắn"

    @property
    def room(self):
        return self.hoi_thoai

    @room.setter
    def room(self, val):
        self.hoi_thoai = val

    @property
    def room_id(self):
        return self.hoi_thoai_id

    @room_id.setter
    def room_id(self, val):
        self.hoi_thoai_id = val

    @property
    def sender(self):
        return self.nguoi_gui

    @sender.setter
    def sender(self, val):
        self.nguoi_gui = val

    @property
    def sender_id(self):
        return self.nguoi_gui_id

    @sender_id.setter
    def sender_id(self, val):
        self.nguoi_gui_id = val

    @property
    def content(self):
        return self.noi_dung

    @content.setter
    def content(self, val):
        self.noi_dung = val

    @property
    def message(self):
        return self.noi_dung

    @message.setter
    def message(self, val):
        self.noi_dung = val

    @property
    def message_type(self):
        return self.loai_tin_nhan

    @message_type.setter
    def message_type(self, val):
        self.loai_tin_nhan = val

    @property
    def type(self):
        return self.loai_tin_nhan

    @type.setter
    def type(self, val):
        self.loai_tin_nhan = val

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
ChatRoom = HoiThoai
ChatMessage = TinNhan
HoiThoai.Status = HoiThoai.TrangThai
TinNhan.Type = TinNhan.LoaiTinNhan
ChatRoom.Status = HoiThoai.TrangThai
ChatMessage.Type = TinNhan.LoaiTinNhan
