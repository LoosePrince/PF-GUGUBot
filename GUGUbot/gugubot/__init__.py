# -*- coding: utf-8 -*-
#+---------------------------------------------------------------------+
import re
import os
import sys

# GUGUbot加入系统路径
gugu_dir = os.path.dirname(__file__)[:-7] # remove \gugubot
sys.path.append(gugu_dir)  if gugu_dir not in sys.path  else None

from .bot import qbot
from data.text import style, DEFAULT_CONFIG
from mcdreforged.api.types import PluginServerInterface, Info
from mcdreforged.api.command import *
from .table import table
import pygame
#+---------------------------------------------------------------------+
def on_load(server: PluginServerInterface, old)->None:
    # 设置系统路径
    set_sys_path()
    global host, port, past_bot, past_info, event_loop
    global qq_bot
    # 获取参数，绑定列表
    config = table("./config/GUGUBot/config.json", DEFAULT_CONFIG, yaml=True)
    data = table("./config/GUGUBot/GUGUBot.json")
    # 获取QQ机器人信息
    host = server.get_plugin_instance('cool_q_api').get_config()['api_host']
    port = server.get_plugin_instance('cool_q_api').get_config()['api_port']
    # 命令前缀判断
    coolQ_command_prefix = server.get_plugin_instance('cool_q_api').get_config()['command_prefix']
    if coolQ_command_prefix != config['command_prefix']:
        server.logger.warning(f"CoolQAPI与gugubot所用command_prefix不一致，可能导致功能紊乱！CoolQ: {coolQ_command_prefix} vs gugubot: {config['command_prefix']}")
    # 继承重载前参数
    if old is not None and hasattr(old, 'past_bot') and \
       old is not None and hasattr(old, 'past_info'):
        past_info = old.past_info
        past_bot = old.past_bot
    else:
        past_bot = False
    # gugubot主体
    qq_bot = qbot(server, config, data, host, port)

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
    server.register_event_listener('cool_q_api.on_qq_info', qq_bot.on_qq_command)
    server.register_event_listener('cool_q_api.on_qq_info', qq_bot.send_msg_to_mc)
    server.register_event_listener('cool_q_api.on_qq_apply', qq_bot.on_qq_request)
    server.register_event_listener('cool_q_api.on_qq_notice', qq_bot.notification)

#+---------------------------------------------------------------------+
# 防止初始化报错
qq_bot = None

# 更新机器人名字 <- 显示在线人数功能
def on_player_joined(server:PluginServerInterface, player:str, info:Info)->None:
    if qq_bot \
        and qq_bot.config["command"]["name"] \
        and past_bot:
        qq_bot.set_number_as_name(server, past_bot, past_info)

# 更新机器人名字 <- 显示在线人数功能
def on_player_left(server:PluginServerInterface, player:str)->None:
    if qq_bot \
        and qq_bot.config["command"]["name"] \
        and past_bot:
        qq_bot.set_number_as_name(server, past_bot,past_info)

# 离线玩家添加白名单功能
def on_info(server:PluginServerInterface, info:Info)->None:
    if qq_bot:
        qq_bot.add_offline_whitelist(server, info)

# mc游戏消息 -> QQ
def on_user_info(server:PluginServerInterface, info:Info)->None:
    if qq_bot:
        qq_bot.send_msg_to_qq(server, info)

# 卸载
def on_unload(server:PluginServerInterface)->None:
    try:
        pygame.quit()
    except:
        pass

# 开服
def on_server_startup(server:PluginServerInterface)->None:
    # 开服提示
    qq_bot.send_msg_to_all_qq(style[qq_bot.style]['server_start'])
    # 开服指令
    for _,command in qq_bot.start_command.data.items():
        # 执行指令
        server.execute(command)

# 设置系统路径
def set_sys_path()->None:
    file_dir = os.path.dirname(__file__)
    if file_dir not in sys.path:
        sys.path.append(file_dir)
#+---------------------------------------------------------------------+