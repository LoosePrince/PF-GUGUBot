import re
import traceback

from typing import Any, Optional, override

from mcdreforged.api.types import PluginServerInterface, Info

from gugubot.builder import CQHandler
from gugubot.parser.basic_parser import BasicParser
from gugubot.utils.types import BoardcastInfo


class MCParser(BasicParser):
    """Minecraft服务器消息解析器。

    处理来自Minecraft服务器的消息，包括玩家聊天、系统消息等。
    """

    @override
    async def parse(self, raw_message: Info, server: PluginServerInterface) -> Optional[BoardcastInfo]:
        """解析Minecraft消息。

        Parameters
        ----------
        raw_message : Any
            从Minecraft服务器接收到的原始消息

        Returns
        -------
        Optional[BoardcastInfo]
            解析后的广播信息对象
        """
        try:
            player = raw_message.player
            content = raw_message.content

            if self._ignore_message(content):
                return None

            self.logger.debug(
                f"[GUGUBot]收到Minecraft消息 - "
                f"玩家: {player}, "
                f"内容: {content}"
            )

            boardcast_info = BoardcastInfo(
                event_type="message",
                event_sub_type="group",
                message=CQHandler.parse(content),
                raw=content,
                server=server,
                logger=self.logger,
                source=self.connector.source,
                source_id=None,
                receiver_source=self.connector.source,  # 对于非桥接消息，receiver_source 等于 source
                sender=raw_message.player,
                sender_id=raw_message.player,
                is_admin=self.connector._is_admin(raw_message.player)
            )

            return boardcast_info

        except Exception as e:
            self.logger.error(f"MC消息解析失败: {str(e)}\n{traceback.format_exc()}")
            raise

    def _ignore_message(self, content: str) -> bool:
        """检查消息是否需要忽略"""
        config  = self.connector.config
        ignore_mc_command_patterns = config.get_keys(["connector", "minecraft", "ignore_mc_command_patterns"], [])

        for pattern in ignore_mc_command_patterns:
            if re.match(pattern, content):
                return True
        return False

