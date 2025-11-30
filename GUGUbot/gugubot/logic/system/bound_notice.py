# -*- coding: utf-8 -*-

from typing import Optional

from gugubot.builder import MessageBuilder
from gugubot.config.BotConfig import BotConfig
from gugubot.logic.system.basic_system import BasicSystem
from gugubot.utils.types import BoardcastInfo


class BoundNoticeSystem(BasicSystem):
    """绑定提醒系统，用于提醒未绑定的玩家进行账号绑定。
    
    当玩家发送消息时，如果该玩家未在玩家管理器中绑定账号，
    则提醒其进行绑定。不会拦截消息，让其他系统继续处理。
    """

    def __init__(self, config: Optional[BotConfig] = None) -> None:
        """初始化绑定提醒系统。"""
        super().__init__("bound_notice", enable=False, config=config)
        self.bound_system = None

    def initialize(self) -> None:
        """初始化系统，加载配置等"""
        self.logger.debug("绑定提醒系统已初始化")

    def set_bound_system(self, bound_system) -> None:
        """设置绑定系统引用，用于访问玩家管理器"""
        self.bound_system = bound_system

    async def process_boardcast_info(self, boardcast_info: BoardcastInfo) -> bool:
        """处理接收到的消息。

        Parameters
        ----------
        boardcast_info: BoardcastInfo
            广播信息，包含消息内容
        """
        message = boardcast_info.message

        if not message:
            return False

        # 先检查是否是开启/关闭命令
        if await self.handle_enable_disable(boardcast_info):
            return True

        # 如果系统未启用或没有绑定系统引用，不处理
        if not self.enable or not self.bound_system:
            return False

        return await self._check_and_notify(boardcast_info)

    async def _check_and_notify(self, boardcast_info: BoardcastInfo) -> bool:
        """检查玩家是否已绑定，如果未绑定则发送提醒"""
        # 只在有发送者ID的情况下检查
        if not boardcast_info.sender_id:
            return False

        # 检查玩家是否在玩家管理器中
        player = self.bound_system.player_manager.get_player(
            boardcast_info.sender_id, 
            platform=boardcast_info.source
        )

        # 如果玩家未绑定，发送提醒消息
        if not player:
            command_prefix = self.config.get("GUGUBot", {}).get("command_prefix", "#")
            # 获取绑定系统的名称
            bound_name = self.bound_system.get_tr("name")
            
            notice_msg = self.get_tr(
                "notice_message", 
                command_prefix=command_prefix,
                bound_name=bound_name
            )
            await self.reply(boardcast_info, [MessageBuilder.at(boardcast_info.sender_id), MessageBuilder.text(notice_msg)])

        # 不拦截消息，让其他系统继续处理
        return False

