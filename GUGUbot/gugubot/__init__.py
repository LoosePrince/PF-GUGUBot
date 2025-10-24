# -*- coding: utf-8 -*-
#+---------------------------------------------------------------------+
from pathlib import Path

# from gugubot.logic.bot_core import GUGUBotCore
from gugubot.connector import ConnectorManager, MCConnector, QQWebSocketConnector, TestConnector, BridgeConnector
from gugubot.logic.system import BanWordSystem, BoundSystem, EchoSystem, KeyWordSystem, SystemManager
from gugubot.logic.system.whitelist import WhitelistSystem
from gugubot.config.BotConfig import BotConfig

from mcdreforged.api.types import PluginServerInterface, Info
from mcdreforged.api.command import *

mc_connector: MCConnector = None
gugubot_config: BotConfig = None

#+---------------------------------------------------------------------+
async def on_load(server: PluginServerInterface, old)->None:
    global qq_bot, connector_manager
    global mc_connector, gugubot_config

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

    # 注册系统管理器
    system_manager = SystemManager(server, connector_manager=connector_manager, config=gugubot_config)
    systems = [EchoSystem()]
    if is_main_server:
        systems.insert(0, BanWordSystem(server))
        systems.insert(1, KeyWordSystem(server))

        whitelist_system = WhitelistSystem(server)
        bound_system = BoundSystem(server)

        # 设置白名单系统引用
        bound_system.set_whitelist_system(whitelist_system)

        systems.insert(1, bound_system)
        systems.insert(1, whitelist_system)
    
    for system in systems:
        system_manager.register_system(system)
    
    connector_manager.register_system_manager(system_manager)

    # # 注册指令
    # server.register_command(
    #     Literal('!!klist').runs(qq_bot.ingame_key_list)
    # )
    # server.register_command(
    #     Literal('!!qq').
    #         then(
    #             GreedyText('message').runs(qq_bot.ingame_command_qq)
    #         )
    # )
    # server.register_command(
    #     Literal('@').then(
    #         Text('QQ(name/id)').suggests(lambda: qq_bot.suggestion).then(
    #             GreedyText('message').runs(qq_bot.ingame_at)
    #         )
    #     )
    # )
    # # 注册帮助消息
    # server.register_help_message('!!klist','显示游戏内关键词')
    # server.register_help_message('!!qq <msg>', '向QQ群发送消息(可以触发qq关键词)')
    # server.register_help_message('!!add <关键词> <回复>','添加游戏内关键词回复')
    # server.register_help_message('!!del <关键词>','删除指定游戏关键词')
    # server.register_help_message('@ <QQ名/号> <消息>','让机器人在qq里@')
    # # 注册监听任务
    # server.register_event_listener("PlayerAdvancementEvent", qq_bot.on_mc_achievement)
    # server.register_event_listener("PlayerDeathEvent", qq_bot.on_mc_death)

    # # 检查插件版本
    # async def check_plugin_version():
    #     try:
    #         response = requests.get("https://api.github.com/repos/LoosePrince/PF-GUGUBot/releases/latest")
    #         if response.status_code != 200:
    #             server.logger.warning(f"无法检查插件版本，网络代码: {response.status_code}")
    #             return
    #         latest_version = response.json()["tag_name"].replace('v', '')
    #         current_version = str(server.get_self_metadata().version)
    #         if latest_version > current_version:
    #             server.logger.info(f"§e[PF-GUGUBot] §6有新版本可用: §b{latest_version}§6，当前版本: §b{current_version}")
    #             server.logger.info("§e[PF-GUGUBot] §6请使用 §b!!MCDR plugin install -U -y gugubot §6来更新插件")
    #         else:
    #             server.logger.info(f"§e[PF-GUGUBot] §6已是最新版本: §b{current_version}")
    #     except Exception as e:
    #         server.logger.warning(f"检查插件版本时出错: {e}")

    # # 在插件加载完成后异步检查版本
    # server.schedule_task(check_plugin_version())

#+---------------------------------------------------------------------+
# # 防止初始化报错
# qq_bot = None

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