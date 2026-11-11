"""
Channels Testing Helper for Mộc Restaurant.
Stubs daphne dependencies in sys.modules so WebsocketCommunicator can be imported
and used in testing environments where daphne is not installed.
"""

import sys
import types

if "daphne" not in sys.modules:
    daphne_mod = types.ModuleType("daphne")
    daphne_mod.testing = types.SimpleNamespace(DaphneProcess=object)
    sys.modules["daphne"] = daphne_mod
    sys.modules["daphne.testing"] = daphne_mod.testing

from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer

__all__ = ["WebsocketCommunicator", "get_channel_layer", "ma_dong_khi_tu_choi"]


async def ma_dong_khi_tu_choi(communicator):
    """Mã đóng khi server từ chối kết nối.

    Server phải accept rồi mới đóng: nếu đóng trước accept, trình duyệt thật chỉ thấy mã 1006
    (WebsocketCommunicator vẫn báo mã nên không tự phát hiện được lỗi này).
    """
    connected, _ = await communicator.connect()
    assert connected, "Server từ chối ngay lúc bắt tay: trình duyệt sẽ không nhận được mã đóng"
    msg = await communicator.receive_output()
    assert msg["type"] == "websocket.close", msg
    return msg.get("code")
