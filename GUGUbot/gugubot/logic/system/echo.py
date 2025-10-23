"""回声系统模块。

该模块提供了回声功能，可以将一个平台的消息转发到其他平台。
"""

from gugubot.logic.system.basic_system import BasicSystem
from gugubot.utils.types import BoardcastInfo, ProcessedInfo


class EchoSystem(BasicSystem):
    """回声系统，负责消息的跨平台转发。

    将从一个平台收到的消息转发到其他已连接的平台。

    Attributes
    ----------
    name : str
        系统名称
    enable : bool
        系统是否启用
    """

    def __init__(self, enable: bool = True) -> None:
        """初始化回声系统。"""
        super().__init__(name="echo", enable=enable)

    def initialize(self) -> None:
        return

    async def process_boardcast_info(self, boardcast_info: BoardcastInfo) -> bool:
        """处理传入的消息。

        将收到的消息转发到除了源平台以外的其他平台。

        Parameters
        ----------
        boardcast_info : BoardcastInfo
            接收到的广播信息

        Returns
        -------
        bool
            是否成功处理了消息
        """
        try:
            # 准备转发的消息
            processed_info = self.create_processed_info(boardcast_info)
            
            # 转发到其他平台（排除源平台）
            await self.system_manager.connector_manager.broadcast_processed_info(
                processed_info,
                exclude=[boardcast_info.source]
            )

            return True

        except Exception as e:
            self.logger.error(f"Echo系统处理消息失败: {str(e)}", exc_info=True)
            return False

