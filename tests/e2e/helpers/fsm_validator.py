"""
Order Lifecycle Finite State Machine (FSM) Validator.
Enforces the 6-state finite transition rules specified in moc_schema_tieng_viet.sql
(lines 15, 421-431) and Master Thesis Section 3.1.
"""

from typing import Set, Dict, List, Optional
from datetime import datetime


VALID_STATES: Set[str] = {
    "cho_tiep_nhan",
    "da_xac_nhan",
    "dang_che_bien",
    "san_sang",
    "hoan_tat",
    "da_huy",
}

TERMINAL_STATES: Set[str] = {
    "hoan_tat",
    "da_huy",
}

# Mapping of current_state -> set of legally permissible next states
ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    "cho_tiep_nhan": {"da_xac_nhan", "da_huy"},
    "da_xac_nhan": {"dang_che_bien", "da_huy"},
    "dang_che_bien": {"san_sang", "da_huy"},
    "san_sang": {"hoan_tat", "da_huy"},
    "hoan_tat": set(),  # Terminal state: No transitions allowed
    "da_huy": set(),    # Terminal state: No transitions allowed
}


class FSMTransitionError(Exception):
    """Raised when an illegal FSM transition is attempted."""
    pass


class OrderFSM:
    """
    Finite State Machine for managing and verifying Order Lifecycle transitions.
    """

    def __init__(self, order_id: str, initial_state: str = "cho_tiep_nhan"):
        if initial_state not in VALID_STATES:
            raise ValueError(f"Invalid initial order state: {initial_state}")
        self.order_id = order_id
        self.current_state = initial_state
        self.history: List[Dict[str, str]] = [
            {
                "tu_trang_thai": "",
                "sang_trang_thai": initial_state,
                "doi_boi": "system",
                "ghi_chu": "Khoi tao don hang",
                "tao_luc": datetime.now().isoformat(),
            }
        ]

    def can_transition_to(self, target_state: str) -> bool:
        """Check if transition to target_state is permitted."""
        if target_state not in VALID_STATES:
            return False
        return target_state in ALLOWED_TRANSITIONS.get(self.current_state, set())

    def transition_to(
        self,
        target_state: str,
        actor: str = "staff",
        note: str = ""
    ) -> Dict[str, str]:
        """
        Execute state transition. Raises FSMTransitionError if invalid.
        Returns the created audit log entry.
        """
        if self.current_state in TERMINAL_STATES:
            raise FSMTransitionError(
                f"Cannot transition from terminal state '{self.current_state}'. Order {self.order_id} is concluded."
            )

        if not self.can_transition_to(target_state):
            raise FSMTransitionError(
                f"Illegal state transition from '{self.current_state}' to '{target_state}' for order {self.order_id}."
            )

        previous_state = self.current_state
        self.current_state = target_state

        log_entry = {
            "tu_trang_thai": previous_state,
            "sang_trang_thai": target_state,
            "doi_boi": actor,
            "ghi_chu": note,
            "tao_luc": datetime.now().isoformat(),
        }
        self.history.append(log_entry)
        return log_entry
