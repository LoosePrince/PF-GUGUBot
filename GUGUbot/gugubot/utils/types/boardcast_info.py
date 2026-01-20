from dataclasses import dataclass
from logging import Logger
from typing import Any, List, Literal, Optional


from mcdreforged.api.types import PluginServerInterface


@dataclass
class BoardcastInfo:
    event_type: Literal["message", "notice", "request"]
    event_sub_type: str
    message: List[dict]

    raw: Any

    server: Optional[PluginServerInterface] = None
    logger: Optional[Logger] = None

    source: str = ""
    source_id: str = ""
    sender: str = ""
    sender_id: str = ""
    receiver_source: str = ""  # 接收消息的本地 connector 的 source
    receiver: Optional[str] = None  # 消息的接收者（例如回复消息时的原发送者）

    is_admin: bool = False

    target: Optional[dict] = (
        None  # e.g., {"123456789": "group", "987654321": "private"}
    )
