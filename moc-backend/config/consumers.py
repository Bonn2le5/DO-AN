"""Shared WebSocket behavior for JWT authenticated consumers."""

import asyncio
import time


class JWTExpiryConsumerMixin:
    """Close an authenticated WebSocket when its handshake access JWT expires."""

    async def tu_choi(self, code):
        """Từ chối kết nối với mã ứng dụng (4401 chưa đăng nhập, 4403 không có quyền, 4404 không thấy).

        Phải accept rồi mới đóng: đóng trước accept thì server trả HTTP 403 cho bắt tay và trình duyệt
        chỉ thấy mã 1006, frontend không phân biệt được nên kết nối lại mãi.
        """
        await self.accept()
        await self.close(code=code)

    def start_jwt_expiry_timer(self):
        expiry = self.scope.get("jwt_exp")
        if expiry:
            self._jwt_expiry_task = asyncio.create_task(self._close_at_jwt_expiry(expiry))

    async def _close_at_jwt_expiry(self, expiry):
        await asyncio.sleep(max(0, float(expiry) - time.time()))
        await self.close(code=4401)

    def cancel_jwt_expiry_timer(self):
        task = getattr(self, "_jwt_expiry_task", None)
        if task and not task.done():
            task.cancel()
