from typing import Optional

from gugubot.connector.basic_connector import BoardcastInfo
from gugubot.logic.system.system_manager import SystemManager
from gugubot.utils.types import ProcessedInfo



class BasicHandler:
    """基础处理器类。
    
    提供基本的消息处理功能，包含系统管理器。

    Attributes
    ----------
    system_manager : Optional[SystemManager]
        系统管理器实例，用于管理和分发消息到不同的系统
    """

    def __init__(self, system_manager: Optional[SystemManager] = None) -> None:
        """初始化基础处理器。

        Parameters
        ----------
        system_manager : Optional[SystemManager]
            系统管理器实例。如果未提供，处理器将在没有系统管理器的情况下运行。
        """
        self.system_manager = system_manager

    async def process(self, boardcast_info: BoardcastInfo) -> None:
        """处理广播信息。

        该方法处理接收到的广播信息，并可能将其转发给系统管理器。

        Parameters
        ----------
        boardcast_info : BoardcastInfo
            需要处理的广播信息
        """
        # 在这里实现对boardcast_info.message的处理逻辑
        is_processed = await self.system_manager.broadcast_command(boardcast_info)

        if is_processed:
            return None # 已被处理，不需要进一步广播

        processed_info = ProcessedInfo(
            processed_message=boardcast_info.message,
            source=boardcast_info.source,
            source_id=boardcast_info.source_id,
            sender=boardcast_info.sender,
            raw=boardcast_info.raw,
            server=boardcast_info.server,
            logger=boardcast_info.logger
        )

        await self.system_manager.connector_manager.broadcast_processed_info(
            processed_info,
            exclude=[boardcast_info.source]
        )
