"""插件模块。

提供各种扩展功能的插件。
"""

from gugubot.logic.plugins.server_notice import (
    broadcast_server_start,
    broadcast_server_stop
)

__all__ = [
    'broadcast_server_start',
    'broadcast_server_stop'
]

