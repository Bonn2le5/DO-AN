"""
Comprehensive Unit & Integration Test Suite for Order FSM Lifecycle & WebSockets.
"""

from decimal import Decimal
from django.test import TransactionTestCase, TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework_simplejwt.tokens import AccessToken
from api.tests_channels_helper import WebsocketCommunicator
from config.asgi import application
from orders.models import DonHang, LichSuTrangThaiDon
from orders.services import DichVuDonHang


class OrderFSMTransitionTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.customer = User.objects.create_user(
            username="khach_fsm",
            email="khach_fsm@example.com",
            thu_dien_tu="khach_fsm@example.com",
            password="password123",
            first_name="Khách",
            last_name="FSM",
        )
        self.other_customer = User.objects.create_user(
            username="khach_khac_fsm",
            email="khach_khac_fsm@example.com",
            thu_dien_tu="khach_khac_fsm@example.com",
            password="password123",
        )
        self.staff = User.objects.create_user(
            username="nhan_vien_fsm",
            email="nv_fsm@example.com",
            thu_dien_tu="nv_fsm@example.com",
            password="password123",
            is_staff=True,
            first_name="Nhân",
            last_name="Viên",
        )

    def _create_order(self, initial_status=DonHang.TrangThai.CHO_TIEP_NHAN):
        return DonHang.objects.create(
            ma_don_hang=f"DH-TEST-{DonHang.objects.count() + 1}",
            khach_hang=self.customer,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            trang_thai=initial_status,
            ten_khach="Khách Hàng",
            sdt_khach="0901234567",
            tien_hang=Decimal("200000"),
            tong_tien=Decimal("200000"),
        )

    def test_order_fsm_valid_happy_path_lifecycle(self):
        """cho_tiep_nhan -> da_xac_nhan -> dang_che_bien -> san_sang -> hoan_tat"""
        order = self._create_order()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.CHO_TIEP_NHAN)

        # 1. da_xac_nhan
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_XAC_NHAN, self.staff, "Xác nhận đơn")
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.DA_XAC_NHAN)

        # 2. dang_che_bien
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DANG_CHE_BIEN, self.staff, "Bếp bắt đầu nấu")
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.DANG_CHE_BIEN)

        # 3. san_sang
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.SAN_SANG, self.staff, "Món đã xong")
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.SAN_SANG)

        # 4. hoan_tat
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.HOAN_TAT, self.staff, "Đã giao cho khách")
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.HOAN_TAT)

        # Verify audit history
        history = list(order.lich_su_trang_thai.order_by("tao_luc"))
        self.assertEqual(len(history), 4)
        self.assertEqual(history[0].tu_trang_thai, DonHang.TrangThai.CHO_TIEP_NHAN)
        self.assertEqual(history[0].sang_trang_thai, DonHang.TrangThai.DA_XAC_NHAN)
        self.assertEqual(history[3].tu_trang_thai, DonHang.TrangThai.SAN_SANG)
        self.assertEqual(history[3].sang_trang_thai, DonHang.TrangThai.HOAN_TAT)

    def test_order_fsm_valid_cancellations(self):
        """Legal cancellations from any non-terminal state to da_huy."""
        for state in [
            DonHang.TrangThai.CHO_TIEP_NHAN,
            DonHang.TrangThai.DA_XAC_NHAN,
            DonHang.TrangThai.DANG_CHE_BIEN,
            DonHang.TrangThai.SAN_SANG,
        ]:
            order = self._create_order(initial_status=state)
            DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_HUY, self.staff, "Hủy đơn hợp lệ")
            order.refresh_from_db()
            self.assertEqual(order.trang_thai, DonHang.TrangThai.DA_HUY)

    def test_order_fsm_illegal_reverse_and_skip_transitions(self):
        order = self._create_order()

        # Illegal skip: cho_tiep_nhan -> dang_che_bien
        with self.assertRaises(ValidationError):
            DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DANG_CHE_BIEN, self.staff)

        # Illegal skip: cho_tiep_nhan -> san_sang
        with self.assertRaises(ValidationError):
            DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.SAN_SANG, self.staff)

        # Advance to san_sang
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_XAC_NHAN, self.staff)
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DANG_CHE_BIEN, self.staff)
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.SAN_SANG, self.staff)

        # Illegal reverse: san_sang -> cho_tiep_nhan
        with self.assertRaises(ValidationError):
            DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.CHO_TIEP_NHAN, self.staff)

    def test_order_fsm_terminal_state_immutability(self):
        # 1. Terminal state hoan_tat cannot be mutated
        order_completed = self._create_order(initial_status=DonHang.TrangThai.HOAN_TAT)
        with self.assertRaises(ValidationError):
            DichVuDonHang.doi_trang_thai(order_completed, DonHang.TrangThai.DA_HUY, self.staff)
        with self.assertRaises(ValidationError):
            DichVuDonHang.doi_trang_thai(order_completed, DonHang.TrangThai.DANG_CHE_BIEN, self.staff)

        # 2. Terminal state da_huy cannot be mutated
        order_cancelled = self._create_order(initial_status=DonHang.TrangThai.DA_HUY)
        with self.assertRaises(ValidationError):
            DichVuDonHang.doi_trang_thai(order_cancelled, DonHang.TrangThai.DA_XAC_NHAN, self.staff)

    def test_order_fsm_self_transition_rejected(self):
        order = self._create_order(initial_status=DonHang.TrangThai.DA_XAC_NHAN)
        with self.assertRaises(ValidationError):
            DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_XAC_NHAN, self.staff)

    def test_order_customer_cancellation_permissions(self):
        # Customer can cancel their own pending order
        order = self._create_order(initial_status=DonHang.TrangThai.CHO_TIEP_NHAN)
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_HUY, self.customer, "Khách đổi ý")
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.DA_HUY)

        # Customer CANNOT cancel confirmed order
        order2 = self._create_order(initial_status=DonHang.TrangThai.DA_XAC_NHAN)
        with self.assertRaises(PermissionDenied):
            DichVuDonHang.doi_trang_thai(order2, DonHang.TrangThai.DA_HUY, self.customer)

        # Customer CANNOT advance order to dang_che_bien
        order3 = self._create_order(initial_status=DonHang.TrangThai.DA_XAC_NHAN)
        with self.assertRaises(PermissionDenied):
            DichVuDonHang.doi_trang_thai(order3, DonHang.TrangThai.DANG_CHE_BIEN, self.customer)

        # Customer cannot cancel another customer's order
        order4 = self._create_order(initial_status=DonHang.TrangThai.CHO_TIEP_NHAN)
        with self.assertRaises(PermissionDenied):
            DichVuDonHang.doi_trang_thai(order4, DonHang.TrangThai.DA_HUY, self.other_customer)

    def test_order_unknown_state_rejected(self):
        order = self._create_order()
        with self.assertRaises(ValidationError):
            DichVuDonHang.doi_trang_thai(order, "dang_giao_hang", self.staff)


class OrderWebSocketTestCase(TransactionTestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="khach_order_ws",
            email="order_ws@example.com",
            thu_dien_tu="order_ws@example.com",
            password="password123",
            first_name="Khách",
            last_name="Hàng",
        )
        self.other_user = User.objects.create_user(
            username="khach_khac_ws",
            email="khach_khac_ws@example.com",
            thu_dien_tu="khach_khac_ws@example.com",
            password="password123",
        )
        self.staff_user = User.objects.create_user(
            username="nhan_vien_ws",
            email="nv_ws@example.com",
            thu_dien_tu="nv_ws@example.com",
            password="password123",
            is_staff=True,
            first_name="Nhân",
            last_name="Viên",
        )
        self.don_hang = DonHang.objects.create(
            ma_don_hang="DH-TEST-WS-01",
            khach_hang=self.user,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
            ten_khach="Khách Hàng",
            sdt_khach="0901234567",
            tien_hang=Decimal("150000"),
            tong_tien=Decimal("150000"),
        )

    async def test_order_tracking_anonymous_rejected(self):
        communicator = WebsocketCommunicator(
            application, f"/ws/orders/{self.don_hang.id}/"
        )
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4401)

    async def test_order_tracking_forbidden_customer_rejected(self):
        token = str(AccessToken.for_user(self.other_user))
        communicator = WebsocketCommunicator(
            application, f"/ws/orders/{self.don_hang.id}/?token={token}"
        )
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4403)

    async def test_order_snapshot_and_realtime_fsm_update(self):
        token = str(AccessToken.for_user(self.user))
        communicator = WebsocketCommunicator(
            application, f"/ws/orders/{self.don_hang.id}/?token={token}"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # 1. Verify snapshot received upon connection
        snapshot = await communicator.receive_json_from()
        self.assertEqual(snapshot["type"], "order_snapshot")
        self.assertEqual(snapshot["order_id"], self.don_hang.id)
        self.assertEqual(snapshot["status"], DonHang.TrangThai.CHO_TIEP_NHAN)

        # 2. Trigger FSM transition by staff
        await self._advance_order_status(DonHang.TrangThai.DA_XAC_NHAN)

        # 3. Receive realtime status update via WebSocket
        update = await communicator.receive_json_from()
        self.assertEqual(update["type"], "order_status_update")
        self.assertEqual(update["order_id"], self.don_hang.id)
        self.assertEqual(update["from_status"], DonHang.TrangThai.CHO_TIEP_NHAN)
        self.assertEqual(update["to_status"], DonHang.TrangThai.DA_XAC_NHAN)
        self.assertEqual(update["status"], DonHang.TrangThai.DA_XAC_NHAN)

        await communicator.disconnect()

    async def test_order_tracking_by_ma_don_hang(self):
        token = str(AccessToken.for_user(self.user))
        communicator = WebsocketCommunicator(
            application, f"/ws/orders/{self.don_hang.ma_don_hang}/?token={token}"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        snapshot = await communicator.receive_json_from()
        self.assertEqual(snapshot["type"], "order_snapshot")
        self.assertEqual(snapshot["order_number"], self.don_hang.ma_don_hang)
        await communicator.disconnect()

    async def test_staff_order_stream(self):
        # 1. Non-staff is rejected with 4403
        token_customer = str(AccessToken.for_user(self.user))
        comm_cust = WebsocketCommunicator(application, f"/ws/orders/staff/?token={token_customer}")
        c_ok, c_code = await comm_cust.connect()
        self.assertFalse(c_ok)
        self.assertEqual(c_code, 4403)

        # 2. Staff connects successfully
        token_staff = str(AccessToken.for_user(self.staff_user))
        comm_staff = WebsocketCommunicator(application, f"/ws/orders/staff/?token={token_staff}")
        s_ok, _ = await comm_staff.connect()
        self.assertTrue(s_ok)

        conn_frame = await comm_staff.receive_json_from()
        self.assertEqual(conn_frame["type"], "staff_connected")

        # 3. When an order transitions, staff stream receives the update
        await self._advance_order_status(DonHang.TrangThai.DA_XAC_NHAN)
        staff_update = await comm_staff.receive_json_from()
        self.assertEqual(staff_update["type"], "order_status_update")
        self.assertEqual(staff_update["order_id"], self.don_hang.id)
        self.assertEqual(staff_update["to_status"], DonHang.TrangThai.DA_XAC_NHAN)

        await comm_staff.disconnect()

    async def _advance_order_status(self, new_status):
        from channels.db import database_sync_to_async

        @database_sync_to_async
        def advance():
            order = DonHang.objects.get(id=self.don_hang.id)
            return DichVuDonHang.doi_trang_thai(
                don_hang=order,
                trang_thai_moi=new_status,
                nguoi_dung=self.staff_user,
                ghi_chu="Xác nhận tự động qua test",
            )

        return await advance()
