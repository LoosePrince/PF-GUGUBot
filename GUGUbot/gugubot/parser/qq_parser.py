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

            echo = message_data.get("echo")# 处理API调用的返回结果
            if echo:
                self.connector.bot.function_return[echo] = message_data
                return None
            
            if not self._is_valid_source(message_data):
                return None

            event_type = message_data.get("post_type", "")
            if event_type not in self.PROCESS_TYPE:
                return None

            if event_type == "message":
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
                
                # 检查是否应该排除此用户的消息
                if await self._should_exclude_user(sender_id, source_id, source_type):
                    self.logger.debug(f"已在connector层拦截排除用户 {sender_id} 的消息")
                    return None

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

                return None
            
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

    async def _should_exclude_user(self, user_id: str, source_id: str, source_type: str) -> bool:
        """检查用户是否应该被排除（完全忽略其消息）
        
        Parameters
        ----------
        user_id : str
            用户QQ号
        source_id : str
            消息来源ID（群号或用户号）
        source_type : str
            消息来源类型（group 或 private）
        
        Returns
        -------
        bool
            True 表示应该排除此用户，False 表示不应该排除
        """
        # 1. 排除配置中指定的额外用户列表
        exclude_ids = self.connector.config.get_keys(["system", "bound_notice", "exclude_ids"], [])
        if user_id in [str(exclude_id) for exclude_id in exclude_ids if exclude_id]:
            self.logger.debug(f"用户 {user_id} 在排除列表中，忽略消息")
            return True
        
        return False


