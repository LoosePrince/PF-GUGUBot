import traceback

import json
from typing import Dict, Optional

from gugubot.parser.basic_parser import BasicParser
from gugubot.builder.qq_builder import ArrayHandler, CQHandler
from gugubot.utils.types import BoardcastInfo


class QQParser(BasicParser):
    PROCESS_TYPE = ["message", "notice", "request"]

    """QQ消息解析器。

    处理来自QQ平台的消息，包括群聊消息、私聊消息等。
    """

    async def parse(self, raw_message: str) -> Optional[BoardcastInfo]:
        """解析QQ消息。

        Parameters
        ----------
        raw_message : str
            QQ WebSocket接收到的JSON格式消息

        Returns
        -------
        Optional[BoardcastInfo]
            解析后的广播信息对象，如果是回调消息则返回None
        """
        try:
            message_data: Dict = json.loads(raw_message)

            if not self._is_valid_source(message_data):
                return None

            event_type = message_data.get("post_type", "")
            if event_type not in self.PROCESS_TYPE:
                return None

            # 处理API调用的返回结果
            echo = message_data.get("echo")
            if echo:
                self.connector.bot.function_return[echo] = message_data
            elif event_type == "message":
                # 处理事件消息
                self_id = message_data.get("self_id")
                if self_id is not None:
                    self.connector.bot.self_id = self_id
                
                message = message_data.get("raw_message", "")
                parsed_message = CQHandler.parse(message) if isinstance(message, str) else ArrayHandler.parse(message)

                source_id = message_data.get("user_id") if message_data.get("message_type") == 'private' else message_data.get("group_id")
                source_type = "private" if message_data.get("message_type") == 'private' else "group"

                sender = message_data.get("sender", {})
                sender_name = sender.get("card") or sender.get("nickname")
                sender_id = str(sender.get("user_id"))   

                # 创建并处理QQ消息对象
                boardcase_info = BoardcastInfo(
                    event_type=event_type,
                    event_sub_type=source_type,
                    message=parsed_message,
                    raw=message_data,
                    server=self.server,
                    logger=self.logger,
                    source=self.connector.source,
                    source_id=str(source_id),
                    receiver_source=self.connector.source,  # 对于非桥接消息，receiver_source 等于 source
                    sender=sender_name,
                    sender_id=sender_id,
                    is_admin=self._is_admin(source_id) or self._is_admin(sender_id)
                )

            else:
                sub_type = message_data.get("request_type") if event_type == "request" else message_data.get("notice_type")

                boardcase_info = BoardcastInfo(
                    event_type=event_type,
                    event_sub_type=sub_type,
                    message=message_data,
                    raw=message_data,
                    server=self.server,
                    logger=self.logger,
                    source=self.connector.source,
                    source_id=message_data.get("user_id"),
                    receiver_source=self.connector.source,  # 对于非桥接消息，receiver_source 等于 source
                )
            
            return boardcase_info

        except Exception as e:
            self.logger.error(f"QQ消息解析失败: {str(e)}\n{traceback.format_exc()}")
            raise

    def _is_admin(self, sender_id) -> bool:
        """检查是否是管理员"""
        config = self.system_manager.config
        admin_ids = config.get_keys(["connector", "QQ", "permissions", "admin_ids"], [])
        admin_groups = config.get_keys(["connector", "QQ", "permissions", "admin_group_ids"], [])
        
        if str(sender_id) in [str(i) for i in admin_ids + admin_groups]:
            return True
        return False

    def _friend_is_admin(self, message_data) -> bool:
        """检查是否是好友管理员"""
        config = self.connector.config
        friend_is_admin = config.get_keys(["connector", "QQ", "permissions", "friend_is_admin"], False)
        
        is_private_chat = message_data.get("message_type") == 'private'

        return friend_is_admin and is_private_chat

    def _is_valid_source(self, message_data) -> bool:
        friend_is_admin = self._friend_is_admin(message_data)

        source_id = message_data.get("user_id") if message_data.get("message_type") == 'private' else message_data.get("group_id")

        admin_ids = self.connector.config.get_keys(["connector", "QQ", "permissions", "admin_ids"], [])
        admin_groups = self.connector.config.get_keys(["connector", "QQ", "permissions", "admin_group_ids"], [])
        group_ids = self.connector.config.get_keys(["connector", "QQ", "permissions", "group_ids"], [])

        valid_source = [str(i) for i in admin_ids + admin_groups + group_ids]

        return friend_is_admin or str(source_id) in valid_source

    

