from django.conf import settings
from django.db import models
from foods.models import MoHinhThoiGian, MonAn


class TuongTacMonAn(MoHinhThoiGian):
    class LoaiTuongTac(models.TextChoices):
        XEM = "xem", "Xem"
        YEU_THICH = "yeu_thich", "Yêu thích"
        THEM_GIO_HANG = "them_gio_hang", "Thêm vào giỏ"
        DAT_MON = "dat_mon", "Đặt món"
        DANH_GIA = "danh_gia", "Đánh giá"

    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="tuong_tac_mon_an", on_delete=models.CASCADE
    )
    mon_an = models.ForeignKey(MonAn, related_name="danh_sach_tuong_tac", on_delete=models.CASCADE)
    loai_tuong_tac = models.CharField(max_length=20, choices=LoaiTuongTac.choices)
    trong_so = models.DecimalField(max_digits=5, decimal_places=2, default=1)

    _LEGACY_MAP = {
        "user": "nguoi_dung",
        "user_id": "nguoi_dung_id",
        "food": "mon_an",
        "food_id": "mon_an_id",
        "interaction_type": "loai_tuong_tac",
        "type": "loai_tuong_tac",
        "weight": "trong_so",
    }

    class Meta:
        db_table = "tuong_tac_mon_an"
        indexes = [models.Index(fields=["nguoi_dung", "tao_luc"])]
        verbose_name = "Tương tác món ăn"

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
    def food(self):
        return self.mon_an

    @food.setter
    def food(self, val):
        self.mon_an = val

    @property
    def food_id(self):
        return self.mon_an_id

    @food_id.setter
    def food_id(self, val):
        self.mon_an_id = val

    @property
    def interaction_type(self):
        return self.loai_tuong_tac

    @interaction_type.setter
    def interaction_type(self, val):
        self.loai_tuong_tac = val

    @property
    def type(self):
        return self.loai_tuong_tac

    @type.setter
    def type(self, val):
        self.loai_tuong_tac = val

    @property
    def weight(self):
        return self.trong_so

    @weight.setter
    def weight(self, val):
        self.trong_so = val


class GoiYMonAn(MoHinhThoiGian):
    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="danh_sach_goi_y", on_delete=models.CASCADE
    )
    mon_an = models.ForeignKey(MonAn, on_delete=models.CASCADE)
    diem_tuong_dong = models.DecimalField(max_digits=5, decimal_places=4)  # cosine similarity
    ly_do_goi_y = models.TextField(blank=True)
    phien_ban_model = models.CharField(max_length=30, blank=True)

    _LEGACY_MAP = {
        "user": "nguoi_dung",
        "user_id": "nguoi_dung_id",
        "food": "mon_an",
        "food_id": "mon_an_id",
        "score": "diem_tuong_dong",
        "reason": "ly_do_goi_y",
        "model_version": "phien_ban_model",
    }

    class Meta:
        db_table = "goi_y_mon_an"
        unique_together = ("nguoi_dung", "mon_an", "phien_ban_model")
        verbose_name = "Gợi ý món ăn"

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
    def food(self):
        return self.mon_an

    @food.setter
    def food(self, val):
        self.mon_an = val

    @property
    def food_id(self):
        return self.mon_an_id

    @food_id.setter
    def food_id(self, val):
        self.mon_an_id = val

    @property
    def score(self):
        return self.diem_tuong_dong

    @score.setter
    def score(self, val):
        self.diem_tuong_dong = val

    @property
    def reason(self):
        return self.ly_do_goi_y

    @reason.setter
    def reason(self, val):
        self.ly_do_goi_y = val

    @property
    def model_version(self):
        return self.phien_ban_model

    @model_version.setter
    def model_version(self, val):
        self.phien_ban_model = val


# Backward-compatible model aliases
FoodInteraction = TuongTacMonAn
Recommendation = GoiYMonAn
TuongTacMonAn.Type = TuongTacMonAn.LoaiTuongTac
FoodInteraction.Type = TuongTacMonAn.LoaiTuongTac
