# -*- coding: utf-8 -*-
#+---------------------------------------------------------------------+
from pathlib import Path

# from gugubot.logic.bot_core import GUGUBotCore
from gugubot.connector import (
    ConnectorManager, MCConnector, QQWebSocketConnector, TestConnector, BridgeConnector
)
from gugubot.logic.system import (
    BanWordSystem, BoundSystem, BoundNoticeSystem, EchoSystem, GeneralHelpSystem, KeyWordSystem, 
    StartupCommandSystem, SystemManager, WhitelistSystem, StyleSystem
)
from gugubot.config import BotConfig
from gugubot.utils import check_plugin_version, StyleManager

from mcdreforged.api.types import PluginServerInterface, Info
from mcdreforged.api.command import *

connector_manager: ConnectorManager = None
mc_connector: MCConnector = None
gugubot_config: BotConfig = None
startup_command_system: StartupCommandSystem = None
style_manager: StyleManager = None

#+---------------------------------------------------------------------+
async def on_load(server: PluginServerInterface, old)->None:
    global connector_manager
    global mc_connector
    global gugubot_config
    global startup_command_system
    global style_manager

    gugubot_config = BotConfig(Path(server.get_data_folder()) / "config.yml")
    gugubot_config.addNewConfig(server)

    is_main_server = gugubot_config.get_keys(["connector", "minecraft_bridge", "is_main_server"], True)

    connector_manager = ConnectorManager(server, gugubot_config)

    mc_connector = MCConnector(server, gugubot_config)
    connectors = [
        mc_connector, 
        TestConnector(server, gugubot_config),
        BridgeConnector(server, gugubot_config)
    ]
    
    if is_main_server:
        connectors.append(QQWebSocketConnector(server, gugubot_config))
        
    for connector in connectors:
        await connector_manager.register_connector(connector)

    # 初始化风格管理器
    style_manager = StyleManager(server, gugubot_config)
    style_manager.scan_styles()

    # 注册系统管理器
    system_manager = SystemManager(server, connector_manager=connector_manager, config=gugubot_config)
    system_manager.style_manager = style_manager
    
    # 创建系统实例，enable状态在各系统__init__中从config自动读取
    systems = [EchoSystem(enable=True, config=gugubot_config)]
    
    if is_main_server:
        general_help_system = GeneralHelpSystem(server, config=gugubot_config)
        ban_word_system = BanWordSystem(server, config=gugubot_config)
        key_word_system = KeyWordSystem(server, config=gugubot_config)
        whitelist_system = WhitelistSystem(server, config=gugubot_config)
        bound_system = BoundSystem(server, config=gugubot_config)
        bound_notice_system = BoundNoticeSystem(config=gugubot_config)
        startup_command_system = StartupCommandSystem(server, config=gugubot_config)
        style_system = StyleSystem(server, style_manager, config=gugubot_config)

        # 设置白名单系统引用
        bound_system.set_whitelist_system(whitelist_system)
        # 设置绑定提醒系统对绑定系统的引用
        bound_notice_system.set_bound_system(bound_system)

        systems.insert(0, general_help_system)
        systems.insert(1, ban_word_system)
        systems.insert(2, bound_system)
        systems.insert(3, bound_notice_system)
        systems.insert(4, key_word_system)
        systems.insert(5, whitelist_system)
        systems.insert(6, startup_command_system)
        systems.insert(7, style_system)

    for system in systems:
        system_manager.register_system(system)
    
    connector_manager.register_system_manager(system_manager)

    # 检查插件版本
    server.schedule_task(check_plugin_version(server))

    # 注册帮助消息
    command_prefix = gugubot_config.get_keys(["GUGUBot", "command_prefix"], "#")
    help_name = server.tr("gugubot.system.general_help.name")
    main_help_msg = f"GUGUBot {help_name}"
    server.register_help_message(f'{command_prefix}{help_name}', main_help_msg)

    # # 注册监听任务
    from gugubot.logic.plugins.mg_event import create_on_mc_achievement, create_on_mc_death
    server.register_event_listener("PlayerAdvancementEvent", create_on_mc_achievement(gugubot_config, connector_manager))
    server.register_event_listener("PlayerDeathEvent", create_on_mc_death(gugubot_config, connector_manager))

#+---------------------------------------------------------------------+
# # 防止初始化报错
# qq_bot = None

from gugubot.logic.plugins.player_notice import create_on_player_join, create_on_player_left
async def on_info(server:PluginServerInterface, info:Info)->None:
    if connector_manager is not None:
        on_player_join = create_on_player_join(connector_manager, gugubot_config)
        on_player_left = create_on_player_left(connector_manager, gugubot_config)
        await on_player_join(server, info)
        await on_player_left(server, info)


# def on_info(server:PluginServerInterface, info:Info)->None:
#     # Why I don't use on_player_join & on_player_left?
#     # -> Some player with illegal name will not trigger the those events.

#     if not isinstance(qq_bot, GUGUBotCore) or not is_qq_connected(server):
#         return 

#     # player list
#     while ("players online:" in info.content or "：" in info.content) and\
#         qq_bot._list_callback:
#         func = qq_bot._list_callback.pop()
#         func(info.content)

#     is_player_login = "logged in with entity id" in info.content
#     is_player_left = "left the game" in info.content

#     if is_player_login:
#         _on_player_join(server, info)
    
#     if is_player_left:
#         _on_player_left(server, info)

#     # forward server msg
#     if qq_bot.config['forward']['mc_to_qq'] and \
#         "[Server]" in info.content:
#         qq_bot.send_msg_to_all_qq(info.content.replace("[Not Secure] ", "", 1))

# def _on_player_join(server:PluginServerInterface, info:Info):
#     # 机器人名字更新
#     if qq_bot.config["command"]["name"]:
#         qq_bot.set_number_as_name(server)
    
#     # 玩家上线通知
#     if qq_bot.config["forward"].get("player_notice", False):
#         player_name = info.content.split(" logged in with entity id")[0].split("[/")[0]

#         if (qq_bot.config['forward'].get("player_notice", False) and is_player(server, qq_bot, player_name)) or \
#             (qq_bot.config['forward'].get("bot_notice", False) and not is_player(server, qq_bot, player_name)):
            
#             qq_bot.send_msg_to_all_qq(get_style_template('player_notice_join').format(player=player_name))

#     # 玩家上线显示群公告
#     if qq_bot.config["forward"].get("show_group_notice", False):
#         player_name = "[".join(info.content.split(" logged in with entity id")[0].split("[")[:-1])
        
#         latest_notice = get_latest_group_notice(qq_bot, logger=server.logger)

#         if latest_notice:

#             latest_notice_json = {
#                 "text": f"群公告：{latest_notice}",
#                 "color": "gray",
#                 "italic": False
#             }
#             server.execute(f'tellraw {player_name} {json.dumps(latest_notice_json)}')

# def _on_player_left(server:PluginServerInterface, info:Info):
#     # 机器人名字更新
#     if qq_bot.config["command"]["name"]:
#         qq_bot.set_number_as_name(server)

#     # 玩家下线通知
#     if qq_bot.config["forward"].get("player_notice", False):
#         player_name = info.content.replace("left the game", "").strip()

#         if (qq_bot.config['forward'].get("player_notice", False) and is_player(server, qq_bot, player_name)) or \
#             (qq_bot.config['forward'].get("bot_notice", False) and not is_player(server, qq_bot, player_name)):

#             qq_bot.send_msg_to_all_qq(get_style_template('player_notice_leave').format(player=player_name))

async def on_user_info(server: PluginServerInterface, info: Info) -> None:
    if mc_connector is not None:
        await mc_connector.on_message(server, info)

# 卸载
async def on_unload(server:PluginServerInterface)->None:
    try:
        if connector_manager:
            await connector_manager.disconnect_all()
    except:
        pass

#+---------------------------------------------------------------------+
# 服务器启动和停止通知
from gugubot.logic.plugins import broadcast_server_start, broadcast_server_stop

async def on_server_startup(server: PluginServerInterface) -> None:
    """服务器启动时的回调函数。"""
    try:
        if startup_command_system:
            await startup_command_system.execute_all_commands()

        if connector_manager:
            # 广播服务器启动消息
            await broadcast_server_start(server, connector_manager, gugubot_config)
    except Exception as e:
        server.logger.error(f"[GUGUBot] 服务器启动通知失败: {e}")

async def on_server_stop(server: PluginServerInterface, server_return_code: int) -> None:
    """服务器停止时的回调函数。"""
    try:
        if connector_manager:
            # 广播服务器停止消息
            await broadcast_server_stop(server, connector_manager, gugubot_config)
    except Exception as e:
        server.logger.error(f"[GUGUBot] 服务器停止通知失败: {e}")
#+---------------------------------------------------------------------+