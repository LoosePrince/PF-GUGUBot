from dataclasses import dataclass
from logging import Logger
from mcdreforged.api.types import PluginServerInterface
from typing import Any, List, Literal, Optional

@dataclass
class ProcessedInfo:
    processed_message: List[dict]

    source: str
    source_id: str

    sender: str
    
    raw: Any
    server: PluginServerInterface
    logger: Logger

    receiver: Optional[str] = None

    target: Optional[dict] = None  # e.g., {"123456789": "group", "987654321": "private"}   
    