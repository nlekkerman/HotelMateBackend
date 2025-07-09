# debug_injection.py
# Place this in your project root and import it at the very top of settings.py

import builtins
from functools import wraps

# --- 1) Patch redis.asyncio.connection.Connection.connect ---
try:
    from redis.asyncio.connection import Connection as _RedisConn

    _orig_connect = _RedisConn.connect

    async def _debug_connect(self):
        builtins.print(
            f"[DEBUG][RedisConn] connecting → host={self.host!r}, port={self.port!r}, "
            f"ssl_context={getattr(self, 'ssl_context', None)!r}"
        )
        try:
            return await _orig_connect(self)
        except Exception as e:
            builtins.print(f"[DEBUG][RedisConn] handshake failed → {e!r}")
            raise

    _RedisConn.connect = _debug_connect
    builtins.print("[DEBUG] Patched redis.asyncio.connection.Connection.connect")

except ImportError as ie:
    builtins.print(f"[DEBUG] Could not patch RedisConn: {ie!r}")


# --- 2) Patch channels_redis.core.RedisChannelLayer.group_send ---
try:
    from channels_redis.core import RedisChannelLayer as _RCL

    _orig_group_send = _RCL.group_send

    async def _debug_group_send(self, group, message):
        builtins.print(f"[DEBUG][ChannelLayer] group_send → group={group!r}, message={message!r}")
        try:
            res = await _orig_group_send(self, group, message)
            builtins.print("[DEBUG][ChannelLayer] group_send succeeded")
            return res
        except Exception as e:
            builtins.print(f"[DEBUG][ChannelLayer] group_send failed → {e!r}")
            raise

    _RCL.group_send = _debug_group_send
    builtins.print("[DEBUG] Patched channels_redis.core.RedisChannelLayer.group_send")

except ImportError as ie:
    builtins.print(f"[DEBUG] Could not patch ChannelLayer: {ie!r}")
