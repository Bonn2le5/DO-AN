"""
Empirical Adversarial Challenge Test Suite for Milestone 3
Web App Nhà hàng Mộc
Agent: m3_challenger_2
Target: Order FSM Matrix, Actor Authorization, Pessimistic Locking, BOM Hooks, WebSocket Security
"""

import threading
from decimal import Decimal

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import connections
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework_simplejwt.tokens import AccessToken

from api.tests_channels_helper import WebsocketCommunicator
from config.asgi import application
from orders.models import DonHang, ChiTietDonHang, LichSuTrangThaiDon
from orders.services import DichVuDonHang
from foods.models import MonAn, DanhMuc, NguyenLieu, DinhMucNguyenLieu, LichSuXuatNhapKho
from chat.models import HoiThoai, TinNhan


class FSMFullMatrixStressTest(TestCase):
    """
    Stress-tests the full 6x6 state transition matrix (36 pairs)
    plus unknown states, self-transitions, and casing variations.
    """

    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(
            username="staff_challenger",
            email="staff_c@example.com",
            thu_dien_tu="staff_c@example.com",
            password="password123",
            is_staff=True,
        )
        self.customer = User.objects.create_user(
            username="cust_challenger",
            email="cust_c@example.com",
            thu_dien_tu="cust_c@example.com",
            password="password123",
        )

    def _create_order(self, status):
        return DonHang.objects.create(
            ma_don_hang=f"CHAL-{DonHang.objects.count() + 1}",
            khach_hang=self.customer,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            trang_thai=status,
            ten_khach="Test Customer",
            sdt_khach="0912345678",
            tien_hang=Decimal("100000"),
            tong_tien=Decimal("100000"),
        )

    def test_complete_6x6_transition_matrix(self):
        """
        Exhaustively test all 36 combinations of (from_state, to_state).
        Verify exactly the 8 legal transitions succeed, and the remaining 28 raise ValidationError.
        """
        states = [
            DonHang.TrangThai.CHO_TIEP_NHAN,
            DonHang.TrangThai.DA_XAC_NHAN,
            DonHang.TrangThai.DANG_CHE_BIEN,
            DonHang.TrangThai.SAN_SANG,
            DonHang.TrangThai.HOAN_TAT,
            DonHang.TrangThai.DA_HUY,
        ]

        legal_transitions = {
            (DonHang.TrangThai.CHO_TIEP_NHAN, DonHang.TrangThai.DA_XAC_NHAN),
            (DonHang.TrangThai.CHO_TIEP_NHAN, DonHang.TrangThai.DA_HUY),
            (DonHang.TrangThai.DA_XAC_NHAN, DonHang.TrangThai.DANG_CHE_BIEN),
            (DonHang.TrangThai.DA_XAC_NHAN, DonHang.TrangThai.DA_HUY),
            (DonHang.TrangThai.DANG_CHE_BIEN, DonHang.TrangThai.SAN_SANG),
            (DonHang.TrangThai.DANG_CHE_BIEN, DonHang.TrangThai.DA_HUY),
            (DonHang.TrangThai.SAN_SANG, DonHang.TrangThai.HOAN_TAT),
            (DonHang.TrangThai.SAN_SANG, DonHang.TrangThai.DA_HUY),
        }

        tested_count = 0
        legal_count = 0
        illegal_count = 0

        for from_s in states:
            for to_s in states:
                tested_count += 1
                order = self._create_order(from_s)

                if (from_s, to_s) in legal_transitions:
                    # Should succeed
                    DichVuDonHang.doi_trang_thai(order, to_s, self.staff, f"Test {from_s}->{to_s}")
                    order.refresh_from_db()
                    self.assertEqual(order.trang_thai, to_s)
                    legal_count += 1
                else:
                    # Must raise ValidationError
                    with self.assertRaises(
                        ValidationError,
                        msg=f"Expected ValidationError for illegal transition {from_s} -> {to_s}"
                    ):
                        DichVuDonHang.doi_trang_thai(order, to_s, self.staff, f"Illegal {from_s}->{to_s}")
                    # Verify state was not mutated
                    order.refresh_from_db()
                    self.assertEqual(order.trang_thai, from_s)
                    illegal_count += 1

        self.assertEqual(tested_count, 36)
        self.assertEqual(legal_count, 8)
        self.assertEqual(illegal_count, 28)

    def test_unknown_and_malicious_states_rejected(self):
        order = self._create_order(DonHang.TrangThai.CHO_TIEP_NHAN)
        adversarial_inputs = [
            "unknown_state",
            "DROP TABLE don_hang;",
            "' OR '1'='1",
            "<script>alert(1)</script>",
            "",
            None,
            "da_hoan_thanh",
            "pending_review",
            12345,
            True,
            False,
        ]
        for bad_input in adversarial_inputs:
            with self.assertRaises(ValidationError, msg=f"Failed to reject invalid status: {bad_input}"):
                DichVuDonHang.doi_trang_thai(order, bad_input, self.staff)
            order.refresh_from_db()
            self.assertEqual(order.trang_thai, DonHang.TrangThai.CHO_TIEP_NHAN)

    def test_status_alias_casing_and_normalization(self):
        # CONFIRMED in upper case
        order = self._create_order(DonHang.TrangThai.CHO_TIEP_NHAN)
        DichVuDonHang.doi_trang_thai(order, "CONFIRMED", self.staff)
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.DA_XAC_NHAN)

        # COOKING with surrounding whitespace
        DichVuDonHang.doi_trang_thai(order, "  cooking  ", self.staff)
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.DANG_CHE_BIEN)

        # READY alias
        DichVuDonHang.doi_trang_thai(order, "ready", self.staff)
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.SAN_SANG)

        # COMPLETED alias
        DichVuDonHang.doi_trang_thai(order, "completed", self.staff)
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.HOAN_TAT)


class ActorAuthorizationStressTest(TestCase):
    """
    Adversarial testing of actor permissions:
    Customer cannot cancel once confirmed/cooking/ready.
    Customer cannot advance order.
    Foreign customer cannot touch another customer's order.
    """

    def setUp(self):
        User = get_user_model()
        self.customer = User.objects.create_user(
            username="owner_cust",
            email="owner@example.com",
            thu_dien_tu="owner@example.com",
            password="password123",
        )
        self.intruder = User.objects.create_user(
            username="intruder_cust",
            email="intruder@example.com",
            thu_dien_tu="intruder@example.com",
            password="password123",
        )
        self.staff = User.objects.create_user(
            username="staff_auth",
            email="staff_auth@example.com",
            thu_dien_tu="staff_auth@example.com",
            password="password123",
            is_staff=True,
        )

    def _create_order(self, status):
        return DonHang.objects.create(
            ma_don_hang=f"AUTH-{DonHang.objects.count() + 1}",
            khach_hang=self.customer,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            trang_thai=status,
            ten_khach="Owner Customer",
            sdt_khach="0911111111",
            tien_hang=Decimal("150000"),
            tong_tien=Decimal("150000"),
        )

    def test_customer_can_only_cancel_pending_order(self):
        # 1. Pending: customer CAN cancel
        order_pending = self._create_order(DonHang.TrangThai.CHO_TIEP_NHAN)
        DichVuDonHang.doi_trang_thai(order_pending, DonHang.TrangThai.DA_HUY, self.customer, "Customer cancels")
        order_pending.refresh_from_db()
        self.assertEqual(order_pending.trang_thai, DonHang.TrangThai.DA_HUY)

        # 2. Confirmed: customer CANNOT cancel
        order_confirmed = self._create_order(DonHang.TrangThai.DA_XAC_NHAN)
        with self.assertRaises(PermissionDenied):
            DichVuDonHang.doi_trang_thai(order_confirmed, DonHang.TrangThai.DA_HUY, self.customer)

        # 3. Cooking: customer CANNOT cancel
        order_cooking = self._create_order(DonHang.TrangThai.DANG_CHE_BIEN)
        with self.assertRaises(PermissionDenied):
            DichVuDonHang.doi_trang_thai(order_cooking, DonHang.TrangThai.DA_HUY, self.customer)

        # 4. Ready: customer CANNOT cancel
        order_ready = self._create_order(DonHang.TrangThai.SAN_SANG)
        with self.assertRaises(PermissionDenied):
            DichVuDonHang.doi_trang_thai(order_ready, DonHang.TrangThai.DA_HUY, self.customer)

    def test_customer_cannot_advance_order(self):
        order = self._create_order(DonHang.TrangThai.CHO_TIEP_NHAN)
        with self.assertRaises(PermissionDenied):
            DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_XAC_NHAN, self.customer)

    def test_intruder_cannot_touch_order(self):
        order = self._create_order(DonHang.TrangThai.CHO_TIEP_NHAN)
        with self.assertRaises(PermissionDenied):
            DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_HUY, self.intruder)

    def test_staff_can_cancel_at_any_non_terminal_state(self):
        for state in [
            DonHang.TrangThai.CHO_TIEP_NHAN,
            DonHang.TrangThai.DA_XAC_NHAN,
            DonHang.TrangThai.DANG_CHE_BIEN,
            DonHang.TrangThai.SAN_SANG,
        ]:
            order = self._create_order(state)
            DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_HUY, self.staff, "Staff cancels")
            order.refresh_from_db()
            self.assertEqual(order.trang_thai, DonHang.TrangThai.DA_HUY)


class BOMInventoryHooksStressTest(TestCase):
    """
    Empirical tests for Bill of Materials (BOM) inventory deduction & refund hooks:
    - Deduction on da_xac_nhan
    - Refund on da_huy from da_xac_nhan and dang_che_bien
    - No refund on da_huy from cho_tiep_nhan
    - Insufficient inventory blocks transition and rolls back atomically
    """

    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(
            username="staff_bom",
            email="staff_bom@example.com",
            thu_dien_tu="staff_bom@example.com",
            password="password123",
            is_staff=True,
        )
        self.customer = User.objects.create_user(
            username="cust_bom",
            email="cust_bom@example.com",
            thu_dien_tu="cust_bom@example.com",
            password="password123",
        )

        self.category = DanhMuc.objects.create(ten="Món Chính Challenger")
        self.dish = MonAn.objects.create(
            ten="Bò Bít Tết Challenger",
            danh_muc=self.category,
            don_gia=Decimal("250000"),
            quan_ly_kho=True,
        )

        self.ingredient_beef = NguyenLieu.objects.create(
            ten="Thịt Bò Úc Challenger",
            don_vi="g",
            ton_kho_hien_tai=Decimal("1000.00"),
        )
        self.ingredient_butter = NguyenLieu.objects.create(
            ten="Bơ Lạt Challenger",
            don_vi="g",
            ton_kho_hien_tai=Decimal("500.00"),
        )

        # 1 portion needs 200g Beef and 20g Butter
        DinhMucNguyenLieu.objects.create(
            mon_an=self.dish,
            nguyen_lieu=self.ingredient_beef,
            so_luong_can=Decimal("200.00"),
        )
        DinhMucNguyenLieu.objects.create(
            mon_an=self.dish,
            nguyen_lieu=self.ingredient_butter,
            so_luong_can=Decimal("20.00"),
        )

    def _create_order_with_items(self, quantity=2, status=DonHang.TrangThai.CHO_TIEP_NHAN):
        order = DonHang.objects.create(
            ma_don_hang=f"BOM-{DonHang.objects.count() + 1}",
            khach_hang=self.customer,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            trang_thai=status,
            ten_khach="Customer BOM",
            sdt_khach="0911223344",
            tien_hang=Decimal("500000"),
            tong_tien=Decimal("500000"),
        )
        ChiTietDonHang.objects.create(
            don_hang=order,
            mon_an=self.dish,
            so_luong=quantity,
            don_gia_luc_dat=Decimal("250000"),
            thanh_tien=Decimal("500000"),
        )
        return order

    def test_bom_deduction_on_da_xac_nhan(self):
        # Order for 2 portions -> needs 400g Beef, 40g Butter
        order = self._create_order_with_items(quantity=2)

        # Initially stock is intact
        self.ingredient_beef.refresh_from_db()
        self.ingredient_butter.refresh_from_db()
        self.assertEqual(self.ingredient_beef.ton_kho_hien_tai, Decimal("1000.00"))
        self.assertEqual(self.ingredient_butter.ton_kho_hien_tai, Decimal("500.00"))

        # Transition to da_xac_nhan
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_XAC_NHAN, self.staff, "Confirm BOM")

        # Verify stock deducted
        self.ingredient_beef.refresh_from_db()
        self.ingredient_butter.refresh_from_db()
        self.assertEqual(self.ingredient_beef.ton_kho_hien_tai, Decimal("600.00"))
        self.assertEqual(self.ingredient_butter.ton_kho_hien_tai, Decimal("460.00"))

        # Verify XUAT audit records
        xuat_logs = list(LichSuXuatNhapKho.objects.filter(
            loai_tham_chieu="don_hang",
            id_tham_chieu=order.id,
            loai_giao_dich=LichSuXuatNhapKho.LoaiGiaoDich.XUAT,
        ))
        self.assertEqual(len(xuat_logs), 2)

    def test_bom_refund_on_cancel_from_da_xac_nhan(self):
        order = self._create_order_with_items(quantity=2)
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_XAC_NHAN, self.staff)

        # Stock deducted
        self.ingredient_beef.refresh_from_db()
        self.assertEqual(self.ingredient_beef.ton_kho_hien_tai, Decimal("600.00"))

        # Cancel from da_xac_nhan
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_HUY, self.staff, "Staff cancels after confirm")

        # Stock refunded back to 1000.00 and 500.00
        self.ingredient_beef.refresh_from_db()
        self.ingredient_butter.refresh_from_db()
        self.assertEqual(self.ingredient_beef.ton_kho_hien_tai, Decimal("1000.00"))
        self.assertEqual(self.ingredient_butter.ton_kho_hien_tai, Decimal("500.00"))

        nhap_logs = list(LichSuXuatNhapKho.objects.filter(
            loai_tham_chieu="don_hang",
            id_tham_chieu=order.id,
            loai_giao_dich=LichSuXuatNhapKho.LoaiGiaoDich.NHAP,
        ))
        self.assertEqual(len(nhap_logs), 2)

    def test_bom_refund_on_cancel_from_dang_che_bien(self):
        order = self._create_order_with_items(quantity=2)
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_XAC_NHAN, self.staff)
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DANG_CHE_BIEN, self.staff)

        # Cancel from dang_che_bien
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_HUY, self.staff, "Cancel in kitchen")

        # Stock refunded
        self.ingredient_beef.refresh_from_db()
        self.assertEqual(self.ingredient_beef.ton_kho_hien_tai, Decimal("1000.00"))

    def test_no_bom_refund_on_cancel_from_cho_tiep_nhan(self):
        order = self._create_order_with_items(quantity=2)
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_HUY, self.customer, "Customer cancels before confirm")

        # No logs created
        logs = LichSuXuatNhapKho.objects.filter(
            loai_tham_chieu="don_hang",
            id_tham_chieu=order.id,
        )
        self.assertEqual(logs.count(), 0)

        self.ingredient_beef.refresh_from_db()
        self.assertEqual(self.ingredient_beef.ton_kho_hien_tai, Decimal("1000.00"))

    def test_insufficient_bom_inventory_blocks_transition_atomically(self):
        # Order needs 6 portions -> 1200g Beef (only 1000g in stock!)
        order = self._create_order_with_items(quantity=6)

        with self.assertRaises(ValidationError) as ctx:
            DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_XAC_NHAN, self.staff)

        self.assertIn("kho", ctx.exception.detail)

        # Verify order rolled back to cho_tiep_nhan
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.CHO_TIEP_NHAN)

        # Verify stock completely uncorrupted
        self.ingredient_beef.refresh_from_db()
        self.ingredient_butter.refresh_from_db()
        self.assertEqual(self.ingredient_beef.ton_kho_hien_tai, Decimal("1000.00"))
        self.assertEqual(self.ingredient_butter.ton_kho_hien_tai, Decimal("500.00"))


class ConcurrencyPessimisticLockStressTest(TransactionTestCase):
    """
    Multi-threaded concurrency stress test:
    Two threads simultaneously attempt to mutate the same order.
    Verify:
    1. select_for_update prevents race conditions.
    2. Exactly one thread succeeds.
    3. The other fails with ValidationError.
    4. BOM deduction is idempotent / executed exactly once.
    """

    def setUp(self):
        User = get_user_model()
        self.staff1 = User.objects.create_user(
            username="staff_thread1",
            email="staff1@example.com",
            thu_dien_tu="staff1@example.com",
            password="password123",
            is_staff=True,
        )
        self.staff2 = User.objects.create_user(
            username="staff_thread2",
            email="staff2@example.com",
            thu_dien_tu="staff2@example.com",
            password="password123",
            is_staff=True,
        )
        self.customer = User.objects.create_user(
            username="cust_race",
            email="cust_race@example.com",
            thu_dien_tu="cust_race@example.com",
            password="password123",
        )

        self.category = DanhMuc.objects.create(ten="Món Race Category")
        self.dish = MonAn.objects.create(
            ten="Gà Nướng Race",
            danh_muc=self.category,
            don_gia=Decimal("150000"),
            quan_ly_kho=True,
        )
        self.ingredient = NguyenLieu.objects.create(
            ten="Thịt Gà Race",
            don_vi="con",
            ton_kho_hien_tai=Decimal("10.00"),
        )
        DinhMucNguyenLieu.objects.create(
            mon_an=self.dish,
            nguyen_lieu=self.ingredient,
            so_luong_can=Decimal("1.00"),
        )

    def _create_order(self):
        order = DonHang.objects.create(
            ma_don_hang="RACE-001",
            khach_hang=self.customer,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
            ten_khach="Race Customer",
            sdt_khach="0933333333",
            tien_hang=Decimal("150000"),
            tong_tien=Decimal("150000"),
        )
        ChiTietDonHang.objects.create(
            don_hang=order,
            mon_an=self.dish,
            so_luong=1,
            don_gia_luc_dat=Decimal("150000"),
            thanh_tien=Decimal("150000"),
        )
        return order

    def test_concurrent_confirmations_race(self):
        """
        Thread 1 and Thread 2 race to confirm the same order (cho_tiep_nhan -> da_xac_nhan).
        Exactly 1 must succeed; the other must fail (e.g. ValidationError self-transition).
        BOM deduction must happen exactly once.
        """
        order = self._create_order()
        results = []
        errors = []

        def worker_confirm(staff_user, delay=0.0):
            import time
            if delay:
                time.sleep(delay)
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    connections.close_all()
                    ord_obj = DonHang.objects.get(id=order.id)
                    res = DichVuDonHang.doi_trang_thai(
                        ord_obj,
                        DonHang.TrangThai.DA_XAC_NHAN,
                        staff_user,
                        f"Confirm by {staff_user.username}",
                    )
                    results.append((staff_user.username, "success"))
                    break
                except ValidationError as ve:
                    errors.append((staff_user.username, "ValidationError", str(ve)))
                    break
                except Exception as e:
                    if "locked" in str(e).lower() and attempt < max_retries - 1:
                        time.sleep(0.05)
                        continue
                    errors.append((staff_user.username, type(e).__name__, str(e)))
                    break
                finally:
                    connections.close_all()

        t1 = threading.Thread(target=worker_confirm, args=(self.staff1, 0.0))
        t2 = threading.Thread(target=worker_confirm, args=(self.staff2, 0.01))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Check that exactly 1 succeeded and 1 failed
        self.assertEqual(len(results), 1, f"Expected exactly 1 success, got: {results}, errors: {errors}")
        self.assertEqual(len(errors), 1, f"Expected exactly 1 error, got: {errors}")

        # Check final state
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.DA_XAC_NHAN)

        # Check inventory deducted EXACTLY once (10.00 - 1.00 = 9.00)
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.ton_kho_hien_tai, Decimal("9.00"))

        # Exactly 1 XUAT log
        xuat_logs = LichSuXuatNhapKho.objects.filter(
            loai_tham_chieu="don_hang",
            id_tham_chieu=order.id,
            loai_giao_dich=LichSuXuatNhapKho.LoaiGiaoDich.XUAT,
        )
        self.assertEqual(xuat_logs.count(), 1)


class WebSocketAdversarialStressTest(TransactionTestCase):
    """
    Adversarial tests on WebSocket authentication and payload edge cases.
    """

    def setUp(self):
        User = get_user_model()
        self.customer = User.objects.create_user(
            username="ws_c_user",
            email="ws_c@example.com",
            thu_dien_tu="ws_c@example.com",
            password="password123",
        )
        self.hoi_thoai = HoiThoai.objects.create(khach_hang=self.customer)

    async def test_websocket_invalid_jwt_token_rejected(self):
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/{self.hoi_thoai.id}/?token=invalid.jwt.token"
        )
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4401)

    async def test_websocket_chat_message_over_5000_chars_rejected(self):
        token = str(AccessToken.for_user(self.customer))
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/{self.hoi_thoai.id}/?token={token}"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        _ = await communicator.receive_json_from()  # welcome

        # Send 5001 characters
        long_message = "A" * 5001
        await communicator.send_json_to({"action": "send_message", "message": long_message})

        err_response = await communicator.receive_json_from()
        self.assertEqual(err_response["type"], "error")
        self.assertEqual(err_response["code"], "MESSAGE_TOO_LONG")

        await communicator.disconnect()

        from channels.db import database_sync_to_async

        @database_sync_to_async
        def get_count():
            return TinNhan.objects.filter(hoi_thoai=self.hoi_thoai).count()

        count = await get_count()
        self.assertEqual(count, 0)


class OrderRestApiFsmStressTest(TestCase):
    """
    Integration tests testing REST API actions:
    /api/orders/<id>/trang_thai/
    /api/orders/<id>/chuyen_trang_thai/
    /api/orders/<id>/status/
    """

    def setUp(self):
        from rest_framework.test import APIClient
        User = get_user_model()
        self.customer_a = User.objects.create_user(
            username="cust_api_a",
            email="cust_a@example.com",
            thu_dien_tu="cust_a@example.com",
            password="password123",
        )
        self.customer_b = User.objects.create_user(
            username="cust_api_b",
            email="cust_b@example.com",
            thu_dien_tu="cust_b@example.com",
            password="password123",
        )
        self.staff = User.objects.create_user(
            username="staff_api",
            email="staff_api@example.com",
            thu_dien_tu="staff_api@example.com",
            password="password123",
            is_staff=True,
        )
        self.order_a = DonHang.objects.create(
            ma_don_hang="API-ORD-01",
            khach_hang=self.customer_a,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
            ten_khach="Customer A",
            sdt_khach="0911223344",
            tien_hang=Decimal("100000"),
            tong_tien=Decimal("100000"),
        )
        self.client = APIClient()

    def test_anonymous_request_rejected(self):
        res = self.client.patch(f"/api/orders/{self.order_a.id}/trang_thai/", {"status": "da_huy"})
        self.assertEqual(res.status_code, 401)

    def test_foreign_customer_cannot_see_or_modify_order(self):
        self.client.force_authenticate(user=self.customer_b)
        res = self.client.patch(f"/api/orders/{self.order_a.id}/trang_thai/", {"status": "da_huy"})
        self.assertEqual(res.status_code, 404)

    def test_owner_customer_can_cancel_pending_order(self):
        self.client.force_authenticate(user=self.customer_a)
        res = self.client.patch(f"/api/orders/{self.order_a.id}/trang_thai/", {"status": "da_huy", "note": "Hủy đơn"})
        self.assertEqual(res.status_code, 200)
        self.order_a.refresh_from_db()
        self.assertEqual(self.order_a.trang_thai, DonHang.TrangThai.DA_HUY)

    def test_owner_customer_cannot_confirm_order(self):
        self.client.force_authenticate(user=self.customer_a)
        res = self.client.patch(f"/api/orders/{self.order_a.id}/trang_thai/", {"status": "da_xac_nhan"})
        self.assertEqual(res.status_code, 403)

    def test_staff_can_advance_order_and_use_aliases(self):
        self.client.force_authenticate(user=self.staff)
        res = self.client.patch(f"/api/orders/{self.order_a.id}/chuyen_trang_thai/", {"to_status": "da_xac_nhan"})
        self.assertEqual(res.status_code, 200)
        self.order_a.refresh_from_db()
        self.assertEqual(self.order_a.trang_thai, DonHang.TrangThai.DA_XAC_NHAN)

        res2 = self.client.patch(f"/api/orders/{self.order_a.id}/status/", {"status": "dang_che_bien"})
        self.assertEqual(res2.status_code, 200)
        self.order_a.refresh_from_db()
        self.assertEqual(self.order_a.trang_thai, DonHang.TrangThai.DANG_CHE_BIEN)

