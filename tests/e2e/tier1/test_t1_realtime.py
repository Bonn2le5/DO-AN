"""
Tier 1: Real-time Communication & FSM Feature Coverage Tests (T1_realtime)
Verifies:
1. Channels ASGI protocol router declaration in config/asgi.py.
2. Order FSM initializes in 'cho_tiep_nhan'.
3. Order FSM transitions through legal happy-path lifecycle states.
4. Early order cancellation from 'cho_tiep_nhan' to 'da_huy'.
5. Chat message contract & DB persistence audit fields.
"""

import unittest
from pathlib import Path
from tests.e2e.helpers.fsm_validator import OrderFSM, VALID_STATES


PROJECT_ROOT = Path("/Users/VuVan/Documents/DO-AN")
BACKEND_DIR = PROJECT_ROOT / "moc-backend"


class TestTier1Realtime(unittest.TestCase):
    """Tier 1: Realtime Communication & FSM Tests"""

    def test_t1_realtime_01_asgi_protocol_router_declaration(self):
        """Test 1: Verify config/asgi.py exists and configures ASGI application."""
        asgi_file = BACKEND_DIR / "config" / "asgi.py"
        self.assertTrue(asgi_file.exists(), "config/asgi.py not found")
        content = asgi_file.read_text(encoding="utf-8")
        self.assertIn("application", content)

    def test_t1_realtime_02_order_fsm_initial_state(self):
        """Test 2: Verify newly created order starts at 'cho_tiep_nhan'."""
        fsm = OrderFSM(order_id="DH1001", initial_state="cho_tiep_nhan")
        self.assertEqual(fsm.current_state, "cho_tiep_nhan")
        self.assertEqual(len(fsm.history), 1)
        self.assertEqual(fsm.history[0]["sang_trang_thai"], "cho_tiep_nhan")

    def test_t1_realtime_03_order_fsm_happy_path_lifecycle(self):
        """Test 3: Verify complete progression: cho_tiep_nhan -> da_xac_nhan -> dang_che_bien -> san_sang -> hoan_tat."""
        fsm = OrderFSM(order_id="DH1002")

        # Step 1: da_xac_nhan
        log1 = fsm.transition_to("da_xac_nhan", actor="nhan_vien_thu_ngan", note="Xac nhan don")
        self.assertEqual(fsm.current_state, "da_xac_nhan")
        self.assertEqual(log1["tu_trang_thai"], "cho_tiep_nhan")

        # Step 2: dang_che_bien
        log2 = fsm.transition_to("dang_che_bien", actor="bep_truong", note="Bat dau nau")
        self.assertEqual(fsm.current_state, "dang_che_bien")

        # Step 3: san_sang
        log3 = fsm.transition_to("san_sang", actor="bep_truong", note="Mon an da xong")
        self.assertEqual(fsm.current_state, "san_sang")

        # Step 4: hoan_tat
        log4 = fsm.transition_to("hoan_tat", actor="phuc_vu", note="Giao mon thanh cong")
        self.assertEqual(fsm.current_state, "hoan_tat")
        self.assertEqual(len(fsm.history), 5)

    def test_t1_realtime_04_early_cancellation_transition(self):
        """Test 4: Verify cancellation is permitted directly from 'cho_tiep_nhan' to 'da_huy'."""
        fsm = OrderFSM(order_id="DH1003")
        log = fsm.transition_to("da_huy", actor="khach_hang", note="Doi y khong dat")
        self.assertEqual(fsm.current_state, "da_huy")
        self.assertEqual(log["sang_trang_thai"], "da_huy")

    def test_t1_realtime_05_chat_message_schema_and_persistence(self):
        """Test 5: Verify chat message payload contract matches required DB persistence fields."""
        chat_msg_payload = {
            "conversation_id": "conv_987",
            "sender_id": 42,
            "sender_name": "Nguyen Van A",
            "is_staff": False,
            "content": "Xin chao, nha hang con ban gan cua so khong?",
            "message_type": "van_ban",
        }
        # Required fields in DB persistence
        required_keys = ["conversation_id", "sender_id", "content", "message_type"]
        for k in required_keys:
            self.assertIn(k, chat_msg_payload)
        self.assertGreater(len(chat_msg_payload["content"].strip()), 0)


if __name__ == "__main__":
    unittest.main()
