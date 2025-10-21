import traceback

from typing import Any, Optional, override

from mcdreforged.api.types import PluginServerInterface, Info

from gugubot.parser.basic_parser import BasicParser
from gugubot.utils.types import BoardcastInfo
from gugubot.utils.message import str_to_array


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

            self.logger.debug(
                f"[GUGUBot]收到Minecraft消息 - "
                f"玩家: {player}, "
                f"内容: {content}"
            )

            boardcast_info = BoardcastInfo(
                event_type="message",
                message=str_to_array(content),
                raw=raw_message,
                server=server,
                logger=self.logger,
                source=self.connector.source,
                source_id=None,
                sender=raw_message.player,
            )

            return boardcast_info

        except Exception as e:
            self.logger.error(f"MC消息解析失败: {str(e)}\n{traceback.format_exc()}")
            raise

