# -*- coding: utf-8 -*-
"""在线玩家列表查询系统。"""
import re
from typing import Optional, List

from mcdreforged.api.types import PluginServerInterface

from gugubot.builder import MessageBuilder
from gugubot.config.BotConfig import BotConfig
from gugubot.logic.system.basic_system import BasicSystem
from gugubot.utils.rcon_manager import RconManager
from gugubot.utils.types import BoardcastInfo, ProcessedInfo


class PlayerListSystem(BasicSystem):
    """在线玩家列表系统。"""

    def __init__(self, server: PluginServerInterface, config: Optional[BotConfig] = None) -> None:
        super().__init__("list", enable=True, config=config)
        self.server = server
        self.rcon_manager = RconManager(server)
        self.bridge_query_cmd = "bridge_list_query_internal_cmd"

    def initialize(self) -> None:
        self.logger.debug("在线玩家列表系统已初始化")

    async def process_boardcast_info(self, boardcast_info: BoardcastInfo) -> bool:
        if await self.handle_enable_disable(boardcast_info):
            return True

        if not self.is_command(boardcast_info):
            return False

        message = boardcast_info.message
        if not message or message[0].get("type") != "text":
            return False

        content = message[0].get("data", {}).get("text", "").strip()
        command_prefix = self.config.get("GUGUBot", {}).get("command_prefix", "#")
        
        command = content.replace(command_prefix, "", 1).strip()

        # 1. Check for internal bridge query command
        if command == self.bridge_query_cmd:
            await self._handle_list_command(boardcast_info, is_bridge_query=True)
            return True

        # 2. Check for normal user command
        # Get translation for command keywords
        list_cmd = self.get_tr("list")
        
        # Default trigger keywords
        triggers = ["player", "玩家", "在线", "online"]
        
        # Add translated keyword if valid
        if list_cmd and not list_cmd.startswith("gugubot.") and list_cmd not in triggers:
            triggers.append(list_cmd)
        
        if command in triggers:
            # Handle local query first
            await self._handle_list_command(boardcast_info, is_bridge_query=False)
            
            # Then broadcast to bridge if applicable
            await self._broadcast_query_to_bridge(boardcast_info)
            return True

        return False

    async def _handle_list_command(self, boardcast_info: BoardcastInfo, is_bridge_query: bool = False) -> None:
        try:
            server_name = self.config.get("GUGUBot", {}).get("server_name", "")
            if not server_name:
                # If server_name is not set in GUGUBot, try to get from bridge config or use default
                server_name = self.config.get_keys(["connector", "minecraft_bridge", "source_name"], "Server")
            
            prefix = f"[{server_name}] " if is_bridge_query else ""

            # Try using RCON first
            if self.server.is_rcon_running():
                result = self.server.rcon_query("list")
                
                # Parse and format the list result if configured
                formatted_result = self._format_player_list(result)

                if formatted_result:
                     await self.reply(boardcast_info, [MessageBuilder.text(f"{prefix}{formatted_result}")])
                     return

            # Fallback if RCON is not running
            self.logger.warning(self.get_tr('rcon_not_running'))
            await self.reply(boardcast_info, [MessageBuilder.text(f"{prefix}{self.get_tr('rcon_not_running')}")])

        except Exception as e:
             self.logger.error(f"Query player list failed: {e}")
             await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("query_failed", error=str(e)))])

    def _format_player_list(self, raw_result: str) -> str:
        """格式化玩家列表输出"""
        try:
            # 获取分隔符配置，默认为冒号和逗号
            # 支持用户在配置中自定义分隔符（支持正则表达式）
            colon_separator = self.config.get_keys(["system", "list", "colon_separator"], ":")
            comma_separator = self.config.get_keys(["system", "list", "comma_separator"], ",")
            
            players = self.parse_player_list(raw_result, colon_separator, comma_separator)
            
            if not players:
                # 如果解析不到玩家，可能是因为真的没玩家，也可能是格式不对
                # 如果原始消息包含"0"或者"empty"，我们假设它是空列表
                # 这里简单判断，如果是原版消息，空列表通常会说 0 players
                if " 0 " in raw_result or "0/" in raw_result:
                    return self.get_tr("list_empty")
                return raw_result
            
            # 排序玩家列表
            players.sort()
            
            # 格式化为带序号的列表
            players_list = [f"{i+1}. {p}" for i, p in enumerate(players)]
            formatted_players = "\n".join(players_list)
            
            # 格式化输出
            return self.get_tr("list_content", count=len(players), players="\n" + formatted_players)
            
        except Exception as e:
            self.logger.warning(f"Failed to format player list: {e}")
            return raw_result

    def parse_player_list(self, player_list: str, colon_separator: str = ":", comma_separator: str = ",") -> List[str]:
        """解析玩家列表字符串
        
        Args:
            player_list: 原始玩家列表字符串 (例如: "There are 2/20 players online: Player1, Player2")
            colon_separator: 冒号分隔符(正则)，用于分割前缀和玩家名单
            comma_separator: 逗号分隔符(正则)，用于分割玩家名
            
        Returns:
            List[str]: 解析出的玩家名列表
        """
        if not player_list:
            return []
            
        try:
            # 1. 通过冒号分割，获取后面的玩家部分
            # 使用正则分割
            parts = re.split(colon_separator, player_list)
            if len(parts) < 2:
                return []
                
            # 取最后一部分作为玩家列表（防止前缀中也有冒号）
            players_part = parts[-1].strip()
            
            if not players_part:
                return []
                
            # 2. 通过逗号分割玩家名
            # 使用正则分割，并过滤空字符串
            players = [p.strip() for p in re.split(comma_separator, players_part) if p.strip()]
            
            return players
            
        except Exception:
            return []

    async def _broadcast_query_to_bridge(self, boardcast_info: BoardcastInfo) -> None:
        """Broadcast query command to other servers via bridge."""
        try:
            # Check if bridge is enabled
            if not self.config.get_keys(["connector", "minecraft_bridge", "enable"], False):
                return

            # Check if bridge connector exists
            bridge_source = self.config.get_keys(["connector", "minecraft_bridge", "source_name"], "Bridge")
            bridge_connector = self.system_manager.connector_manager.get_connector(bridge_source)
            
            if not bridge_connector:
                return

            # Construct the internal query command
            command_prefix = self.config.get("GUGUBot", {}).get("command_prefix", "#")
            command_text = f"{command_prefix}{self.bridge_query_cmd}"

            # Construct ProcessedInfo
            # Note: We are sending a command to be executed by other servers' PlayerListSystem
            processed_info = ProcessedInfo(
                processed_message=[MessageBuilder.text(command_text)],
                source=boardcast_info.source,
                source_id=boardcast_info.source_id,
                sender=boardcast_info.sender,
                sender_id=boardcast_info.sender_id,
                raw=boardcast_info.raw,
                server=boardcast_info.server,
                logger=boardcast_info.logger,
                # We don't specify target to broadcast to all
            )

            # Broadcast via bridge
            # This will send the command to all connected clients (if server) or to server (if client)
            # The bridge connector on the other side will receive it, wrap it in BoardcastInfo, 
            # and pass it to SystemManager, which will dispatch it to PlayerListSystem.
            await self.system_manager.connector_manager.broadcast_processed_info(
                processed_info,
                include=[bridge_source]
            )
            
        except Exception as e:
            self.logger.error(f"Failed to broadcast list query to bridge: {e}")
