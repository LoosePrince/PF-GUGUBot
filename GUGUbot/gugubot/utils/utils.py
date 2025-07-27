# -*- coding: utf-8 -*-
import asyncio
import html
import os
import re
import time
import types

from functools import partial
from pathlib import Path

import pygame

from mcdreforged.api.types import PluginServerInterface


# 解包字体，绑定图片
def packing_copy(server) -> None:
    def __copyFile(path, target_path):            
        if os.path.exists(target_path):
            return
        target_path = Path(target_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with server.open_bundled_file(path) as file_handler: # 从包内解包文件
            message = file_handler.read()
        with open(target_path, 'wb') as f:                        # 复制文件
            f.write(message)
    
    __copyFile("gugubot/data/config_default.yml", "./config/GUGUbot/config.yml")        # 默认设置
    __copyFile("gugubot/data/bound.jpg", "./config/GUGUbot/bound.jpg")        # 绑定图片
    __copyFile("gugubot/font/MicrosoftYaHei-01.ttf", "./config/GUGUbot/font/MicrosoftYaHei-01.ttf") # 默认字体

def is_valid_message(info, bot, config):
    condition = [
        not is_self(info, bot),                           # 不是机器人自己发的消息
        info.content,                                                 # 不是空内容
        not info.content.startswith(config['command_prefix']),        # 不是指令
        info.source_id in config.get('group_id', [])                 # 是指定群消息
    ]
    return all(condition) and (not is_robot(bot, info.source_id, info.user_id) \
            or config['forward'].get('forward_other_bot', False))      # 不是机器人/是机器人 + 转发机器人)

def is_valid_command_source(info, config) -> bool:
    return any([
        info.source_id in config.get('group_id', []),
        (config.get('admin_group_id') and info.source_id in config.get('admin_group_id')),
        info.source_id in config.get('admin_id', []),
        (config.get("friend_is_admin", False) and info.sub_type == "private")
    ])

def is_self(info, bot)->bool:
    bot_data = asyncio.run(bot.get_login_info())["data"]
    bot_qq_id = int(bot_data['user_id'])
    return info.user_id == bot_qq_id

# 判断是否是机器人
def is_robot(bot, group_id, user_id)->bool:
    user_info = asyncio.run(bot.get_group_member_info(group_id, user_id))
    if user_info and user_info.get('data', {}) and user_info.get('data', {}).get('is_robot', False):
        return True
    return False

def get_latest_group_notice(qq_bot, logger):
    group_notices = asyncio.run(qq_bot.bot._get_group_notice(qq_bot.config["group_id"][0]))

    if not group_notices:
        logger.warning("无法获取群公告，建议尝试增加 cq_qq_api 的 max_wait_time 参数")
        return ""
    if not group_notices['data']:
        logger.warning("无群公告可供展示")
        return ""

    latest_notice = max(group_notices['data'], key = lambda x: x['publish_time'])
    latest_notice_text = latest_notice['message']['text']

    # decoding \n, <, >
    latest_notice_text = html.unescape(latest_notice_text)

    return latest_notice_text

async def get_group_name(bot, group_id_list:list)->dict:
    group_name_dict = {}

    for group_id in group_id_list:
        respond = await bot.get_group_info(group_id)
        
        group_name_dict[group_id] = respond["data"]["group_name"] if respond else "QQ"
    
    return group_name_dict
    
def get_admin_id_list(bot, config):
    request_results = [bot.get_group_member_list_sync(admin_group_id)  for admin_group_id in config.get("admin_group_id", [])]
    request_data = [result.get('data', []) for result in request_results if result]
    admin_ids = {person['user_id'] for group_list in request_data for person in group_list if 'user_id' in person}

    return list(admin_ids) + config.get("admin_id", [])

#==================================================================#
#                      text2image Helper                           #
#==================================================================#

# 文字转图片函数，一定程度防止风控
def text2image(font, input_string: str) -> str:
    # 分割成行并渲染每行文字
    lines = input_string.split("\n")
    line_images = [font.render(text, True, (0, 0, 0), (255, 255, 255)) for text in lines]
    
    # 计算图片尺寸
    max_width = max(image.get_width() for image in line_images)
    total_height = len(lines) * 33
    
    # 创建图片表面并填充白色背景
    surface = pygame.Surface((max_width, total_height))
    surface.fill((255, 255, 255))
    
    # 将每行文字绘制到图片表面上
    for i, image in enumerate(line_images):
        surface.blit(image, (0, i * 33))
    
    # 确保输出目录存在
    output_dir = "./config/GUGUbot/image"
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成唯一的文件名并保存图片
    image_path = os.path.join(output_dir, f"{int(time.time())}.jpg")
    pygame.image.save(surface, image_path)
    
    return image_path

# 文字转图片-装饰器
def addTextToImage(func):
    def _newReply(font, font_limit: int, is_main_server, self, info, message: str, force_reply: bool = False):
        if not is_main_server and not force_reply:
            return 

        if font_limit > 0 and len(message.split("]")[-1]) >= font_limit:
            image_path = text2image(font, message)
            message = f"[CQ:image,file=file:///{os.path.abspath(image_path)}]"

        message_types = {
            'private': self.send_private_msg,
            'group': self.send_group_msg
        }
        send_func = message_types.get(info.message_type)
        if send_func:
            send_func(info.source_id, message)

        try:
            time.sleep(2)
            os.remove(image_path)
        except Exception:
            pass

    def _addTextToImage(self, server: PluginServerInterface, info, bot):
        font_limit = int(self.config["font_limit"])
        _newReplyWithFont = partial(_newReply, None if font_limit <= 0 else self.font, font_limit, self.is_main_server)
        bot.reply = types.MethodType(_newReplyWithFont, bot)
        return func(self, server, info, bot)

    return _addTextToImage


#==================================================================#
#                     list parser Helper                           #
#==================================================================#

def is_player(server, qbot, player_name):
    ip_logger = server.get_plugin_instance("player_ip_logger")

    if ip_logger:
        return ip_logger.is_player(player_name)
    elif qbot.data:
        return player_name in [name for i in qbot.data for name in i]
    else:
        return True


def parse_list_content(bound_list, server, content:str, use_rcon:bool = False) -> tuple[list[str], list[str]]:
    bound_list = {i for player_names in bound_list.values() for i in player_names}

    match_pattern = r"players online:(?: (.*)|(.+))"
    match_result = re.search(match_pattern, content)

    instance_list = []
    online_player_api = server.get_plugin_instance("online_player_api")
    if match_result:
        instance_list = match_result.group(1) or match_result.group(2)

        instance_list = [i.strip() for i in instance_list.split(", ") if i.strip()] if instance_list else []
        instance_list = [i.split(']')[-1].split('】')[-1].strip() for i in instance_list] # 针对 [123] 玩家 和 【123】玩家 这种人名
    elif not use_rcon and online_player_api: # 使用 online_player_api
        instance_list = online_player_api.get_player_list()
    elif "players online:" in content:
        server.logger.warning("无法解析多行返回，开启 rcon 或下载 online_player_api 来解析")
        server.logger.warning("下载命令: !!MCDR plugin install online_player_api")

    # 有人绑定 -> 识别假人
    ip_logger = server.get_plugin_instance("player_ip_logger")
    
    player_list = []
    bot_list = []

    for instance in instance_list:
        if (not ip_logger or (ip_logger and ip_logger.is_player(instance))) \
            and (not bound_list or (bound_list and instance in bound_list)):
            player_list.append(instance)
        else:
            bot_list.append(instance)

    return player_list, bot_list