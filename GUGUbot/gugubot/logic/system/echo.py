"""回声系统模块。

该模块提供了回声功能，可以将一个平台的消息转发到其他平台。
"""

from gugubot.config.BotConfig import BotConfig
from gugubot.logic.system.basic_system import BasicSystem
from gugubot.utils.types import BoardcastInfo


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

    def __init__(self, enable: bool = True, config: BotConfig = None) -> None:
        """初始化回声系统。"""
        super().__init__(name="echo", enable=enable, config=config)

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
        # 先检查是否是开启/关闭命令
        if await self.handle_enable_disable(boardcast_info):
            return True

        # 检查是否是QQ私聊消息，如果是则不广播
        if boardcast_info.source == "QQ" and boardcast_info.event_sub_type == "private":
            return False

        # 检查是否是QQ管理群的消息，如果是则不广播
        if boardcast_info.source == "QQ" and boardcast_info.event_sub_type == "group":
            admin_group_ids = self.config.get_keys(
                ["connector", "QQ", "permissions", "admin_group_ids"], []
            )
            if boardcast_info.source_id and str(boardcast_info.source_id) in [
                str(i) for i in admin_group_ids if i
            ]:
                # 管理群消息不广播，直接返回False
                return False

        if boardcast_info.event_type != "message":
            return False

        try:
            # 准备转发的消息
            processed_info = self.create_processed_info(boardcast_info)

            # 转发到其他平台（排除接收消息的本地 connector）
            # 使用 receiver_source 如果存在，否则回退到 source
            exclude_source = (
                boardcast_info.receiver_source
                if boardcast_info.receiver_source
                else boardcast_info.source
            )
            await self.system_manager.connector_manager.broadcast_processed_info(
                processed_info, exclude=[exclude_source]
            )

            return True

        except Exception as e:
            self.logger.error(f"Echo系统处理消息失败: {str(e)}", exc_info=True)
            return False
