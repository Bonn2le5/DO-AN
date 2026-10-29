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

__all__ = ["WebsocketCommunicator", "get_channel_layer"]
