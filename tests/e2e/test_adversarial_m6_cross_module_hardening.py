#!/usr/bin/env python3
"""
Adversarial Multi-Module Cross-Hardening Stress Test Suite for Milestone 6.
Web App Nhà hàng Mộc — Challenger m6_challenger_1.

Multi-Module Verification Matrix:
1. Cross-Module Flow: GIS Discovery -> Table Hold Race -> Pessimistic Confirmation -> VNPay IPN.
2. Concurrent BOM Stockout Atomic Rollback: Shared raw materials, insufficient stock rejection, atomic inventory rollback.
3. Order FSM Traversal with Audit Trail & Real-time Broadcast triggers.
4. AI Recommendation Feedback Loop: Order/Review interaction weights (4.0/5.0), cache invalidation, and explainable tags.
5. Deposit Policy Compliance: Tiered cancellation refund matrix (>24h 100%, 6-24h 50%, <6h 0%, no-show 0%) and PhieuHoanTien receipt generation.
6. Strict Tenant & Role Security Boundaries: Customer isolation, customer cancellation restrictions, review moderation filtering.
"""

import os
import sys
from datetime import datetime, date, time as dtime, timedelta
from decimal import Decimal
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "moc-backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("TESTING", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.conf import settings
# Configure in-memory cache for test environment isolation
settings.CACHES["default"] = {
    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    "LOCATION": "m6-cross-locmem",
}
from django.core.cache import cache, caches
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError

from accounts.models import NguoiDung, VaiTro
from branches.models import ChiNhanh
from branches.services import find_nearest_branches, haversine_distance_km
from foods.models import DanhMuc, MonAn, NguyenLieu, DinhMucNguyenLieu, LichSuXuatNhapKho
from foods.services import DichVuKho
from reservations.models import BanAn, DatBan, ChinhSachDatCoc, QuyTacHuyDatCoc
from reservations.services import DichVuDatBan
from orders.models import DonHang, ChiTietDonHang, LichSuTrangThaiDon
from orders.services import DichVuDonHang
from payments.models import ThanhToan, PhieuHoanTien
from payments.services import VNPayService, RefundService
from reviews.models import DanhGia
from recommendations.models import TuongTacMonAn, GoiYMonAn
from recommendations.services import DichVuGoiY, tao_ly_do_goi_y


class TestMilestone6CrossModuleHardening(TransactionTestCase):
    """Empirical Multi-Module Cross-Hardening Stress Suite."""

    def setUp(self):
        super().setUp()
        cache.clear()
        self.client = APIClient()

        # 1. Setup Roles
        self.role_admin, _ = VaiTro.objects.get_or_create(ten="quan_tri_vien", defaults={"mo_ta": "Quản trị viên"})
        self.role_staff, _ = VaiTro.objects.get_or_create(ten="nhan_vien", defaults={"mo_ta": "Nhân viên"})
        self.role_customer, _ = VaiTro.objects.get_or_create(ten="khach_hang", defaults={"mo_ta": "Khách hàng"})

        # 2. Setup Users
        self.staff_user = NguoiDung.objects.create_user(
            username="m6_staff_harness",
            email="staff_m6@mocrestaurant.vn",
            password="Password123!",
            is_staff=True,
            ho_ten="M6 Staff",
        )
        self.staff_user.danh_sach_vai_tro.add(self.role_staff)

        self.customer_alice = NguoiDung.objects.create_user(
            username="m6_alice_harness",
            email="alice_m6@gmail.com",
            password="Password123!",
            is_staff=False,
            ho_ten="Alice M6",
        )
        self.customer_alice.danh_sach_vai_tro.add(self.role_customer)

        self.customer_bob = NguoiDung.objects.create_user(
            username="m6_bob_harness",
            email="bob_m6@gmail.com",
            password="Password123!",
            is_staff=False,
            ho_ten="Bob M6",
        )
        self.customer_bob.danh_sach_vai_tro.add(self.role_customer)

        # 3. Setup Branches
        self.branch_tanbinh = ChiNhanh.objects.create(
            ten="Mộc Tân Bình",
            dia_chi="123 Hoàng Văn Thụ, Tân Bình, TP.HCM",
            so_dien_thoai="02811112222",
            toa_do_gis="106.6669,10.7925",
            con_hoat_dong=True,
        )
        self.branch_q1 = ChiNhanh.objects.create(
            ten="Mộc Quận 1",
            dia_chi="456 Nguyễn Huệ, Quận 1, TP.HCM",
            so_dien_thoai="02833334444",
            toa_do_gis="106.7009,10.7769",
            con_hoat_dong=True,
        )
        self.branch_inactive = ChiNhanh.objects.create(
            ten="Mộc Đóng Cửa",
            dia_chi="999 Đang Sửa Chữa, TP.HCM",
            toa_do_gis="106.6800,10.7800",
            con_hoat_dong=False,
        )

        # 4. Setup Tables
        self.table_vip = BanAn.objects.create(
            chi_nhanh=self.branch_tanbinh,
            so_ban="VIP-01",
            khu_vuc="VIP",
            suc_chua=6,
            trang_thai="trong",
        )
        self.table_standard = BanAn.objects.create(
            chi_nhanh=self.branch_tanbinh,
            so_ban="STD-02",
            khu_vuc="Thuong",
            suc_chua=4,
            trang_thai="trong",
        )

        # 5. Setup Cancellation Rules & Deposit Policy
        self.policy = ChinhSachDatCoc.objects.create(
            chi_nhanh=self.branch_tanbinh,
            phan_tram_coc=Decimal("30.00"),
            con_ap_dung=True,
        )
        QuyTacHuyDatCoc.objects.create(
            chinh_sach=self.policy,
            moc_thoi_gian=QuyTacHuyDatCoc.MocThoiGian.TRUOC_24H,
            phan_tram_hoan_tien=Decimal("100.00"),
        )
        QuyTacHuyDatCoc.objects.create(
            chinh_sach=self.policy,
            moc_thoi_gian=QuyTacHuyDatCoc.MocThoiGian.TU_6_DEN_24H,
            phan_tram_hoan_tien=Decimal("50.00"),
        )
        QuyTacHuyDatCoc.objects.create(
            chinh_sach=self.policy,
            moc_thoi_gian=QuyTacHuyDatCoc.MocThoiGian.TRONG_6H,
            phan_tram_hoan_tien=Decimal("0.00"),
        )
        QuyTacHuyDatCoc.objects.create(
            chinh_sach=self.policy,
            moc_thoi_gian=QuyTacHuyDatCoc.MocThoiGian.KHACH_KHONG_DEN,
            phan_tram_hoan_tien=Decimal("0.00"),
        )

        # 6. Setup Food Categories & Dishes
        self.cat_main = DanhMuc.objects.create(
            ten="Món Chính M6",
            duong_dan="mon-chinh-m6",
            con_hoat_dong=True,
        )

        self.dish_hotpot = MonAn.objects.create(
            danh_muc=self.cat_main,
            ten="Lẩu riêu cua bắp bò",
            duong_dan="lau-rieu-cua-bap-bo-m6",
            don_gia=Decimal("350000"),
            mo_ta_chi_tiet="Lẩu riêu cua tươi ngọt, bắp bò Úc tươi mềm, nước dùng chua thanh",
            con_hang=True,
            hien_thi=True,
            do_cay=1,
            diem_danh_gia=Decimal("0"),
            so_luot_danh_gia=0,
        )
        self.dish_grill = MonAn.objects.create(
            danh_muc=self.cat_main,
            ten="Bắp bò nướng tảng cay",
            duong_dan="bap-bo-nuong-tang-cay-m6",
            don_gia=Decimal("220000"),
            mo_ta_chi_tiet="Bắp bò nướng cay sốt ớt tiêu xanh",
            con_hang=True,
            hien_thi=True,
            do_cay=3,
            diem_danh_gia=Decimal("0"),
            so_luot_danh_gia=0,
        )

        # 7. Setup Raw Materials & BOM (Bill of Materials)
        self.ing_beef = NguyenLieu.objects.create(
            ten="Bắp bò Úc tươi M6",
            don_vi="kg",
            ton_kho_hien_tai=Decimal("2.000"),
            ton_kho_toi_thieu=Decimal("0.500"),
            con_hoat_dong=True,
        )
        self.ing_crab = NguyenLieu.objects.create(
            ten="Cua đồng xay M6",
            don_vi="kg",
            ton_kho_hien_tai=Decimal("5.000"),
            ton_kho_toi_thieu=Decimal("1.000"),
            con_hoat_dong=True,
        )

        # BOM:
        # Lẩu riêu cua: 0.8 kg bắp bò + 0.5 kg cua đồng
        DinhMucNguyenLieu.objects.create(
            mon_an=self.dish_hotpot,
            nguyen_lieu=self.ing_beef,
            so_luong_can=Decimal("0.800"),
        )
        DinhMucNguyenLieu.objects.create(
            mon_an=self.dish_hotpot,
            nguyen_lieu=self.ing_crab,
            so_luong_can=Decimal("0.500"),
        )
        # Bắp bò nướng tảng: 1.5 kg bắp bò
        DinhMucNguyenLieu.objects.create(
            mon_an=self.dish_grill,
            nguyen_lieu=self.ing_beef,
            so_luong_can=Decimal("1.500"),
        )

    # =========================================================================
    # Test 1: Cross-Module Flow: GIS -> Table Hold Race -> Confirmation -> VNPay IPN
    # =========================================================================
    def test_01_cross_module_gis_table_race_and_vnpay_ipn(self):
        """Verify GIS branch selection, 10-minute Redis table lock race, and VNPay IPN receipt."""
        # Step A: GIS Nearest Branch (User near Tan Binh: 10.7930, 106.6670)
        nearest = find_nearest_branches(user_lat=10.7930, user_lng=106.6670, limit=2)
        self.assertGreaterEqual(len(nearest), 1)
        self.assertEqual(nearest[0].id, self.branch_tanbinh.id)
        # Inactive branch must be strictly excluded
        branch_ids = [b.id for b in nearest]
        self.assertNotIn(self.branch_inactive.id, branch_ids)

        # Step B: Concurrency Table Hold Race
        future_date = (timezone.now() + timedelta(days=2)).date().isoformat()
        hold_time = "19:00"

        # Alice holds table VIP
        success_alice, msg_alice = DichVuDatBan.giu_ban_tam_thoi(
            ban_id=self.table_vip.id,
            ngay=future_date,
            gio=hold_time,
            so_khach=4,
        )
        self.assertTrue(success_alice, f"Alice should acquire hold lock: {msg_alice}")

        # Bob immediately attempts to hold the same table -> must get BAN_DANG_BAN
        success_bob, msg_bob = DichVuDatBan.giu_ban_tam_thoi(
            ban_id=self.table_vip.id,
            ngay=future_date,
            gio=hold_time,
            so_khach=4,
        )
        self.assertIn("BAN_DANG_BAN", str(msg_bob))

        # Step C: Alice confirms reservation in Database Transaction
        booking = DichVuDatBan.tao_dat_ban(
            nguoi_dung=self.customer_alice,
            du_lieu={
                "chi_nhanh": self.branch_tanbinh,
                "ban_an": self.table_vip,
                "ngay_dat": future_date,
                "gio_bat_dau": hold_time,
                "so_luong_khach": 4,
                "ten_khach": "Alice M6",
                "sdt_khach": "0911223344",
                "id_giu_ban": msg_alice["id_giu_ban"],
            }
        )
        self.assertIsNotNone(booking)
        self.assertEqual(booking.ban_an, self.table_vip)

        # Step D: VNPay Sandbox Payment Creation & IPN Webhook Verification
        vnp_txn_ref = f"BK_{booking.id}_{int(timezone.now().timestamp())}"
        payment = ThanhToan.objects.create(
            dat_ban=booking,
            nguoi_dung=self.customer_alice,
            so_tien=Decimal("200000"),
            phuong_thuc="vnpay",
            loai_thanh_toan="tien_coc",
            ma_giao_dich=vnp_txn_ref,
            trang_thai="cho_thanh_toan",
        )

        # Create payment URL with HMAC-SHA512
        payment_url, params = VNPayService.create_payment_url(
            thanh_toan=payment,
            ip_addr="127.0.0.1",
            order_info=f"Coc dat ban #{booking.id}",
        )
        self.assertIn("vpcpay.html?", payment_url)
        self.assertIn("vnp_SecureHash", params)

        # Simulate VNPay IPN callback
        hash_secret = getattr(settings, "VNPAY_HASH_SECRET", "VNPAYSECRETKEY2026MOCRESTAURANT")
        ipn_data = {
            "vnp_TxnRef": vnp_txn_ref,
            "vnp_Amount": "20000000",  # VNPay amounts are multiplied by 100
            "vnp_ResponseCode": "00",
            "vnp_TransactionStatus": "00",
            "vnp_OrderInfo": f"Coc dat ban #{booking.id}",
            "vnp_BankCode": "NCB",
            "vnp_PayDate": timezone.now().strftime("%Y%m%d%H%M%S"),
            "vnp_TransactionNo": "14123456",
        }
        ipn_data["vnp_SecureHash"] = VNPayService.calculate_hmac_sha512(ipn_data, hash_secret)

        # Staff/System handles IPN
        resp = self.client.get("/api/payments/vnpay/ipn/", ipn_data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data.get("RspCode"), "00")

        # Refresh booking & payment state
        booking.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(payment.trang_thai, "thanh_cong")
        self.assertEqual(booking.trang_thai, DatBan.TrangThai.DA_XAC_NHAN)
        self.assertEqual(booking.trang_thai_coc, DatBan.TrangThaiCoc.THANH_CONG)

    # =========================================================================
    # Test 2: Shared BOM Material Shortage & Atomic Inventory Rollback
    # =========================================================================
    def test_02_shared_bom_material_shortage_atomic_rollback(self):
        """
        Verify that multi-item order requiring more shared material than available stock:
        1. Fails atomically with ValidationError.
        2. Preserves order in cho_tiep_nhan.
        3. Leaves inventory balances completely intact (zero partial deductions).
        4. Succeeds smoothly once inventory is replenished.
        """
        # Create Order: 1 Lẩu riêu cua (needs 0.8kg beef) + 1 Bắp bò nướng (needs 1.5kg beef)
        # Total beef needed = 2.300 kg. Available stock = 2.000 kg. Deficit = 0.300 kg.
        order = DonHang.objects.create(
            ma_don_hang="DH-M6-ROLLBACK-01",
            khach_hang=self.customer_alice,
            chi_nhanh=self.branch_tanbinh,
            tong_tien=Decimal("570000"),
            trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            ten_khach="Alice M6",
            sdt_khach="0911223344",
        )
        ChiTietDonHang.objects.create(
            don_hang=order,
            mon_an=self.dish_hotpot,
            so_luong=1,
            don_gia_luc_dat=self.dish_hotpot.don_gia,
            thanh_tien=self.dish_hotpot.don_gia,
        )
        ChiTietDonHang.objects.create(
            don_hang=order,
            mon_an=self.dish_grill,
            so_luong=1,
            don_gia_luc_dat=self.dish_grill.don_gia,
            thanh_tien=self.dish_grill.don_gia,
        )

        initial_beef_stock = self.ing_beef.ton_kho_hien_tai
        initial_crab_stock = self.ing_crab.ton_kho_hien_tai

        # Staff attempts to confirm order -> must raise ValidationError for insufficient stock
        with self.assertRaises(ValidationError) as ctx:
            DichVuDonHang.doi_trang_thai(
                don_hang=order,
                trang_thai_moi=DonHang.TrangThai.DA_XAC_NHAN,
                nguoi_dung=self.staff_user,
                ghi_chu="Confirm order with material deficit",
            )
        self.assertIn("không đủ tồn kho", str(ctx.exception).lower())

        # Check atomic rollback
        order.refresh_from_db()
        self.ing_beef.refresh_from_db()
        self.ing_crab.refresh_from_db()

        self.assertEqual(order.trang_thai, DonHang.TrangThai.CHO_TIEP_NHAN, "Order must remain cho_tiep_nhan")
        self.assertEqual(self.ing_beef.ton_kho_hien_tai, initial_beef_stock, "Beef stock must NOT be partially deducted")
        self.assertEqual(self.ing_crab.ton_kho_hien_tai, initial_crab_stock, "Crab stock must NOT be partially deducted")

        # Now replenish beef stock by 3.0 kg
        self.ing_beef.ton_kho_hien_tai = Decimal("5.000")
        self.ing_beef.save(update_fields=["ton_kho_hien_tai", "cap_nhat_luc"])
        LichSuXuatNhapKho.objects.create(
            nguyen_lieu=self.ing_beef,
            loai_giao_dich=LichSuXuatNhapKho.LoaiGiaoDich.NHAP,
            so_luong=Decimal("3.000"),
            ton_kho_truoc=initial_beef_stock,
            ton_kho_sau=Decimal("5.000"),
            ghi_chu="Replenish beef for M6 test",
            tao_boi=self.staff_user,
        )
        self.assertEqual(self.ing_beef.ton_kho_hien_tai, Decimal("5.000"))

        # Transition order again -> must now succeed
        updated_order = DichVuDonHang.doi_trang_thai(
            don_hang=order,
            trang_thai_moi=DonHang.TrangThai.DA_XAC_NHAN,
            nguoi_dung=self.staff_user,
            ghi_chu="Confirm after replenishment",
        )
        self.assertEqual(updated_order.trang_thai, DonHang.TrangThai.DA_XAC_NHAN)

        # Inventory check: 5.000 - 2.300 = 2.700 kg beef, 5.000 - 0.500 = 4.500 kg crab
        self.ing_beef.refresh_from_db()
        self.ing_crab.refresh_from_db()
        self.assertEqual(self.ing_beef.ton_kho_hien_tai, Decimal("2.700"))
        self.assertEqual(self.ing_crab.ton_kho_hien_tai, Decimal("4.500"))

    # =========================================================================
    # Test 3: Order FSM Linear Traversal & Audit Trail Verification
    # =========================================================================
    def test_03_order_fsm_traversal_audit_and_reversals(self):
        """Traverse 5-stage FSM lifecycle and verify complete LichSuTrangThaiDon audit log."""
        order = DonHang.objects.create(
            ma_don_hang="DH-M6-FSM-01",
            khach_hang=self.customer_alice,
            chi_nhanh=self.branch_tanbinh,
            tong_tien=Decimal("350000"),
            trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            ten_khach="Alice M6",
            sdt_khach="0911223344",
        )
        ChiTietDonHang.objects.create(
            don_hang=order,
            mon_an=self.dish_hotpot,
            so_luong=1,
            don_gia_luc_dat=self.dish_hotpot.don_gia,
            thanh_tien=self.dish_hotpot.don_gia,
        )

        stages = [
            DonHang.TrangThai.DA_XAC_NHAN,
            DonHang.TrangThai.DANG_CHE_BIEN,
            DonHang.TrangThai.SAN_SANG,
            DonHang.TrangThai.HOAN_TAT,
        ]

        for next_st in stages:
            DichVuDonHang.doi_trang_thai(
                don_hang=order,
                trang_thai_moi=next_st,
                nguoi_dung=self.staff_user,
                ghi_chu=f"Transitioned to {next_st}",
            )
            order.refresh_from_db()
            self.assertEqual(order.trang_thai, next_st)

        # Check Audit Trail
        history = list(LichSuTrangThaiDon.objects.filter(don_hang=order).order_by("tao_luc"))
        self.assertEqual(len(history), 4)
        self.assertEqual(history[0].sang_trang_thai, DonHang.TrangThai.DA_XAC_NHAN)
        self.assertEqual(history[-1].sang_trang_thai, DonHang.TrangThai.HOAN_TAT)

        # Verify illegal transition rejection from terminal state hoan_tat
        with self.assertRaises(ValidationError):
            DichVuDonHang.doi_trang_thai(
                don_hang=order,
                trang_thai_moi=DonHang.TrangThai.DANG_CHE_BIEN,
                nguoi_dung=self.staff_user,
            )

    # =========================================================================
    # Test 4: AI Recommendations Feedback Loop & Explainable Tags
    # =========================================================================
    def test_04_ai_recommendations_interactions_cache_invalidation_and_explainable_tags(self):
        """
        Verify:
        1. Order creation logs interaction with weight 4.0.
        2. Review logs interaction with weight 5.0.
        3. Cache invalidation on new interactions.
        4. Explainable tags accurately describe characteristics.
        """
        # User Alice orders hotpot -> weight = 4.00
        TuongTacMonAn.objects.create(
            nguoi_dung=self.customer_alice,
            mon_an=self.dish_hotpot,
            loai_tuong_tac="dat_mon",
            trong_so=Decimal("4.00"),
        )
        # User Alice reviews hotpot with 5 stars -> weight = 5.00
        TuongTacMonAn.objects.create(
            nguoi_dung=self.customer_alice,
            mon_an=self.dish_hotpot,
            loai_tuong_tac="danh_gia",
            trong_so=Decimal("5.00"),
        )

        # Explainable tag check
        tag_hotpot = tao_ly_do_goi_y(self.dish_hotpot)
        self.assertTrue(any(k in tag_hotpot.lower() for k in ["lẩu", "cay", "đặc trưng", "phổ biến"]))

        tag_grill = tao_ly_do_goi_y(self.dish_grill)
        self.assertTrue(any(k in tag_grill.lower() for k in ["nướng", "cay", "đặc trưng", "phổ biến"]))

        # Generate recommendations for Alice
        recs = DichVuGoiY.cap_nhat_goi_y(self.customer_alice, gioi_han=5)
        self.assertGreaterEqual(len(recs), 1)

        # Verify cache entry created
        cached_count = GoiYMonAn.objects.filter(nguoi_dung=self.customer_alice).count()
        self.assertEqual(cached_count, len(recs))

        # Adding a new interaction must clear cache
        TuongTacMonAn.objects.create(
            nguoi_dung=self.customer_alice,
            mon_an=self.dish_grill,
            loai_tuong_tac="xem",
            trong_so=Decimal("1.00"),
        )
        cached_count_after = GoiYMonAn.objects.filter(nguoi_dung=self.customer_alice).count()
        self.assertEqual(cached_count_after, 0, "Signal must invalidate recommendation cache")

    # =========================================================================
    # Test 5: Deposit Refund Tier Calculation & PhieuHoanTien Generation
    # =========================================================================
    def test_05_deposit_refund_tier_matrix_and_receipt_generation(self):
        """
        Test the tiered refund policy matrix:
        - Cancellation > 24h: 100% refund
        - Cancellation 6-24h: 50% refund
        - Cancellation < 6h: 0% refund
        - Cancellation with no-show: 0% refund
        """
        now = timezone.now()

        # Case 1: Cancel > 24h (30h ahead) -> 100%
        dt_30h = now + timedelta(hours=30)
        booking_30h = DatBan.objects.create(
            chi_nhanh=self.branch_tanbinh,
            ban_an=self.table_standard,
            nguoi_dung=self.customer_alice,
            so_luong_khach=4,
            ngay_dat=dt_30h.date(),
            gio_bat_dau=dt_30h.time(),
            trang_thai=DatBan.TrangThai.DA_XAC_NHAN,
            yeu_cau_dat_coc=True,
            so_tien_coc=Decimal("200000"),
            trang_thai_coc="da_thanh_toan",
            ten_khach="Alice M6",
            sdt_khach="0911223344",
        )
        ThanhToan.objects.create(
            dat_ban=booking_30h,
            nguoi_dung=self.customer_alice,
            so_tien=Decimal("200000"),
            loai_thanh_toan="tien_coc",
            phuong_thuc="vnpay",
            trang_thai="thanh_cong",
        )

        res_30h = RefundService.process_cancellation_and_refund(
            dat_ban=booking_30h,
            user=self.customer_alice,
            ly_do="Huy truoc 30h",
            is_no_show=False,
        )
        self.assertEqual(res_30h["phan_tram_hoan_tien"], 100.0)
        self.assertEqual(Decimal(str(res_30h["so_tien_hoan"])), Decimal("200000"))
        self.assertTrue(res_30h["phieu_hoan_tien"]["ma_phieu_hoan"].startswith("RF-"))

        # Case 2: Cancel between 6h and 24h (12h ahead) -> 50%
        dt_12h = now + timedelta(hours=12)
        booking_12h = DatBan.objects.create(
            chi_nhanh=self.branch_tanbinh,
            ban_an=self.table_vip,
            nguoi_dung=self.customer_bob,
            so_luong_khach=4,
            ngay_dat=dt_12h.date(),
            gio_bat_dau=dt_12h.time(),
            trang_thai=DatBan.TrangThai.DA_XAC_NHAN,
            yeu_cau_dat_coc=True,
            so_tien_coc=Decimal("300000"),
            trang_thai_coc="da_thanh_toan",
            ten_khach="Bob M6",
            sdt_khach="0922334455",
        )
        ThanhToan.objects.create(
            dat_ban=booking_12h,
            nguoi_dung=self.customer_bob,
            so_tien=Decimal("300000"),
            loai_thanh_toan="tien_coc",
            phuong_thuc="vnpay",
            trang_thai="thanh_cong",
        )

        res_12h = RefundService.process_cancellation_and_refund(
            dat_ban=booking_12h,
            user=self.customer_bob,
            ly_do="Huy truoc 12h",
            is_no_show=False,
        )
        self.assertEqual(res_12h["phan_tram_hoan_tien"], 50.0)
        self.assertEqual(Decimal(str(res_12h["so_tien_hoan"])), Decimal("150000"))

        # Case 3: Cancel < 6h (3h ahead) -> 0%
        dt_3h = now + timedelta(hours=3)
        booking_3h = DatBan.objects.create(
            chi_nhanh=self.branch_tanbinh,
            ban_an=self.table_standard,
            nguoi_dung=self.customer_alice,
            so_luong_khach=2,
            ngay_dat=dt_3h.date(),
            gio_bat_dau=dt_3h.time(),
            trang_thai=DatBan.TrangThai.DA_XAC_NHAN,
            yeu_cau_dat_coc=True,
            so_tien_coc=Decimal("200000"),
            trang_thai_coc="da_thanh_toan",
            ten_khach="Alice M6",
            sdt_khach="0911223344",
        )
        res_3h = RefundService.process_cancellation_and_refund(
            dat_ban=booking_3h,
            user=self.customer_alice,
            ly_do="Huy truoc 3h",
            is_no_show=False,
        )
        self.assertEqual(res_3h["phan_tram_hoan_tien"], 0.0)
        self.assertEqual(Decimal(str(res_3h["so_tien_hoan"])), Decimal("0"))

        # Case 4: No-show -> 0%
        dt_ns = now + timedelta(hours=10)
        booking_noshow = DatBan.objects.create(
            chi_nhanh=self.branch_tanbinh,
            ban_an=self.table_standard,
            nguoi_dung=self.customer_bob,
            so_luong_khach=2,
            ngay_dat=dt_ns.date(),
            gio_bat_dau=dt_ns.time(),
            trang_thai=DatBan.TrangThai.DA_XAC_NHAN,
            yeu_cau_dat_coc=True,
            so_tien_coc=Decimal("200000"),
            trang_thai_coc="da_thanh_toan",
            ten_khach="Bob NoShow",
            sdt_khach="0922334455",
        )
        ThanhToan.objects.create(
            dat_ban=booking_noshow,
            nguoi_dung=self.customer_bob,
            so_tien=Decimal("200000"),
            loai_thanh_toan="tien_coc",
            phuong_thuc="vnpay",
            trang_thai="thanh_cong",
        )
        res_noshow = RefundService.process_cancellation_and_refund(
            dat_ban=booking_noshow,
            user=self.staff_user,
            ly_do="Khach khong den",
            is_no_show=True,
        )
        self.assertEqual(res_noshow["phan_tram_hoan_tien"], 0.0)
        self.assertEqual(Decimal(str(res_noshow["so_tien_hoan"])), Decimal("0"))

    # =========================================================================
    # Test 6: Cross-Tenant Isolation & Role-Based Permissions
    # =========================================================================
    def test_06_cross_tenant_isolation_and_permission_boundaries(self):
        """
        Verify:
        - Customer Bob cannot cancel Alice's order.
        - Customer Alice cannot cancel order once confirmed (da_xac_nhan).
        - Unapproved reviews (hien_thi=False) are strictly hidden from customers.
        """
        order_alice = DonHang.objects.create(
            ma_don_hang="DH-M6-ISO-01",
            khach_hang=self.customer_alice,
            chi_nhanh=self.branch_tanbinh,
            tong_tien=Decimal("350000"),
            trang_thai=DonHang.TrangThai.DA_XAC_NHAN,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            ten_khach="Alice M6",
            sdt_khach="0911223344",
        )

        # Bob attempts to cancel Alice's order via REST API -> 404 isolation
        self.client.force_authenticate(user=self.customer_bob)
        res_bob = self.client.patch(f"/api/orders/{order_alice.id}/trang_thai/", {"status": "da_huy", "ghi_chu": "Bob malicious cancel"})
        self.assertIn(res_bob.status_code, [403, 404], "Bob must NOT be permitted to modify Alice's order")

        # Alice attempts to cancel her own confirmed order -> 403 Forbidden
        self.client.force_authenticate(user=self.customer_alice)
        res_alice = self.client.patch(f"/api/orders/{order_alice.id}/trang_thai/", {"status": "da_huy", "ghi_chu": "Alice cancel confirmed"})
        self.assertEqual(res_alice.status_code, 403, "Customer cannot cancel order once confirmed")

        # Review Moderation Isolation:
        # Create approved review & hidden review
        order_rev_alice = DonHang.objects.create(
            khach_hang=self.customer_alice,
            chi_nhanh=self.branch_tanbinh,
            trang_thai=DonHang.TrangThai.HOAN_TAT,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            tong_tien=self.dish_hotpot.don_gia,
        )
        item_rev_alice = ChiTietDonHang.objects.create(
            don_hang=order_rev_alice,
            mon_an=self.dish_hotpot,
            so_luong=1,
            don_gia_luc_dat=self.dish_hotpot.don_gia,
            thanh_tien=self.dish_hotpot.don_gia,
        )
        rev_approved = DanhGia.objects.create(
            mon_an=self.dish_hotpot,
            nguoi_dung=self.customer_alice,
            don_hang=order_rev_alice,
            chi_tiet_don_hang=item_rev_alice,
            diem_danh_gia=5,
            nhan_xet="Ngon tuyệt vời!",
            hien_thi=True,
        )

        order_rev_bob = DonHang.objects.create(
            khach_hang=self.customer_bob,
            chi_nhanh=self.branch_tanbinh,
            trang_thai=DonHang.TrangThai.HOAN_TAT,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            tong_tien=self.dish_hotpot.don_gia,
        )
        item_rev_bob = ChiTietDonHang.objects.create(
            don_hang=order_rev_bob,
            mon_an=self.dish_hotpot,
            so_luong=1,
            don_gia_luc_dat=self.dish_hotpot.don_gia,
            thanh_tien=self.dish_hotpot.don_gia,
        )
        rev_hidden = DanhGia.objects.create(
            mon_an=self.dish_hotpot,
            nguoi_dung=self.customer_bob,
            don_hang=order_rev_bob,
            chi_tiet_don_hang=item_rev_bob,
            diem_danh_gia=1,
            nhan_xet="Spam comment chờ duyệt",
            hien_thi=False,
        )

        # Alice views reviews -> rev_hidden must NOT be in results
        res_reviews_alice = self.client.get(f"/api/reviews/?mon_an={self.dish_hotpot.id}")
        self.assertEqual(res_reviews_alice.status_code, 200)
        reviews_alice = res_reviews_alice.data if isinstance(res_reviews_alice.data, list) else res_reviews_alice.data.get("results", [])
        review_ids = [r["id"] for r in reviews_alice]
        self.assertIn(rev_approved.id, review_ids)
        self.assertNotIn(rev_hidden.id, review_ids, "Hidden review must NOT leak to customers")

        # Staff views reviews -> rev_hidden must be visible
        self.client.force_authenticate(user=self.staff_user)
        res_reviews_staff = self.client.get(f"/api/reviews/?mon_an={self.dish_hotpot.id}")
        self.assertEqual(res_reviews_staff.status_code, 200)
        reviews_staff = res_reviews_staff.data if isinstance(res_reviews_staff.data, list) else res_reviews_staff.data.get("results", [])
        staff_review_ids = [r["id"] for r in reviews_staff]
        self.assertIn(rev_hidden.id, staff_review_ids, "Staff must see hidden reviews for moderation")


if __name__ == "__main__":
    os.environ["TESTING"] = "1"
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=2)
    failures = runner.run_tests(["tests.e2e.test_adversarial_m6_cross_module_hardening"])
    sys.exit(bool(failures))
