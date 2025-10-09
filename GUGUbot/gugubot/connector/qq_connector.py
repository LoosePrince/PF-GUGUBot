import asyncio
import json
import logging
import threading
import time
import uuid
import websocket
from typing import Any, Dict, Optional, Union

from GUGUbot.gugubot.connector.basic_connector import BasicConnector
from gugubot.parser.InfoSource.QQ import QQInfo
from gugubot.constant.language import LANGUAGE

logging.getLogger("websocket").setLevel(logging.WARNING)

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
        def handler(**kwargs):
            # For methods that are expected to return a value,
            # automatically add an echo id to track the response.
            if name.startswith("get_") or name.startswith("can_") or name.startswith("_get"):
                function_return_id = str(uuid.uuid4())
                kwargs["echo"] = function_return_id
                command_request = self.format_request(name, kwargs)
                self.send_message(command_request)

                start_time = time.time()
                while True:
                    if function_return_id in self.function_return:
                        result = self.function_return[function_return_id]
                        del self.function_return[function_return_id]
                        return result

                    time.sleep(0.2)
                    if time.time() - start_time >= self.max_wait_time:
                        return None
            else:
                command_request = self.format_request(name, kwargs)
                self.send_message(command_request)
        return handler

class QQWebSocketConnector(BasicConnector):
    def __init__(self, server, config):
        super().__init__(source="QQ")
        self.config = config
        self.server = server
        self.ws = None
        self.listener_thread = None
        self.language = config.get("language", "zh")
        
        # 检查语言包是否存在
        if self.language not in LANGUAGE:
            self.server.logger.warning(f"未找到语言包: {self.language}，使用默认语言")
            self.language = "zh"
        
        self.url = self._build_url(config)
        token = config.get("token")
        self.headers = {"Authorization": f"Bearer {token}"} if token else None

        self.bot = Bot(self.send_message, max_wait_time=config.get("max_wait_time", 5))

    def _build_url(self, config):
        host = config.get("host", "127.0.0.1")
        port = config.get("port", 6700)
        post_path = config.get("post_path", "")
        url = f"ws://{host}:{port}"
        if post_path:
            url += f"/{post_path}"

        return url

    async def connect(self) -> None:
        """建立到QQ WebSocket服务器的连接"""
        self.server.logger.info(LANGUAGE[self.language]["try_connect"].format(self.url))
        self.ws = websocket.WebSocketApp(
            self.url,
            header=self.headers,
            on_message=self._on_websocket_message,
            on_error=self.on_error,
            on_close=self.on_close
        )

        self.listener_thread = threading.Thread(target=self.ws.run_forever, kwargs={'reconnect': 5})
        self.listener_thread.daemon = True  # 设置为守护线程
        self.listener_thread.start()
        self.server.logger.info(LANGUAGE[self.language]["start_connect"])

    def _on_websocket_message(self, _: Any, raw_message: str) -> None:
        """处理来自WebSocket的原始消息回调。

        Parameters
        ----------
        _ : Any
            WebSocket实例（未使用）
        raw_message : str
            接收到的原始消息字符串
        """
        try:
            self.server.logger.debug(LANGUAGE[self.language]["received_message"].format(raw_message))
            asyncio.create_task(self.on_message(raw_message))
        except Exception as e:
            self.server.logger.error(f"WebSocket消息处理失败: {str(e)}")

    def on_error(self, _: Any, error: Exception) -> None:
        """处理WebSocket错误

        Parameters
        ----------
        _ : Any
            WebSocket实例（未使用）
        error : Exception
            发生的错误
        """
        self.server.logger.error(LANGUAGE[self.language]["error_connect"].format(error))

    def on_close(self, _: Any, status_code: Optional[int], reason: Optional[str]) -> None:
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
        self.server.logger.debug(
            f"{LANGUAGE[self.language]['close_connect']} " + 
            f"(状态码: {status_code if status_code is not None else '未知'}, " +
            f"原因: {reason if reason is not None else '未知'})"
        )


    async def send_message(self, message: Any) -> None:
        """向QQ WebSocket服务器发送消息"""
        if self.ws and self.ws.sock and self.ws.sock.connected:
            try:
                self.ws.send(json.dumps(message))
                self.server.logger.debug(LANGUAGE[self.language]["send_message"].format(message))
            except Exception as e:
                self.server.logger.error(f"发送消息失败: {e}")
        else:
            self.server.logger.warning(LANGUAGE[self.language]["retry_connect"])

    async def disconnect(self) -> None:
        """断开与QQ WebSocket服务器的连接"""
        try:
            if self.ws:
                self.ws.close()
            if self.listener_thread and self.listener_thread.is_alive():
                self.listener_thread.join(timeout=5)  # 设置超时时间
            self.server.logger.info(LANGUAGE[self.language]["close_info"])
        except Exception as e:
            self.server.logger.warning(LANGUAGE[self.language]["error_close"].format(e))
            raise

    async def on_message(self, raw_message: str) -> None:
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
            message_data: Dict = json.loads(raw_message)
            
            # 处理API调用的返回结果
            echo = message_data.get("echo")
            if echo:
                self.bot.function_return[echo] = message_data
            else:
                # 处理事件消息
                self_id = message_data.get("self_id")
                if self_id is not None:
                    self.bot.self_id = self_id
                
                # 创建并处理QQ消息对象
                QQInfo(message_data, self.server, self.bot)
                
        except json.JSONDecodeError as e:
            self.server.logger.error(f"JSON解析失败: {e}")
        except Exception as e:
            self.server.logger.error(f"消息处理失败: {e}", exc_info=True)
