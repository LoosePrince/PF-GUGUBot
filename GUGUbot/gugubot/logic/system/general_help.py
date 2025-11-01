# -*- coding: utf-8 -*-
"""通用帮助系统模块。

该模块提供了通用帮助功能，响应 # 或 #帮助 命令。
"""

from typing import Optional

from mcdreforged.api.types import PluginServerInterface

from gugubot.builder import MessageBuilder
from gugubot.config.BotConfig import BotConfig
from gugubot.logic.system.basic_system import BasicSystem
from gugubot.utils.types import BoardcastInfo


class GeneralHelpSystem(BasicSystem):
    """通用帮助系统，响应帮助命令。

    当用户发送 # 或 #帮助 时，显示通用帮助信息。

    Attributes
    ----------
    name : str
        系统名称
    enable : bool
        系统是否启用
    """

    def __init__(self, server: PluginServerInterface, config: Optional[BotConfig] = None) -> None:
        """初始化通用帮助系统。"""
        super().__init__("general_help", enable=True, config=config)
        self.server = server

    def initialize(self) -> None:
        """初始化系统，加载配置等"""
        return

    async def process_boardcast_info(self, boardcast_info: BoardcastInfo) -> bool:
        """处理接收到的命令。

        Parameters
        ----------
        boardcast_info: BoardcastInfo
            广播信息，包含消息内容
        
        Returns
        -------
        bool
            是否处理了该消息
        """
        message = boardcast_info.message

        if not message:
            return False

        first_message = message[0]
        if first_message.get("type") != "text":
            return False

        content = first_message.get("data", {}).get("text", "").strip()
        command_prefix = self.config.get("GUGUBot", {}).get("command_prefix", "#")

        # 检查是否是帮助命令
        help_command = self.get_tr("help_command")

        if content == command_prefix or content == f"{command_prefix}{help_command}":
            return await self._handle_help(boardcast_info)

        return False

    async def _handle_help(self, boardcast_info: BoardcastInfo) -> bool:
        """处理帮助命令"""
        command_prefix = self.config.get("GUGUBot", {}).get("command_prefix", "#")
        is_admin = boardcast_info.is_admin
        
        # 获取各系统的翻译名称
        key_words_name = self.server.tr("gugubot.system.key_words.name")
        ban_words_name = self.server.tr("gugubot.system.ban_words.name")
        bound_name = self.server.tr("gugubot.system.bound.name")
        whitelist_name = self.server.tr("gugubot.system.whitelist.name")
        startup_command_name = self.server.tr("gugubot.system.startup_command.name")
        style_name = self.server.tr("gugubot.system.style.name")
        
        # 根据是否是管理员显示不同的帮助信息
        if is_admin:
            help_msg = self.get_tr(
                "admin_help_msg", 
                command_prefix=command_prefix,
                key_words=key_words_name,
                ban_words=ban_words_name,
                bound=bound_name,
                whitelist=whitelist_name,
                startup_command=startup_command_name,
                style=style_name
            )
        else:
            help_msg = self.get_tr(
                "help_msg", 
                command_prefix=command_prefix,
                key_words=key_words_name,
                bound=bound_name,
                style=style_name
            )
        
        await self.reply(boardcast_info, [MessageBuilder.text(help_msg)])
        return True

