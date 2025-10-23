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

	is_admin: bool = False