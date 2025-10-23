import logging

from typing import TYPE_CHECKING, List, Optional

from gugubot.config.BotConfig import BotConfig
from gugubot.utils.types import BoardcastInfo, ProcessedInfo

if TYPE_CHECKING:
    from gugubot.logic.system.system_manager import SystemManager
    

class BasicSystem:
    """基础系统类，所有系统都应该继承此类。

    提供系统的基本功能和接口。

    Attributes
    ----------
    name : str
        系统名称
    system_manager : SystemManager
        系统管理器的引用
    logger : logging.Logger
        日志记录器实例
    """

    def __init__(self, name: str, enable: bool = True) -> None:
        """初始化基础系统。

        Parameters
        ----------
        name : str
            系统名称
        """
        self.name = name
        self.system_manager: Optional[SystemManager] = None
        self.logger: Optional[logging.Logger] = None
        self.enable: bool = enable
        self.config: Optional[BotConfig] = None

    def initialize(self) -> None:
        """初始化系统。

        在系统被注册到系统管理器时调用。
        子类应该重写此方法以实现自己的初始化逻辑。
        """
        pass

    async def process_boardcast_info(self, boardcast_info: BoardcastInfo) -> bool:
        """处理接收到的命令。

        Parameters
        ----------
        boardcast_info : BoardcastInfo
            命令信息

        Returns
        -------
        bool
            命令是否成功处理

        子类必须重写此方法以实现命令处理逻辑。
        """
        raise NotImplementedError("子类必须实现process_boardcast_info方法")

    def is_command(self, boardcast_info: BoardcastInfo) -> bool:
        """判断是否是命令
        
        Parameters
        ----------
        boardcast_info : BoardcastInfo
            广播信息

        Returns
        -------
        bool
            是否是命令
        """
        message = boardcast_info.message
        if not message:
            return False
        
        first_message = message[0]
        if first_message.get("type") != "text":
            return False
        
        content = first_message.get("data",{}).get("text", "")
        command_prefix = self.config.get("GUGUBot", {}).get("command_prefix", "#")

        return content.startswith(command_prefix)

    @staticmethod
    def create_processed_info(boardcast_info: BoardcastInfo) -> ProcessedInfo:
        """创建用于转发的处理后消息对象。

        Parameters
        ----------
        boardcast_info : BoardcastInfo
            原始广播信息

        Returns
        -------
        ProcessedInfo
            处理后的消息对象
        """
        # 构造转发消息的格式

        return ProcessedInfo(
            processed_message=boardcast_info.message,
            source=boardcast_info.source,
            source_id=boardcast_info.source_id,
            sender=boardcast_info.sender,
            raw=boardcast_info.raw,
            server=boardcast_info.server,
            logger=boardcast_info.logger
        )

    async def reply(self, boardcast_info: BoardcastInfo, message: List[dict]) -> None:

        respond = ProcessedInfo(
            processed_message=message,
            source=boardcast_info.source,
            source_id=boardcast_info.source_id,
            sender=self.system_manager.server.tr("gugubot.bot_name"),
            raw=boardcast_info.raw,
            server=boardcast_info.server,
            logger=boardcast_info.logger,
            target={boardcast_info.source_id: boardcast_info.event_sub_type}
        )

        await self.system_manager.connector_manager.broadcast_processed_info(
            respond,
            include=[boardcast_info.source]
        )

    def get_tr(self, key: str, global_key: bool = False, **kwargs) -> str:
        server = self.system_manager.server 
        if global_key:
            return server.tr(key, **kwargs)
        else:
            return server.tr(f"gugubot.system.{self.name}.{key}", **kwargs)
        
        
