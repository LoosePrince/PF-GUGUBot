# -*- coding: utf-8 -*-
import asyncio

from typing import Dict, List, Optional, Union

from mcdreforged.api.types import PluginServerInterface

from gugubot.builder import MessageBuilder
from gugubot.config.BotConfig import BotConfig
from gugubot.logic.system.basic_system import BasicSystem
from gugubot.logic.system.whitelist import WhitelistSystem
from gugubot.utils.player_manager import PlayerManager, Player
from gugubot.utils.types import BoardcastInfo


class BoundSystem(BasicSystem):
    """绑定系统，用于管理QQ账号与游戏玩家的绑定关系。
    
    提供绑定、解绑、查询绑定信息等功能。
    """

    def __init__(self, server: PluginServerInterface, config: Optional[BotConfig] = None) -> None:
        """初始化绑定系统。"""
        super().__init__("bound", enable=False, config=config)
        self.server = server
        self.player_manager = PlayerManager(server, self)
        self.whitelist: Optional[WhitelistSystem] = None

    def initialize(self) -> None:
        """初始化系统，加载配置等"""
        self.player_manager.load()
        self.logger.debug(f"已加载 {len(self.player_manager.get_all_players())} 个玩家绑定信息")

    def set_whitelist_system(self, whitelist: WhitelistSystem) -> None:
        """设置白名单系统引用"""
        self.whitelist = whitelist

    async def process_boardcast_info(self, boardcast_info: BoardcastInfo) -> bool:
        """处理接收到的命令。

        Parameters
        ----------
        boardcast_info: BoardcastInfo
            广播信息，包含消息内容
        """
        message = boardcast_info.message

        if not message:
            return False
        
        first_message = message[0]
        
        if first_message.get("type") != "text":
            return False

        # 先检查是否是开启/关闭命令
        if await self.handle_enable_disable(boardcast_info):
            return True

        return await self._handle_msg(boardcast_info)

    async def _handle_msg(self, boardcast_info: BoardcastInfo) -> bool:
        """处理消息"""
        content = boardcast_info.message[0].get("data",{}).get("text", "")

        if self.is_command(boardcast_info):
            return await self._handle_command(boardcast_info)

        return False

    async def _handle_command(self, boardcast_info: BoardcastInfo) -> bool:
        """处理绑定相关命令"""
        command = boardcast_info.message[0].get("data",{}).get("text", "")
        command_prefix = self.config.get("GUGUBot", {}).get("command_prefix", "#")
        system_name = self.get_tr("name")

        command = command.replace(command_prefix, "", 1).strip()

        valid_commands = [system_name, self.get_tr("bind"), self.get_tr("unbind"), self.get_tr("list"), self.get_tr("search")]
        if not any(command.startswith(i) for i in valid_commands):
            return False
        
        command = command.replace(system_name, "", 1).strip()
        
        if command.strip() == "" and len(boardcast_info.message) == 1:
            return await self._handle_help(boardcast_info)
        elif command.startswith(self.get_tr("unbind")):
            return await self._handle_unbind(boardcast_info)
        elif command.startswith(self.get_tr("list")):
            return await self._handle_list(boardcast_info)
        
        return await self._handle_bind(boardcast_info)

    async def _handle_bind(self, boardcast_info: BoardcastInfo) -> bool:
        """处理绑定命令"""
        command = boardcast_info.message[0].get("data",{}).get("text", "")
        command_prefix = self.config.get("GUGUBot", {}).get("command_prefix", "#")
        system_name = self.get_tr("name")
        bind_cmd = self.get_tr("bind")

        for i in [command_prefix, system_name]:
            command = command.replace(i, "", 1).strip()

        if not command and len(boardcast_info.message) == 1:
            await self.reply(boardcast_info, [MessageBuilder.text(
                self.get_tr("bind_instruction", command_prefix=command_prefix, name=system_name, bind=bind_cmd)
            )])
            return True

        # 解析消息段
        source = boardcast_info.source
        target_id = boardcast_info.sender_id  # 默认绑定到发送者
        player_name = ""
        is_bedrock = False
        
        # 检查是否有@消息段，如果有就更新要绑定的平台账户
        for message_segment in boardcast_info.message:
            if message_segment.get("type") == "at":
                target_id = message_segment.get("data", {}).get("qq", boardcast_info.sender_id)
                break
        
        # 使用最后一个消息段来处理玩家名和基岩版标识
        last_text_message = [message for message in boardcast_info.message if message.get("type") == "text"][-1]
        last_text = last_text_message.get("data", {}).get("text", "")
        for i in [command_prefix, system_name]:
            last_text = last_text.replace(i, "", 1).strip()
        parts = last_text.split(maxsplit=1)
        if parts:
            player_name = parts[0]

        is_bedrock = is_offline = is_online = False
        if len(parts) > 1:
            is_bedrock = parts[1].lower() in ["bedrock", "基岩", "be"]
            is_offline = parts[1].lower() in ["offline", "离线", "off"]
            is_online = parts[1].lower() in ["online", "在线", "on"]

        if not player_name:
            await self.reply(boardcast_info, [MessageBuilder.text(
                self.get_tr("bind_instruction", command_prefix=command_prefix, name=system_name, bind=bind_cmd)
            )])
            return True

        # 检查是否达到绑定上限
        player = self.player_manager.get_player(target_id or player_name, platform=source)

        exceeded_platform_bound = exceeded_bedrock_bound = exceeded_java_bound = False
        if player:
            exceeded_platform_bound = len(player.accounts.get(source, [])) >= self.config.get("system", {}).get("bound", {}).get("max_platform_bound", 1)
            exceeded_bedrock_bound = len(player.bedrock_name) >= self.config.get("system", {}).get("bound", {}).get("max_bedrock_bound", 1)
            exceeded_java_bound = len(player.java_name) >= self.config.get("system", {}).get("bound", {}).get("max_java_bound", 1)

        # 到达所有绑定上限
        if player and exceeded_platform_bound and exceeded_bedrock_bound and exceeded_java_bound:
            await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("max_bound_reached"))])
            return True

        elif (not is_bedrock and exceeded_platform_bound and exceeded_java_bound) \
            or (is_bedrock and exceeded_platform_bound and exceeded_bedrock_bound):
            await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("max_bound_reached"))])
            return True

        # 直接执行绑定
        bound_result = await self._bind_player(boardcast_info, player_name, source, is_bedrock, is_offline, is_online, target_id)
        if bound_result:
            await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("bind_success"))])
        else:
            await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("bind_existed"))])

        return True


    async def _bind_player(self, boardcast_info: BoardcastInfo, player_name: str, platform: str, 
                           is_bedrock: bool=False, is_offline: bool=False, is_online: bool=False, 
                           target_id: str = None) -> bool:
        """执行玩家绑定"""
        try:
            # 如果用户未指定任何选项，则使用系统默认模式
            if not any([is_bedrock, is_online, is_offline]):
                is_offline = not self.whitelist.online_mode
                is_online = self.whitelist.online_mode
            
            # 检查玩家名是否已被其他用户绑定
            if self.player_manager.is_name_bound_by_other_user(player_name, target_id, platform):
                return False

            def _bound_whitelist(player_name: str, is_offline: bool, is_online: bool, is_bedrock: bool):
                if self.config.get("system", {}).get("bound", {}).get("whitelist_add_with_bound", False) and self.whitelist:
                    self.whitelist.add_player(
                        player_name,
                        force_offline=is_offline,
                        force_online=is_online,
                        force_bedrock=is_bedrock
                    )

            # 检查是否已存在该玩家
            existing_player = self.player_manager.get_player(target_id, platform=platform)
            if existing_player:
                if (is_bedrock and player_name not in existing_player.bedrock_name) \
                    or (not is_bedrock and player_name not in existing_player.java_name):
                    existing_player.add_name(player_name, is_bedrock)
                    self.player_manager.save()
                    _bound_whitelist(player_name, is_offline, is_online, is_bedrock)
                    return True

                elif player_name not in existing_player.accounts.get(platform, []):
                    existing_player.add_account(platform, target_id)
                    self.player_manager.save()
                    _bound_whitelist(player_name, is_offline, is_online, is_bedrock)
                    return True

                return False
            
            # 添加新玩家绑定
            self.player_manager.add_player_account(
                player_name, platform=platform, account_id=target_id, is_bedrock=is_bedrock
            )
            self.player_manager.save()
            _bound_whitelist(player_name, is_offline, is_online, is_bedrock)

            return True
        except Exception as e:
            self.logger.error(f"绑定玩家失败: {e}")
            return False

    async def _handle_unbind(self, boardcast_info: BoardcastInfo) -> bool:
        """处理解绑命令"""
        command = boardcast_info.message[0].get("data",{}).get("text", "")
        command_prefix = self.config.get("GUGUBot", {}).get("command_prefix", "#")
        system_name = self.get_tr("name")
        unbind_command = self.get_tr("unbind")

        for i in [command_prefix, system_name, unbind_command]:
            command = command.replace(i, "", 1).strip()

        if not command:
            # 解绑当前用户的所有绑定
            return await self._unbind_current_user(boardcast_info)
        else:
            # 检查是否是基岩版独立命令
            if command.lower() in ["bedrock", "基岩", "be"]:
                return await self._unbind_bedrock_only(boardcast_info)
            
            # 解析玩家名和基岩版参数
            parts = command.split(maxsplit=1)
            player_name = parts[0]
            is_bedrock = False
            
            if len(parts) > 1:
                is_bedrock = parts[1].lower() in ["bedrock", "基岩", "be"]
            
            # 解绑指定玩家
            return await self._unbind_specific_player(boardcast_info, player_name, is_bedrock)

    async def _unbind_current_user(self, boardcast_info: BoardcastInfo) -> bool:
        """解绑当前用户的Java版玩家名（默认行为）"""
        player = self.player_manager.get_player(str(boardcast_info.sender_id), platform=boardcast_info.source)
        if not player:
            await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("no_bindings"))])
            return True
        
        # 检查是否有Java版玩家名
        if not player.java_name:
            await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("no_bindings"))])
            return True
        
        # 从白名单中删除玩家名
        self._remove_from_whitelist(player.java_name)
        
        # 清空Java版玩家名列表
        player.java_name.clear()
        self.player_manager.save()
        await self._clean_bound(player, self.player_manager)
        await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("unbind_success"))])
        return True

    async def _unbind_bedrock_only(self, boardcast_info: BoardcastInfo) -> bool:
        """解绑当前用户的所有基岩版玩家名"""
        player = self.player_manager.get_player(boardcast_info.sender_id)
        if not player:
            await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("no_bindings"))])
            return True
        
        # 检查是否有基岩版玩家名
        if not player.bedrock_name:
            await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("no_bindings"))])
            return True
        
        # 从白名单中删除玩家名
        self._remove_from_whitelist(player.bedrock_name)
        
        # 清空基岩版玩家名列表
        player.bedrock_name.clear()
        self.player_manager.save()
        await self._clean_bound(player, self.player_manager)
        await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("unbind_success"))])
        return True

    async def _unbind_specific_player(self, boardcast_info: BoardcastInfo, player_name: str, is_bedrock: bool = False) -> bool:
        """解绑指定玩家"""
        player = self.player_manager.get_player(player_name)
        if not player:
            await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("player_not_found"))])
            return True
        
        is_admin = boardcast_info.is_admin
        # 检查是否是绑定玩家
        if not is_admin and boardcast_info.sender_id not in player.accounts.get(boardcast_info.source, []):
            await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("no_bindings"))])
            return True
        
        # 根据基岩版参数选择性解绑
        if is_bedrock:
            # 只解绑基岩版玩家名
            if player_name in player.bedrock_name:
                # 从白名单中删除玩家名
                self._remove_from_whitelist(player_name)
                
                player.bedrock_name.remove(player_name)
                await self._clean_bound(player, self.player_manager)
                await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("unbind_success"))])
                return True
            else:
                await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("player_not_found"))])
                return True
        else:
            # 只解绑Java版玩家名
            if player_name in player.java_name:
                # 从白名单中删除玩家名
                self._remove_from_whitelist(player_name)
                
                player.java_name.remove(player_name)
                await self._clean_bound(player, self.player_manager)
                await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("unbind_success"))])
                return True
            else:
                await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("player_not_found"))])
                return True

    def _remove_from_whitelist(self, player_names: Union[str, List[str]]) -> None:
        """从白名单中删除玩家名的辅助函数
        
        Parameters
        ----------
        player_names : Union[str, List[str]]
            要删除的玩家名，可以是单个字符串或字符串列表
        """
        if not self.config.get("system", {}).get("bound", {}).get("whitelist_remove_with_leave", False) or not self.whitelist:
            return
        
        # 统一转换为列表处理
        if isinstance(player_names, str):
            player_names = [player_names]
        
        for name in player_names:
            self.whitelist.remove_player(name)

    async def _clean_bound(self, player: Player, player_manager: PlayerManager) -> bool:
        """清理绑定"""
        if not player.java_name and not player.bedrock_name:
            player_manager.remove_player(player.name)

    async def _handle_list(self, boardcast_info: BoardcastInfo) -> bool:
        """处理显示绑定列表命令"""
        player = self.player_manager.get_player(boardcast_info.sender_id)
        if not player:
            await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("no_bindings"))])
            return True
        
        # 获取所有绑定的玩家名
        bound_players = []
        for platform, accounts in player.accounts.items():
            if platform == "qq":
                continue
            bound_players.extend(accounts)
        
        if not bound_players:
            await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("no_bindings"))])
            return True
        
        player_list = "\n".join(f"{i+1}. {name}" for i, name in enumerate(bound_players))
        await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("bind_list", player_list=player_list))])
        return True


    async def _handle_help(self, boardcast_info: BoardcastInfo) -> bool:
        """绑定指令帮助"""
        command_prefix = self.config.get("GUGUBot", {}).get("command_prefix", "#")
        system_name = self.get_tr("name")
        enable_cmd = self.get_tr("gugubot.enable", global_key=True)
        disable_cmd = self.get_tr("gugubot.disable", global_key=True)
        bind_cmd = self.get_tr("bind")
        unbind_cmd = self.get_tr("unbind")
        list_cmd = self.get_tr("list")
        help_msg = self.get_tr(
            "help_msg", 
            command_prefix=command_prefix, 
            name=system_name,
            enable=enable_cmd,
            disable=disable_cmd,
            bind=bind_cmd,
            unbind=unbind_cmd,
            list=list_cmd
        )
        await self.reply(boardcast_info, [MessageBuilder.text(help_msg)])
        return True

    def get_player_by_qq_id(self, qq_id: str) -> Optional[Player]:
        """通过QQ ID获取玩家信息"""
        return self.player_manager.get_player(qq_id)

    def get_player_by_name(self, player_name: str) -> Optional[Player]:
        """通过玩家名获取玩家信息"""
        return self.player_manager.get_player(player_name)
