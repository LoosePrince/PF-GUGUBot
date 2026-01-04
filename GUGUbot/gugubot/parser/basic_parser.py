import traceback

from abc import ABC, abstractmethod
from typing import Any, Optional

from gugubot.utils.types import BoardcastInfo


class BasicParser(ABC):
    """基础解析器类。

    负责将不同平台的网络消息转换为统一的广播信息格式。

    Attributes
    ----------
    connector : BasicConnector
        消息连接器实例
    system_manager : SystemManager
        系统管理器实例，用于广播消息
    logger : Any
        日志记录器实例
    """

    def __init__(self, connector) -> None:
        """初始化解析器。

        Parameters
        ----------
        connector : BasicConnector
            消息连接器实例
        """
        self.connector = connector
        self.system_manager = connector.connector_manager.system_manager
        self.logger = connector.logger
        self.server = connector.server

    @abstractmethod
    async def parse(self, raw_message: Any, *args, **kargs) -> Optional[BoardcastInfo]:
        """解析原始消息。

        Parameters
        ----------
        raw_message : Any
            需要解析的原始消息

        Returns
        -------
        Optional[BoardcastInfo]
            解析后的广播信息对象，如果消息不需要广播则返回None
        """
        raise NotImplementedError

    async def process_message(self, raw_message: Any, *args, **kargs) -> None:
        """处理并广播消息。

        Parameters
        ----------
        raw_message : Any
            需要处理的原始消息
        """
        try:
            boardcast_info = await self.parse(raw_message, *args, **kargs)
            if boardcast_info is not None and self.system_manager is not None:
                await self.system_manager.broadcast_command(boardcast_info)
        except Exception as e:
            if self.logger:
                error_msg = str(e) + "\n" + traceback.format_exc()
                self.logger.error(f"消息处理失败: {error_msg}")