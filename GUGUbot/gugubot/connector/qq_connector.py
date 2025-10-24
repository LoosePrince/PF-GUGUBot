import logging
import traceback
import time
import uuid

import asyncio

from typing import Any, Optional, override

from gugubot.builder import MessageBuilder
from gugubot.connector.basic_connector import BasicConnector
from gugubot.config.BotConfig import BotConfig
from gugubot.utils.types import ProcessedInfo
from gugubot.parser.qq_parser import QQParser
from gugubot.ws import WebSocketFactory

class Bot:
    def __init__(self, send_message, max_wait_time: int = 9) -> None:
        self.send_message = send_message
        self.max_wait_time = max_wait_time if 0 < max_wait_time <= 9 else 9
        self.function_return = {}
        self.self_id = None  # 机器人自己的QQ号

    @staticmethod
    def format_request(action: str, params: dict = {}):
        return {
            "action": action,
            "params": params,
            "echo": params.get("echo", "")
        }

    def __getattr__(self, name):
        if name.startswith("get_") or name.startswith("can_") or name.startswith("_get"):
            async def handler(**kwargs):
                # For methods that are expected to return a value,
                # automatically add an echo id to track the response.
                
                function_return_id = str(uuid.uuid4())
                kwargs["echo"] = function_return_id
                command_request = self.format_request(name, kwargs)
                await self.send_message(command_request)

                start_time = time.time()
                import asyncio
                while True:
                    if function_return_id in self.function_return:
                        result = self.function_return[function_return_id]
                        del self.function_return[function_return_id]
                        return result

                    await asyncio.sleep(0.2)
                    if time.time() - start_time >= self.max_wait_time:
                        del self.function_return[function_return_id]
                        return None
        else:
            async def handler(**kwargs):
                command_request = self.format_request(name, kwargs)
                await self.send_message(command_request)
        return handler

class QQWebSocketConnector(BasicConnector):
    def __init__(self, server, config: BotConfig = None):
        super().__init__(source="QQ", parser=QQParser)
        self.server = server
        self.ws_client = None
        self.config = config or {}
        
        # determine scheme using single parameter 'use_ssl' (boolean)
        self.use_ssl = config.get_keys(["connector", "QQ", "connection", "use_ssl"], False)
        self.scheme = "wss" if self.use_ssl else "ws"
        self.url = self._build_url(config)
        
        self.token = config.get_keys(["connector", "QQ", "connection", "token"], None)
        self.reconnect = config.get_keys(["connector", "QQ", "connection", "reconnect"], 5)
        self.verify = config.get_keys(["connector", "QQ", "connection", "verify"], True)
        self.ca_certs = config.get_keys(["connector", "QQ", "connection", "ca_certs"], None)
        self.extra_sslopt = config.get_keys(["connector", "QQ", "connection", "sslopt"], {})

        self.bot = Bot(self._send_message, max_wait_time=config.get_keys(["connector", "QQ", "connection", "max_wait_time"], 5))

    def _build_url(self, config):
        host = config.get_keys(["connector", "QQ", "connection", "host"], "127.0.0.1")
        port = config.get_keys(["connector", "QQ", "connection", "port"], 8080)
        post_path = config.get_keys(["connector", "QQ", "connection", "post_path"], "")
        url = f"{self.scheme}://{host}:{port}"
        if post_path:
            url += f"/{post_path}"

        return url

    @override
    async def connect(self) -> None:
        """建立到QQ WebSocket服务器的连接"""
        self.logger.info(self.server.tr("gugubot.connector.QQ.try_connect", url=self.url))
        
        # 使用WebSocketFactory创建客户端
        self.ws_client = WebSocketFactory.create_client(
            url=self.url,
            token=self.token,
            on_message=self.on_message,
            on_open=self._on_open,
            on_error=self._on_error,
            on_close=self._on_close,
            logger=self.logger
        )
        
        # 连接到服务器
        self.ws_client.connect(
            reconnect=self.reconnect,
            use_ssl=self.use_ssl,
            verify=self.verify,
            ca_certs=self.ca_certs,
            extra_sslopt=self.extra_sslopt,
            thread_name="[GUGUBot]QQ_Connector"
        )
        
        self.logger.info(self.server.tr("gugubot.connector.QQ.start_connect"))

    def _on_open(self, _):
        self.logger.info(f"[{self.source}] " + self.server.tr("gugubot.connector.QQ.connect_success"))

    def _on_error(self, _: Any, error: Exception) -> None:
        """处理WebSocket错误

        Parameters
        ----------
        _ : Any
            WebSocket实例（未使用）
        error : Exception
            发生的错误
        """
        self.logger.error(self.server.tr("gugubot.connector.QQ.error_connect", error=error))

    def _on_close(self, _: Any, status_code: Optional[int], reason: Optional[str]) -> None:
        """处理WebSocket连接关闭

        Parameters
        ----------
        _ : Any
            WebSocket实例（未使用）
        status_code : Optional[int]
            关闭状态码
        reason : Optional[str]
            关闭原因
        """
        self.logger.debug(
            self.server.tr("gugubot.connector.QQ.close_connect", status_code=status_code, reason=reason)
        )


    async def _send_message(self, message: Any) -> None:
        """向QQ WebSocket服务器发送消息"""
        if self.ws_client and self.ws_client.is_connected():
            if self.ws_client.send(message):
                self.logger.debug(self.server.tr("gugubot.connector.QQ.send_message", message=message))
            else:
                self.logger.error(self.server.tr("gugubot.connector.QQ.send_message_failed", error="发送失败"))
        else:
            self.logger.warning(self.server.tr("gugubot.connector.QQ.retry_connect"))


    async def send_message(self, processed_info: ProcessedInfo) -> None:
        forward_group_ids = self.config.get_keys(["connector", "QQ", "permissions", "group_ids"], [])
        forward_group_target = {str(group_id): "group" for group_id in forward_group_ids}
        target = processed_info.target or forward_group_target

        message = processed_info.processed_message
        source = processed_info.source
        if source != "QQ":
            source_message = MessageBuilder.text(f"[{source}] {processed_info.sender}: ")
            message = [source_message] + message

        for target_id, target_type in target.items():
            if target_type == "group":
                await self.bot.send_group_msg(
                    group_id=int(target_id),
                    message=message
                )
            elif target_type == "private":
                await self.bot.send_private_msg(
                    user_id=int(target_id),
                    message=message
                )
            else:
                await self.bot.send_temp_msg(
                    group_id=int(target_type),
                    user_id=int(target_id),
                    message=message
                )

    @override
    async def disconnect(self) -> None:
        """断开与QQ WebSocket服务器的连接"""
        try:
            if self.ws_client:
                self.ws_client.disconnect(timeout=5)
            self.logger.info(self.server.tr("gugubot.connector.QQ.close_info"))
        except Exception as e:
            self.logger.warning(self.server.tr("gugubot.connector.QQ.error_close", error=str(e) + f"\n{traceback.format_exc()}"))
            raise

    @override
    def on_message(self, _, raw_message: str) -> None:
        """处理并分发WebSocket消息。

        处理流程:
        1. 将原始JSON字符串解析为消息数据
        2. 如果是回调消息（包含echo），存储到function_return
        3. 如果是事件消息：
           - 更新机器人ID（如果包含）
           - 创建并处理QQ信息对象

        Parameters
        ----------
        raw_message : str
            WebSocket接收到的JSON格式消息
        """
        try:
            asyncio.run(self.parser(self).process_message(raw_message))

        except Exception as e:
            # 使用翻译条目并包含堆栈信息
            self.logger.error(self.server.tr("gugubot.connector.QQ.message_handle_failed", error=str(e) + f"\n{traceback.format_exc()}"))
