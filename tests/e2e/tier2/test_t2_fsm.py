"""
Tier 2: Order FSM Invalid Transitions & Security Boundary Tests (T2_fsm)
Verifies:
1. Backward transition attempt ('san_sang' -> 'cho_tiep_nhan') is strictly blocked.
2. Skipping mandatory lifecycle steps ('cho_tiep_nhan' -> 'san_sang') is blocked.
3. Completed order in terminal state ('hoan_tat') cannot be reopened or mutated.
4. Cancelled order in terminal state ('da_huy') cannot be re-activated.
5. Unknown/malformed status string raises validation error immediately.
"""

import unittest
from tests.e2e.helpers.fsm_validator import OrderFSM, FSMTransitionError


class TestTier2FSM(unittest.TestCase):
    """Tier 2: Order Lifecycle FSM Boundary Tests"""

    def test_t2_fsm_01_reverse_transition_blocked(self):
        """Test 1: Transitioning backwards from 'san_sang' to 'cho_tiep_nhan' raises FSMTransitionError."""
        fsm = OrderFSM(order_id="DH_REV_01")
        fsm.transition_to("da_xac_nhan")
        fsm.transition_to("dang_che_bien")
        fsm.transition_to("san_sang")

        with self.assertRaises(FSMTransitionError):
            fsm.transition_to("cho_tiep_nhan")

        # Verify state remained 'san_sang'
        self.assertEqual(fsm.current_state, "san_sang")

    def test_t2_fsm_02_illegal_skip_blocked(self):
        """Test 2: Skipping directly from 'cho_tiep_nhan' to 'san_sang' without kitchen cooking is blocked."""
        fsm = OrderFSM(order_id="DH_SKIP_01")

        with self.assertRaises(FSMTransitionError):
            fsm.transition_to("san_sang")

        self.assertEqual(fsm.current_state, "cho_tiep_nhan")

    def test_t2_fsm_03_terminal_hoan_tat_immutability(self):
        """Test 3: Terminal state 'hoan_tat' rejects all subsequent transition attempts."""
        fsm = OrderFSM(order_id="DH_TERM_01")
        fsm.transition_to("da_xac_nhan")
        fsm.transition_to("dang_che_bien")
        fsm.transition_to("san_sang")
        fsm.transition_to("hoan_tat")

        # Try to cancel completed order
        with self.assertRaises(FSMTransitionError):
            fsm.transition_to("da_huy")

        # Try to set back to preparing
        with self.assertRaises(FSMTransitionError):
            fsm.transition_to("dang_che_bien")

        self.assertEqual(fsm.current_state, "hoan_tat")

    def test_t2_fsm_04_terminal_da_huy_immutability(self):
        """Test 4: Terminal state 'da_huy' rejects re-activation attempts."""
        fsm = OrderFSM(order_id="DH_TERM_02")
        fsm.transition_to("da_huy")

        with self.assertRaises(FSMTransitionError):
            fsm.transition_to("da_xac_nhan")

        self.assertEqual(fsm.current_state, "da_huy")

    def test_t2_fsm_05_unknown_state_name_rejected(self):
        """Test 5: An unapproved state name is rejected immediately."""
        fsm = OrderFSM(order_id="DH_UNK_01")

        with self.assertRaises(FSMTransitionError):
            fsm.transition_to("dang_giao_hang")  # Not in 6 valid FSM states

        self.assertEqual(fsm.current_state, "cho_tiep_nhan")


if __name__ == "__main__":
    unittest.main()
