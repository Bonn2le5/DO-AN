"""
Redis Table Hold & 2-Phase Concurrency Control Simulator.
Implements the exact logic of Phase 1 (Redis SET NX EX 600) and Phase 2 (DB Lock + Token validation)
defined in Master Thesis Paragraph 26 and moc_schema_tieng_viet.sql.
"""

import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple


class RedisTableLockSimulator:
    """
    Thread-safe simulator of Redis temporary table reservation hold with TTL countdown.
    Supports atomic SET NX EX, TTL expiration, and 2-phase confirmation.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # Storage: key -> {"token": str, "user_id": int, "expires_at": float, "metadata": dict}
        self._store: Dict[str, Dict[str, Any]] = {}
        # Database confirmed bookings: key -> dict
        self._db_bookings: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def make_key(ban_id: int, ngay: str, gio: str) -> str:
        return f"giu-ban:{ban_id}:{ngay}:{gio}"

    def hold_table(
        self,
        ban_id: int,
        ngay: str,
        gio: str,
        user_id: int,
        ttl_seconds: int = 600,
        party_size: int = 4,
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Phase 1: Attempt to hold table using atomic SET NX EX.
        Returns: (http_status_code, response_data)
        - HTTP 200: Successfully held
        - HTTP 409: Conflict, table already held or booked
        """
        key = self.make_key(ban_id, ngay, gio)
        now = time.time()

        with self._lock:
            # Check if permanently booked in DB
            if key in self._db_bookings:
                return 409, {
                    "status": "conflict",
                    "error_code": "TABLE_ALREADY_BOOKED",
                    "message": "Bàn ăn này đã được chốt đặt trong khung giờ này.",
                    "ban_an_id": ban_id,
                    "ngay_dat": ngay,
                    "gio_bat_dau": gio,
                }

            # Check existing Redis key
            existing = self._store.get(key)
            if existing is not None:
                if existing["expires_at"] > now:
                    # Still active -> Conflict!
                    remaining = int(existing["expires_at"] - now)
                    return 409, {
                        "status": "conflict",
                        "error_code": "TABLE_CURRENTLY_HELD",
                        "message": "Bàn ăn này đang được khách hàng khác giữ chỗ trong 10 phút. Vui lòng chọn bàn khác hoặc thử lại sau.",
                        "ban_an_id": ban_id,
                        "ngay_dat": ngay,
                        "gio_bat_dau": gio,
                        "retry_after_seconds": remaining,
                    }
                else:
                    # Expired, clean up
                    del self._store[key]

            # Atomic SET NX EX
            token = f"HOLD_{uuid.uuid4().hex}"
            expires_at = now + ttl_seconds
            expires_iso = (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat()

            self._store[key] = {
                "token": token,
                "user_id": user_id,
                "expires_at": expires_at,
                "metadata": {
                    "ban_id": ban_id,
                    "ngay": ngay,
                    "gio": gio,
                    "party_size": party_size,
                },
            }

            return 200, {
                "status": "success",
                "id_giu_ban": token,
                "thoi_han_giu_cho": expires_iso,
                "thoi_gian_con_lai_giay": ttl_seconds,
                "ban_an_id": ban_id,
                "ngay_dat": ngay,
                "gio_bat_dau": gio,
            }

    def confirm_booking(
        self,
        ban_id: int,
        ngay: str,
        gio: str,
        user_id: int,
        hold_token: str,
        so_tien_coc: float = 200000.0,
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Phase 2: Database Confirmation with Pessimistic Locking.
        Validates hold_token and commits booking record.
        """
        key = self.make_key(ban_id, ngay, gio)
        now = time.time()

        with self._lock:
            # Check DB collision
            if key in self._db_bookings:
                return 409, {
                    "status": "conflict",
                    "error_code": "TABLE_ALREADY_CONFIRMED",
                    "message": "Bàn ăn này đã có khách hàng chốt xác nhận.",
                }

            # Check hold token
            current_hold = self._store.get(key)
            if not current_hold:
                return 400, {
                    "status": "error",
                    "error_code": "HOLD_EXPIRED",
                    "message": "Phiên giữ bàn đã hết hạn (quá 10 phút). Vui lòng thực hiện lại.",
                }

            if current_hold["expires_at"] <= now:
                del self._store[key]
                return 400, {
                    "status": "error",
                    "error_code": "HOLD_EXPIRED",
                    "message": "Phiên giữ bàn đã hết hạn.",
                }

            if current_hold["token"] != hold_token:
                return 403, {
                    "status": "error",
                    "error_code": "INVALID_TOKEN",
                    "message": "Mã giữ chỗ không hợp lệ.",
                }

            # Commit to DB
            booking_id = f"DB{int(time.time()*1000) % 10000000:07d}"
            db_record = {
                "ma_dat_ban": booking_id,
                "ban_an_id": ban_id,
                "user_id": user_id,
                "ngay_dat": ngay,
                "gio_bat_dau": gio,
                "so_tien_coc": so_tien_coc,
                "trang_thai": "da_xac_nhan",
                "trang_thai_coc": "thanh_cong",
                "xac_nhan_luc": datetime.now().isoformat(),
            }
            self._db_bookings[key] = db_record

            # Release Redis key
            del self._store[key]

            return 201, {
                "status": "success",
                "ma_dat_ban": booking_id,
                "data": db_record,
            }

    def release_hold(self, ban_id: int, ngay: str, gio: str, hold_token: str) -> bool:
        """Manually release hold token."""
        key = self.make_key(ban_id, ngay, gio)
        with self._lock:
            if key in self._store and self._store[key]["token"] == hold_token:
                del self._store[key]
                return True
            return False

    def is_table_available(self, ban_id: int, ngay: str, gio: str) -> bool:
        """Check if table is free (neither held nor confirmed)."""
        key = self.make_key(ban_id, ngay, gio)
        now = time.time()
        with self._lock:
            if key in self._db_bookings:
                return False
            if key in self._store:
                if self._store[key]["expires_at"] > now:
                    return False
                else:
                    del self._store[key]
            return True
