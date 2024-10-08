# -*- coding: utf-8 -*-
#+---------------------------------------------------------------------+
import json
import os
import requests
import shutil
import sys

# GUGUbot加入系统路径
gugu_dir = os.path.dirname(__file__)[:-7] # remove \gugubot
sys.path.append(gugu_dir)  if gugu_dir not in sys.path  else None

from .bot import qbot
from .utils import get_style_template

from mcdreforged.api.types import PluginServerInterface, Info
from mcdreforged.api.command import *
import pygame
#+---------------------------------------------------------------------+
def on_load(server: PluginServerInterface, old)->None:
    # 设置系统路径
    set_sys_path()
    global past_bot, past_info
    global qq_bot

    # 获取接口机器人
    cq_qq_api_instance = server.get_plugin_instance("cq_qq_api")
    if cq_qq_api_instance is None:
        server.logger.error("~~ 未找到前置插件 ~~")
    cq_qq_api_bot = cq_qq_api_instance.get_bot()

    # 继承重载前参数
    if old is not None and hasattr(old, 'past_bot') and \
       old is not None and hasattr(old, 'past_info'):
        past_info = old.past_info
        past_bot = old.past_bot
    else:
        past_bot = False

    # 更新配置文件 -> 1.1.4 -> 1.1.5 config迁移
    temp_update_version(server)

    # gugubot主体
    qq_bot = qbot(server, cq_qq_api_bot)

    # 注册指令
    qq_bot.server.register_command(
        Literal('!!klist').runs(qq_bot.ingame_key_list)
    )
    qq_bot.server.register_command(
        Literal('!!qq').
            then(
                GreedyText('message').runs(qq_bot.ingame_command_qq)
            )
    )
    qq_bot.server.register_command(
        Literal('@').then(
            Text('QQ(name/id)').suggests(lambda: qq_bot.suggestion).then(
                GreedyText('message').runs(qq_bot.ingame_at)
            )
        )
    )
    # 注册帮助消息
    server.register_help_message('!!klist','显示游戏内关键词')
    server.register_help_message('!!qq <msg>', '向QQ群发送消息(可以触发qq关键词)')
    server.register_help_message('!!add <关键词> <回复>','添加游戏内关键词回复')
    server.register_help_message('!!del <关键词>','删除指定游戏关键词')
    server.register_help_message('@ <QQ名/号> <消息>','让机器人在qq里@')
    # 注册监听任务
    server.register_event_listener('cq_qq_api.on_qq_command', qq_bot.on_qq_command)
    server.register_event_listener('cq_qq_api.on_qq_message', qq_bot.send_msg_to_mc)
    server.register_event_listener('cq_qq_api.on_qq_request', qq_bot.on_qq_request)
    server.register_event_listener('cq_qq_api.on_qq_notice', qq_bot.notification)

    # 检查插件版本
    def check_plugin_version():
        try:
            response = requests.get("https://api.github.com/repos/LoosePrince/PF-GUGUBot/releases/latest")
            if response.status_code != 200:
                server.logger.warning(f"无法检查插件版本，网络代码: {response.status_code}")
                return
            latest_version = response.json()["tag_name"].replace('v', '')
            current_version = str(server.get_self_metadata().version)
            if latest_version > current_version:
                server.logger.info(f"§e[PF-GUGUBot] §6有新版本可用: §b{latest_version}§6，当前版本: §b{current_version}")
                server.logger.info("§e[PF-GUGUBot] §6请使用 §b!!MCDR plugin install -U -y gugubot §6来更新插件")
            else:
                server.logger.info(f"§e[PF-GUGUBot] §6已是最新版本: §b{current_version}")
        except Exception as e:
            server.logger.warning(f"检查插件版本时出错: {e}")

    # 在插件加载完成后异步检查版本
    server.schedule_task(check_plugin_version)

#+---------------------------------------------------------------------+
# 防止初始化报错
qq_bot = None

# 更新机器人名字 <- 显示在线人数功能
def on_player_joined(server:PluginServerInterface, player:str, info:Info)->None:
    if isinstance(qq_bot, qbot) and qq_bot.config["command"]["name"]:
        qq_bot.set_number_as_name(server)
        
    # if isinstance(qq_bot, qbot) and qq_bot.config["forward"].get("player_notice", False):
    #     qq_bot.send_msg_to_all_qq(get_style_template('player_notice_join', qq_bot.style).format(player))

# 更新机器人名字 <- 显示在线人数功能
# 对违规名字无效
# def on_player_left(server:PluginServerInterface, player:str)->None:
#     if isinstance(qq_bot, qbot) and qq_bot.config["command"]["name"]:
#         qq_bot.set_number_as_name(server)

# 离线玩家添加白名单功能
def on_info(server:PluginServerInterface, info:Info)->None:
    if isinstance(qq_bot, qbot):
        qq_bot.add_offline_whitelist(server, info)

        # list function
        while "players online:" in info.content and qq_bot._list_callback:
            func = qq_bot._list_callback.pop()
            func(info.content)

        # 更新机器人名字 <- 显示在线人数功能
        if ("logged in with entity id" in info.content or "lost connection:" in info.content) and qq_bot.config["command"]["name"]:
            qq_bot.set_number_as_name(server)

        # 玩家上线通知
        if "logged in with entity id" in info.content and qq_bot.config["forward"].get("player_notice", False):
            player_name = info.content.split(" logged in with entity id")[0].split("[")[:-1]
            player_name = "[".join(player_name)
            qq_bot.send_msg_to_all_qq(get_style_template('player_notice_join', qq_bot.style).format(player_name))

        # 玩家下线通知
        if "left the game" in info.content and qq_bot.config["forward"].get("player_notice", False):
            player_name = info.content.replace("left the game", "").strip()
            qq_bot.send_msg_to_all_qq(get_style_template('player_notice_leave', qq_bot.style).format(player_name))

# mc游戏消息 -> QQ
def on_user_info(server:PluginServerInterface, info:Info)->None:
    if isinstance(qq_bot, qbot):
        qq_bot.send_msg_to_qq(server, info)

# 卸载
def on_unload(server:PluginServerInterface)->None:
    try:
        pygame.quit()
    except:
        pass

# 开服
def on_server_startup(server:PluginServerInterface)->None:
    if isinstance(qq_bot, qbot):
        # 开服提示
        qq_bot.send_msg_to_all_qq(get_style_template('server_start', qq_bot.style))
        # 开服指令
        for _,command in qq_bot.start_command.data.items():
            # 执行指令
            server.execute(command)

# 关服
def on_server_stop(server: PluginServerInterface, server_return_code: int)->None:
    if isinstance(qq_bot, qbot):
        # 关服提示
        qq_bot.send_msg_to_all_qq(get_style_template('server_stop', qq_bot.style))

# 设置系统路径
def set_sys_path()->None:
    file_dir = os.path.dirname(__file__)
    if file_dir not in sys.path:
        sys.path.append(file_dir)
#+---------------------------------------------------------------------+
def temp_update_version(server:PluginServerInterface)->None:
    config_dir = "./config/GUGUbot"
    old_config_dir = "./config/GUGUBot"
    
    files_to_check = ["config.json", "GUGUbot.json"]
    
    for file in files_to_check:
        new_path = os.path.join(config_dir, file)
        old_path = os.path.join(old_config_dir, file)
        
        if not os.path.exists(new_path) and os.path.exists(old_path):
            try:
                os.makedirs(config_dir, exist_ok=True)
                shutil.copy2(old_path, new_path)
                server.logger.info(f"Copied {file} from {old_config_dir} to {config_dir}")
            except Exception as e:
                server.logger.error(f"Error copying {file}: {str(e)}")
