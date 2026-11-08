"""Shared WebSocket behavior for JWT authenticated consumers."""

import asyncio
import time


class JWTExpiryConsumerMixin:
    """Close an authenticated WebSocket when its handshake access JWT expires."""

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
