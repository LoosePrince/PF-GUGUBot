# -*- coding: utf-8 -*-
"""不活跃用户检查插件模块。

该模块提供检查QQ绑定玩家长期未登录游戏的功能，支持定时自动检查和手动命令触发。
"""

import asyncio
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from mcdreforged.api.types import PluginServerInterface

from gugubot.builder import MessageBuilder
from gugubot.config import BasicConfig
from gugubot.logic.system.basic_system import BasicSystem
from gugubot.utils.types import BoardcastInfo


class InactiveCheckSystem(BasicConfig, BasicSystem):
    """不活跃用户检查系统，用于检查和提醒QQ绑定玩家长期未登录。
    
    提供定时自动检查和手动触发检查功能。
    """

    def __init__(self, server: PluginServerInterface, config=None) -> None:
        """初始化不活跃用户检查系统。"""
        BasicSystem.__init__(self, "inactive_check", enable=False, config=config)
        self.server = server
        
        # 设置数据文件路径
        data_path = Path(server.get_data_folder()) / "plugins" / "inactive_check.json"
        data_path.parent.mkdir(parents=True, exist_ok=True)
        BasicConfig.__init__(self, data_path)
        
        # 系统依赖
        self.bound_system = None
        self.qq_connector = None
        self.whitelist_system = None
        self.active_whitelist_system = None  # 活跃白名单系统，用于过滤玩家
        
        # 检查状态
        self._checking = False
        self._schedule_task_running = True  # 控制定时任务的运行

    def initialize(self) -> None:
        """初始化系统，加载配置等"""
        # 从配置文件加载数据
        self.load()
        
        # 如果没有上次检查时间，初始化为0
        if "last_check_time" not in self:
            self["last_check_time"] = 0
            self.save()
        
        last_check_time = self.get("last_check_time", 0)
        if last_check_time > 0:
            last_check_str = datetime.fromtimestamp(last_check_time).strftime('%Y-%m-%d %H:%M:%S')
            self.logger.info(f"不活跃检查系统已加载，上次检查时间: {last_check_str}")
        else:
            self.logger.info("不活跃检查系统已加载，尚未进行过检查")
        
        # 启动定时检查任务
        self.server.schedule_task(self._schedule_check())

    def set_bound_system(self, bound_system) -> None:
        """设置绑定系统引用"""
        self.bound_system = bound_system

    def set_qq_connector(self, qq_connector) -> None:
        """设置QQ连接器引用"""
        self.qq_connector = qq_connector

    def set_whitelist_system(self, whitelist_system) -> None:
        """设置白名单系统引用"""
        self.whitelist_system = whitelist_system

    def set_active_whitelist_system(self, active_whitelist_system) -> None:
        """设置活跃白名单系统引用"""
        self.active_whitelist_system = active_whitelist_system

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
        if not self.enable:
            return False

        if self.is_command(boardcast_info):
            return await self._handle_command(boardcast_info)

        return False

    async def _handle_command(self, boardcast_info: BoardcastInfo) -> bool:
        """处理不活跃检查相关命令"""

        if not boardcast_info.is_admin:
            return False

        command = boardcast_info.message[0].get("data", {}).get("text", "")
        command_prefix = self.config.get("GUGUBot", {}).get("command_prefix", "#")
        system_name = self.get_tr("name")

        command = command.replace(command_prefix, "", 1).strip()

        valid_commands = [system_name, self.get_tr("check"), self.get_tr("next")]
        if not any(command.startswith(i) for i in valid_commands):
            return False
        
        command = command.replace(system_name, "", 1).strip()
        
        if command.startswith(self.get_tr("check")):
            return await self._handle_check(boardcast_info)
        elif command.startswith(self.get_tr("next")):
            return await self._handle_next(boardcast_info)
        
        return await self._handle_help(boardcast_info)

    async def _handle_check(self, boardcast_info: BoardcastInfo) -> bool:
        """处理手动检查命令（仅管理员）"""
        # 检查是否正在检查中
        if self._checking:
            await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("checking"))])
            return True
        
        # 检查依赖
        if not self.qq_connector:
            await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("qq_connector_not_found"))])
            return True
        
        if not self.bound_system:
            await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("bound_system_not_found"))])
            return True
        
        if not self.whitelist_system or not self.whitelist_system._api:
            await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("whitelist_not_found"))])
            return True
        
        # 开始检查
        await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("check_start"))])
        
        # 执行检查
        inactive_players_dict = await self._check_inactive_players()
        
        # 发送通知
        if inactive_players_dict:
            await self._send_notification(inactive_players_dict)
            
            # 统计总数（包括不活跃和从未进入游戏的玩家）
            total_inactive = sum(len(data.get("inactive", [])) for data in inactive_players_dict.values())
            total_never_played = sum(len(data.get("never_played", [])) for data in inactive_players_dict.values())
            total_count = total_inactive + total_never_played
            
            await self.reply(boardcast_info, [
                MessageBuilder.text(self.get_tr(
                    "check_complete", 
                    total_count=total_count,
                    inactive_count=total_inactive,
                    never_played_count=total_never_played
                ))
            ])
        else:
            await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("no_inactive_players"))])
        
        await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr("manual_check_success"))])
        return True

    async def _handle_next(self, boardcast_info: BoardcastInfo) -> bool:
        """处理查看下次检查时间命令"""
        last_check_time = self.get("last_check_time", 0)
        check_interval = self.config.get_keys(["system", "inactive_check", "check_interval"], 86400)
        next_check_time = last_check_time + check_interval
        
        next_check_str = datetime.fromtimestamp(next_check_time).strftime('%Y-%m-%d %H:%M:%S')
        await self.reply(boardcast_info, [
            MessageBuilder.text(self.get_tr("next_check_time", time=next_check_str))
        ])
        return True

    async def _handle_help(self, boardcast_info: BoardcastInfo) -> bool:
        """不活跃检查指令帮助"""
        command_prefix = self.config.get("GUGUBot", {}).get("command_prefix", "#")
        system_name = self.get_tr("name")
        enable_cmd = self.get_tr("gugubot.enable", global_key=True)
        disable_cmd = self.get_tr("gugubot.disable", global_key=True)
        check_cmd = self.get_tr("check")
        next_cmd = self.get_tr("next")
        
        help_msg = self.get_tr(
            "help_msg",
            command_prefix=command_prefix,
            name=system_name,
            enable=enable_cmd,
            disable=disable_cmd,
            check=check_cmd,
            next=next_cmd
        )
        await self.reply(boardcast_info, [MessageBuilder.text(help_msg)])
        return True

    def _get_player_uuid(self, player_name: str) -> Optional[str]:
        """通过玩家名获取UUID
        
        Parameters
        ----------
        player_name : str
            玩家名
            
        Returns
        -------
        Optional[str]
            玩家UUID，如果未找到则返回None
        """
        if not self.whitelist_system or not self.whitelist_system._api:
            return None
        
        try:
            whitelist = self.whitelist_system._api.get_whitelist()
            for player_info in whitelist:
                if player_info.name.lower() == player_name.lower():
                    return player_info.uuid
        except Exception as e:
            self.logger.error(f"获取玩家 {player_name} 的UUID失败: {e}")
        
        return None

    async def _check_inactive_players(self) -> Dict[int, Dict[str, List[Dict]]]:
        """检查不活跃玩家的核心逻辑
        
        Returns
        -------
        Dict[int, Dict[str, List[Dict]]]
            字典，key为群号，value为包含 'inactive' 和 'never_played' 两个键的字典
            'inactive': 进过游戏但长时间未登录的玩家列表
            'never_played': 已绑定但从未进入游戏的玩家列表
        """
        self._checking = True
        inactive_players_dict = {}
        
        try:
            # 获取配置
            group_ids = self.config.get_keys(["connector", "QQ", "permissions", "group_ids"], [])
            inactive_days = self.config.get_keys(["system", "inactive_check", "inactive_days"], 30)
            never_played_days = self.config.get_keys(["system", "inactive_check", "never_played_days"], 7)
            inactive_seconds = inactive_days * 86400
            never_played_seconds = never_played_days * 86400
            current_time = time.time()
            QQ_connector_name = self.config.get_keys(["connector", "QQ", "source_name"], "QQ")
            
            # 获取playerdata目录
            player_data_dir = Path("server/world/playerdata")
            
            if not player_data_dir.exists():
                self.logger.warning(f"playerdata目录不存在: {player_data_dir}")
                return {}
            
            # 获取所有玩家
            all_players = self.bound_system.player_manager.get_all_players()
            
            # 遍历每个群，收集该群的不活跃玩家
            for group_id in group_ids:
                inactive_players = []  # 进过游戏但长时间未登录的玩家
                never_played_players = []  # 从未进入游戏的玩家
                
                # 先获取该群的成员列表（避免重复调用API）
                group_members = {}  # key: user_id, value: member info (包含join_time)
                try:
                    member_list_result = await self.qq_connector.bot.get_group_member_list(group_id=int(group_id))
                    if member_list_result and member_list_result.get("status") == "ok":
                        members = member_list_result.get("data", [])
                        for member in members:
                            user_id = str(member.get("user_id", ""))
                            if user_id:
                                group_members[user_id] = member
                except Exception as e:
                    self.logger.error(f"获取群 {group_id} 成员列表失败: {e}")
                    continue
                
                # 检查每个玩家
                for player in all_players:
                    # 只检查有QQ绑定的玩家
                    qq_accounts = player.accounts.get(QQ_connector_name, [])
                    if not qq_accounts:
                        continue
                    
                    # 检查玩家是否在活跃白名单中，如果是则跳过
                    if self.active_whitelist_system:
                        # 检查玩家的所有名称（Java和Bedrock）是否在活跃白名单中
                        player_names = player.java_name + player.bedrock_name
                        if any(self.active_whitelist_system.is_in_whitelist(name) for name in player_names):
                            self.logger.debug(f"玩家 {player.name} 在活跃白名单中，跳过不活跃检查")
                            continue
                    
                    # 检查该玩家是否在当前群，并获取进群时间
                    player_in_group = False
                    join_time = None
                    
                    # 检查玩家的任一QQ账号是否在该群
                    for qq_account in qq_accounts:
                        qq_str = str(qq_account)
                        if qq_str in group_members:
                            player_in_group = True
                            # 获取进群时间
                            join_time = group_members[qq_str].get("join_time", 0)
                            break
                    
                    if not player_in_group:
                        continue
                    
                    # 检查玩家的所有UUID对应的playerdata文件，找最新的修改时间
                    latest_mtime = 0
                    found_any_file = False
                    
                    for player_name in (player.java_name + player.bedrock_name):
                        uuid = self._get_player_uuid(player_name)
                        if uuid:
                            player_file = player_data_dir / f"{uuid}.dat"
                            if player_file.exists():
                                found_any_file = True
                                mtime = player_file.stat().st_mtime
                                latest_mtime = max(latest_mtime, mtime)
                    
                    # 区分两种情况
                    if not found_any_file:
                        # 从未进入过游戏，使用进群时间作为参考
                        # 如果有进群时间且超过阈值
                        if join_time and join_time > 0:
                            days_since_join = int((current_time - join_time) / 86400)
                            if (current_time - join_time) > never_played_seconds:
                                never_played_players.append({
                                    "player_name": player.name,
                                    "qq_accounts": qq_accounts,
                                    "days_since_bind": days_since_join
                                })
                                self.logger.debug(f"玩家 {player.name} 进群 {days_since_join} 天后仍未进入游戏")
                        else:
                            # 如果没有进群时间记录，也加入列表（向后兼容或无法获取进群时间的情况）
                            never_played_players.append({
                                "player_name": player.name,
                                "qq_accounts": qq_accounts,
                                "days_since_bind": None
                            })
                            self.logger.debug(f"玩家 {player.name} 已绑定但从未进入游戏（无进群时间记录）")
                    elif (current_time - latest_mtime) > inactive_seconds:
                        # 进过游戏但长时间未登录
                        days_inactive = int((current_time - latest_mtime) / 86400)
                        inactive_players.append({
                            "player_name": player.name,
                            "qq_accounts": qq_accounts,
                            "days_inactive": days_inactive
                        })
                        self.logger.debug(f"玩家 {player.name} 已不活跃 {days_inactive} 天")
                
                # 如果有任何不活跃玩家，保存到字典中
                if inactive_players or never_played_players:
                    inactive_players_dict[group_id] = {
                        "inactive": inactive_players,
                        "never_played": never_played_players
                    }
                    self.logger.info(
                        f"群 {group_id} 发现 {len(inactive_players)} 名不活跃玩家，"
                        f"{len(never_played_players)} 名从未进入游戏的玩家"
                    )
            
            # 更新最后检查时间
            self["last_check_time"] = int(current_time)
            self.save()
            
        except Exception as e:
            self.logger.error(f"检查不活跃玩家时出错: {e}\n{traceback.format_exc()}")
        finally:
            self._checking = False
        
        return inactive_players_dict

    async def _send_notification(self, inactive_players_dict: Dict[int, Dict[str, List[Dict]]]) -> None:
        """发送通知到配置的目标
        
        Parameters
        ----------
        inactive_players_dict : Dict[int, Dict[str, List[Dict]]]
            不活跃玩家字典，key为群号，value为包含 'inactive' 和 'never_played' 的字典
        """
        # 获取配置
        notify_targets = self.config.get_keys(["system", "inactive_check", "notify_targets"], {})
        admin_private = notify_targets.get("admin_private", True)
        admin_groups = notify_targets.get("admin_groups", True)
        origin_group = notify_targets.get("origin_group", False)
        
        inactive_days = self.config.get_keys(["system", "inactive_check", "inactive_days"], 30)
        
        # 构建通知消息
        for group_id, players_data in inactive_players_dict.items():
            try:
                inactive_players = players_data.get("inactive", [])
                never_played_players = players_data.get("never_played", [])
                
                # 如果两类玩家都没有，跳过
                if not inactive_players and not never_played_players:
                    continue
                
                # 获取群信息
                group_info_result = await self.qq_connector.bot.get_group_info(group_id=int(group_id))
                group_name = "未知群"
                if group_info_result and group_info_result.get("status") == "ok":
                    group_name = group_info_result.get("data", {}).get("group_name", "未知群")
                
                # 构建消息的各个部分
                notification_parts = [self.get_tr("notification_title")]
                
                # 1. 不活跃玩家部分
                if inactive_players:
                    player_list = []
                    for player in inactive_players:
                        qq_accounts_str = ", ".join(str(qq) for qq in player["qq_accounts"])
                        player_item = self.get_tr(
                            "player_item",
                            player_name=player["player_name"],
                            qq_accounts=qq_accounts_str,
                            days_inactive=player["days_inactive"]
                        )
                        player_list.append(player_item)
                    player_list_str = "\n".join(player_list)
                    
                    inactive_section = self.get_tr(
                        "notification_content",
                        group_name=group_name,
                        group_id=group_id,
                        count=len(inactive_players),
                        days=inactive_days,
                        player_list=player_list_str
                    )
                    notification_parts.append(inactive_section)
                
                # 2. 从未进入游戏玩家部分
                if never_played_players:
                    never_played_list = []
                    never_played_days_config = self.config.get_keys(["system", "inactive_check", "never_played_days"], 7)
                    for player in never_played_players:
                        qq_accounts_str = ", ".join(str(qq) for qq in player["qq_accounts"])
                        days_since_bind = player.get("days_since_bind")
                        
                        if days_since_bind is not None:
                            player_item = self.get_tr(
                                "never_played_player_item",
                                player_name=player["player_name"],
                                qq_accounts=qq_accounts_str,
                                days_since_bind=days_since_bind
                            )
                        else:
                            # 向后兼容：没有绑定时间记录的情况
                            player_item = self.get_tr(
                                "never_played_player_item_no_time",
                                player_name=player["player_name"],
                                qq_accounts=qq_accounts_str
                            )
                        never_played_list.append(player_item)
                    never_played_list_str = "\n".join(never_played_list)
                    
                    never_played_section = self.get_tr(
                        "never_played_content",
                        group_name=group_name,
                        group_id=group_id,
                        count=len(never_played_players),
                        days=never_played_days_config,
                        player_list=never_played_list_str
                    )
                    notification_parts.append(never_played_section)
                
                # 组合完整消息
                notification_msg = "\n\n".join(notification_parts)
                
                # 发送到私聊管理员
                if admin_private:
                    admin_ids = self.config.get_keys(["connector", "QQ", "permissions", "admin_ids"], [])
                    for admin_id in admin_ids:
                        if not admin_id:
                            continue
                        try:
                            await self.qq_connector.bot.send_private_msg(
                                user_id=int(admin_id),
                                message=[MessageBuilder.text(notification_msg)]
                            )
                        except Exception as e:
                            self.logger.error(f"发送私聊消息到管理员 {admin_id} 失败: {e}\n{traceback.format_exc()}")
                
                # 发送到管理群
                if admin_groups:
                    admin_group_ids = self.config.get_keys(["connector", "QQ", "permissions", "admin_group_ids"], [])
                    for admin_group_id in admin_group_ids:
                        if not admin_group_id:
                            continue
                        try:
                            await self.qq_connector.bot.send_group_msg(
                                group_id=int(admin_group_id),
                                message=[MessageBuilder.text(notification_msg)]
                            )
                        except Exception as e:
                            self.logger.error(f"发送消息到管理群 {admin_group_id} 失败: {e}\n{traceback.format_exc()}")
                
                # 发送到原群
                if origin_group:
                    try:
                        await self.qq_connector.bot.send_group_msg(
                            group_id=int(group_id),
                            message=[MessageBuilder.text(notification_msg)]
                        )
                    except Exception as e:
                        self.logger.error(f"发送消息到原群 {group_id} 失败: {e}\n{traceback.format_exc()}")
            
            except Exception as e:
                self.logger.error(f"发送通知时出错: {e}\n{traceback.format_exc()}")

    async def _schedule_check(self) -> None:
        """定时检查任务"""
        self.logger.info("不活跃检查定时任务已启动")
        
        while self._schedule_task_running:
            try:
                # 读取配置
                last_check_time = self.get("last_check_time", 0)
                check_interval = self.config.get_keys(["system", "inactive_check", "check_interval"], 86400)
                
                # 计算下次检查时间
                next_check_time = last_check_time + check_interval
                current_time = time.time()
                wait_time = max(0, next_check_time - current_time)
                
                # 记录下次检查时间
                if wait_time > 0:
                    next_check_str = datetime.fromtimestamp(next_check_time).strftime('%Y-%m-%d %H:%M:%S')
                    self.logger.debug(f"下次检查时间: {next_check_str}")
                
                # 等待到下次检查时间（分割成小段以便快速响应停止信号）
                while wait_time > 0 and self._schedule_task_running:
                    sleep_time = min(wait_time, 1.0)  # 每次最多睡眠1秒
                    await asyncio.sleep(sleep_time)
                    wait_time -= sleep_time

                if not self._schedule_task_running:
                    break
                
                # 检查系统是否已启用
                if not self.enable:
                    self.logger.debug("系统未启用，跳过本次检查")
                    # 更新检查时间，避免重复检查
                    self["last_check_time"] = int(time.time())
                    self.save()
                    continue
                
                # 检查依赖
                if not self.qq_connector or not self.bound_system or not self.whitelist_system:
                    self.logger.warning("依赖系统未初始化，跳过本次检查")
                    continue
                
                # 执行检查
                self.logger.info("开始定时检查不活跃玩家...")
                inactive_players_dict = await self._check_inactive_players()
                
                # 发送通知
                if inactive_players_dict:
                    await self._send_notification(inactive_players_dict)
                    total_inactive = sum(len(data.get("inactive", [])) for data in inactive_players_dict.values())
                    total_never_played = sum(len(data.get("never_played", [])) for data in inactive_players_dict.values())
                    self.logger.info(
                        f"定时检查完成，共发现 {total_inactive} 名不活跃玩家，"
                        f"{total_never_played} 名从未进入游戏的玩家"
                    )
                else:
                    self.logger.info("定时检查完成，所有玩家均活跃")
            
            except Exception as e:
                self.logger.error(f"定时检查任务出错: {e}\n{traceback.format_exc()}")
                # 出错后等待一段时间再继续（分割成小段以便快速响应停止信号）
                for _ in range(60):
                    if not self._schedule_task_running:
                        break
                    await asyncio.sleep(1.0)
        
        self.logger.info("不活跃检查定时任务已停止")

    def stop_schedule_task(self) -> None:
        """停止定时检查任务"""
        self._schedule_task_running = False
        self.logger.info("正在停止不活跃检查定时任务...")

