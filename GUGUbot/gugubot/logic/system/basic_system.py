import logging

from typing import TYPE_CHECKING, Optional

from gugubot.utils.types import BoardcastInfo

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

    def initialize(self) -> None:
        """初始化系统。

        在系统被注册到系统管理器时调用。
        子类应该重写此方法以实现自己的初始化逻辑。
        """
        pass

    async def process_command(self, boardcast_info: BoardcastInfo) -> bool:
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
        raise NotImplementedError("子类必须实现process_command方法")
