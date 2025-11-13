import json
import time
import asyncio
from typing import Any, Dict, override

from mcdreforged.api.types import Info

from gugubot.builder import McMessageBuilder
from gugubot.connector.basic_connector import BasicConnector
from gugubot.config.BotConfig import BotConfig
from gugubot.utils.types import ProcessedInfo, BoardcastInfo
from gugubot.parser.mc_parser import MCParser
from gugubot.ws import WebSocketFactory

class BridgeConnector(BasicConnector):
    """桥接连接器，支持服务器模式和客户端模式
    
    根据配置中的is_main_server决定运行模式：
    - True: 启动WebSocket服务器，等待其他服务器连接
    - False: 作为客户端连接到主服务器
    """
    
    def __init__(self, server, config: BotConfig = None):
        source_name = config.get_keys(["connector", "minecraft_bridge", "source_name"], "Bridge")
        super().__init__(source=source_name, parser=MCParser, config=config)
        self.server = server
        
        # 存储日志前缀
        connector_basic_name = self.server.tr("gugubot.connector.name")
        self.log_prefix = f"[{connector_basic_name}{self.source}]"
        
        # 判断是否为服务器模式
        self.is_main_server = config.get_keys(["connector", "minecraft_bridge", "is_main_server"], True)
        
        # 获取配置
        self.reconnect = config.get_keys(["connector", "minecraft_bridge", "connection", "reconnect"], 5)
        self.ping_interval = config.get_keys(["connector", "minecraft_bridge", "connection", "ping_interval"], 20)
        self.ping_timeout = config.get_keys(["connector", "minecraft_bridge", "connection", "ping_timeout"], 10)
        self.use_ssl = config.get_keys(["connector", "minecraft_bridge", "connection", "use_ssl"], False)
        self.verify = config.get_keys(["connector", "minecraft_bridge", "connection", "verify"], True)
        self.ca_certs = config.get_keys(["connector", "minecraft_bridge", "connection", "ca_certs"], None)
        self.extra_sslopt = config.get_keys(["connector", "minecraft_bridge", "connection", "sslopt"], {})
        
        # 创建WebSocket实例
        self.ws_server = None
        self.ws_client = None

    @override
    async def connect(self) -> None:
        """建立连接"""
        if self.is_main_server:
            self._start_server()
        else:
            self._connect_to_server()

    def _start_server(self) -> None:
        """启动WebSocket服务器"""
        self.logger.info(f"{self.log_prefix} 正在启动桥接服务器")
        
        # 创建服务器并设置回调
        self.ws_server = WebSocketFactory.create_bridge_server(
            self.config,
            logger=self.logger
        )
        
        # 设置回调（在创建服务器后）
        self.ws_server._on_message_callback = self._handle_server_message
        self.ws_server._on_client_connect_callback = self._on_client_connect
        self.ws_server._on_client_disconnect_callback = self._on_client_disconnect
        
        # 启动服务器（守护线程）
        self.ws_server.start(daemon=True)
        
        self.logger.info(f"{self.log_prefix} 桥接服务器就绪 ~")

    def _connect_to_server(self) -> None:
        """连接到主服务器"""
        self.logger.info(f"{self.log_prefix} 正在连接到桥接服务器")
        
        # 创建客户端并设置回调
        self.ws_client = WebSocketFactory.create_bridge_client(
            self.config,
            logger=self.logger
        )
        
        # 设置回调
        self.ws_client._on_message_callback = self._handle_client_message
        self.ws_client._on_open_callback = self._on_client_open
        self.ws_client._on_error_callback = self._on_client_error
        self.ws_client._on_close_callback = self._on_client_close
        
        # 连接到服务器
        self.ws_client.connect(
            reconnect=self.reconnect,
            ping_interval=self.ping_interval,
            ping_timeout=self.ping_timeout,
            use_ssl=self.use_ssl,
            verify=self.verify,
            ca_certs=self.ca_certs,
            extra_sslopt=self.extra_sslopt,
            thread_name="[GUGUBot]Bridge_Client"
        )
        
        self.logger.info(f"{self.log_prefix} 连接线程已启动 ~")

    def _on_client_connect(self, client: Dict, server: Any) -> None:
        """新客户端连接到服务器时"""
        client_address = client.get('address') if client else 'unknown'
        self.logger.info(f"{self.log_prefix} 新桥接客户端连接: {client_address}")

    def _on_client_disconnect(self, client: Dict, server: Any) -> None:
        """客户端从服务器断开时"""
        client_address = client.get('address') if client else 'unknown'
        self.logger.info(f"{self.log_prefix} 桥接客户端断开: {client_address}")

    def _on_client_open(self, ws) -> None:
        """客户端连接建立时"""
        self.logger.info(f"{self.log_prefix} 连接成功 ~")

    def _on_client_error(self, ws, error: Exception) -> None:
        """客户端连接错误时"""
        self.logger.error(f"{self.log_prefix} 连接错误: {error}")

    def _on_client_close(self, ws, status_code: int, reason: str) -> None:
        """客户端连接关闭时"""
        self.logger.info(f"{self.log_prefix} 连接关闭: {status_code} - {reason}")

    def _handle_server_message(self, client: Dict, server: Any, message: str) -> None:
        """处理服务器端接收到的消息（同步方法）"""
        try:
            message_data = json.loads(message) if isinstance(message, str) else message
            
            # 广播消息给所有其他客户端（除了发送者）
            if self.ws_server and self.ws_server.get_client_count() > 1:
                # 添加来源标识
                message_data["bridge_source"] = client.get('address', ['unknown', 0])[0]
                
                # 广播给其他客户端
                for other_client in self.ws_server.get_clients():
                    if other_client['id'] != client['id']:
                        self.ws_server.send_message(other_client, message_data)
            
            # 处理消息并传递给本地系统
            asyncio.run(self._process_bridge_message(message_data))
            
        except Exception as e:
            self.logger.error(f"{self.log_prefix} 服务器消息处理失败: {e}")

    def _handle_client_message(self, ws, message: str) -> None:
        """处理客户端接收到的消息（同步方法）"""
        try:
            message_data = json.loads(message) if isinstance(message, str) else message 
            
            # 处理消息并传递给本地系统
            asyncio.run(self._process_bridge_message(message_data))
            
        except Exception as e:
            self.logger.error(f"{self.log_prefix} 客户端消息处理失败: {e}")

    async def _process_bridge_message(self, message_data: Dict) -> None:
        """处理桥接消息的实际逻辑"""
        try:
            # 解析消息类型和内容
            processed_message = message_data.get("processed_message", [])
            sender = message_data.get("sender", "System")
            sender_id = message_data.get("sender_id", None)
            source = message_data.get("source", "")
            source_id = message_data.get("source_id", "")
            server = self.server
            logger = self.logger
            raw = message_data.get("raw", message_data)
            target = message_data.get("target", {})
            is_admin = message_data.get("is_admin", False) or self._is_admin(sender_id)

            # 如果 target 存在且 self.source 不在 target 中，则不处理消息
            if target and self.source not in target:
                return

            processed_info = BoardcastInfo(
                event_type="message",
                event_sub_type="group",
                message=processed_message,
                sender=sender,
                sender_id=sender_id,
                source=source,  # 保留远程服务器的 source
                source_id=source_id,
                receiver_source=self.source,  # 本地接收消息的 connector 的 source
                raw=raw,
                server=server,
                logger=logger,
                is_admin=is_admin
            )

            await self.parser(self).system_manager.broadcast_command(processed_info)

        except Exception as e:
            self.logger.error(f"{self.log_prefix} 处理桥接消息失败: {e}")

    @override
    async def send_message(self, processed_info: ProcessedInfo) -> None:
        """发送消息"""
        if not self.enable:
            return
        
        message_data = {
            "sender": processed_info.sender or "System",
            "sender_id": processed_info.sender_id,
            "receiver": processed_info.receiver,
            "source": self.source,
            "source_id": processed_info.source_id,
            "raw": processed_info.raw,
            "processed_message": processed_info.processed_message,
            "target": processed_info.target,
            "is_admin": self._is_admin(processed_info.sender_id)
        }
        
        if self.is_main_server:
            # 服务器模式：广播给所有连接的客户端
            if self.ws_server and self.ws_server.is_running():
                count = self.ws_server.broadcast(message_data)
                self.logger.debug(f"{self.log_prefix} 广播消息给 {count} 个客户端")
        else:
            # 客户端模式：发送给服务器
            if self.ws_client and self.ws_client.is_connected():
                if self.ws_client.send(message_data):
                    self.logger.debug(f"{self.log_prefix} 发送消息到服务器")
                else:
                    self.logger.warning(f"{self.log_prefix} 发送消息失败")

    @override
    async def disconnect(self) -> None:
        """断开连接"""
        try:
            if self.is_main_server:
                # 关闭服务器
                if self.ws_server and self.ws_server.is_running():
                    self.ws_server.stop()
                self.logger.info(f"{self.log_prefix} 已断开 ~")
            else:
                # 关闭客户端连接
                if self.ws_client:
                    self.ws_client.disconnect()
                self.logger.info(f"{self.log_prefix} 已断开 ~")
        except Exception as e:
            self.logger.warning(f"{self.log_prefix} 断开连接时出错: {e}")

    @override
    async def on_message(self, raw: Any) -> BoardcastInfo:
        """处理接收到的消息"""
        if not self.enable:
            return None
        
        if self.parser:
            return await self.parser(self).parse(raw)
        return None

    def _is_admin(self, sender_id) -> bool:
        """检查是否是管理员"""
        bound_system = self.connector_manager.system_manager.get_system("bound")

        if not bound_system:
            return False

        player_manager = bound_system.player_manager
        return player_manager.is_admin(sender_id)