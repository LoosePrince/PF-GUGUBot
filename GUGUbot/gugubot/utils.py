# -*- coding: utf-8 -*-
import json
import os
import random
import re
import time
import types

from functools import partial

import pygame

from mcdreforged.api.types import PluginServerInterface

from .data.text import style, qq_face_name
from .table import table
#==================================================================#
#                         Style template                           #
#==================================================================#
def get_style()->dict:
    config = table("./config/GUGUbot/config.json", yaml=True)
    extra_style = read_extra_style(config['dict_address'].get('extra_style_path', ""))
    style.update(extra_style)
    return style

def read_extra_style(extra_style_path)->dict:
    if os.path.exists(extra_style_path):
        with open(extra_style_path, 'r', encoding='UTF-8') as f:
            extra_style = json.load(f)
        return extra_style
    return {}

def get_style_template(template_name:str, current_style:str)->str:
    style = get_style()
    style_template = style[current_style].get(template_name, None)
    normal_template = style['正常'][template_name]

    if style_template is not None \
        and style_template.count("{}") == normal_template.count("{}"):
        return style_template
    return normal_template

#==================================================================#
#                        Beautify message                          #
#==================================================================#
def process_json(match):
    json_data = match.group(1).replace('&#44;', ',').replace('&#91;', '[').replace('&#93;', ']')
    parsed_data = json.loads(json_data)
    desc = parsed_data.get('meta', {}).get('detail_1', {}).get('desc', '')
    group_notice = parsed_data.get('prompt', '')
    return ('[链接]' + desc) if desc else group_notice if group_notice else ''

def extract_url(match):
    cq_code = match.group(0)
    pattern = r'url=([^\s,\]]+)'
    pattern2 = r'file=([^\s,\]]+)'
    summary_pattern = r'summary=(?:&#91;)?(.*?)(?:&#93;)?,'
    url_match = re.search(pattern, cq_code)
    url_match2 = re.search(pattern2, cq_code)
    summary_match = re.search(summary_pattern, cq_code)
    summary_match = f"表情: {summary_match.group(1)}" if summary_match else '图片'
    if url_match:
        url = url_match.group(1)
        return f'[[CICode,url={re.sub("&amp;", "&", url)},name={summary_match}]]'
    if url_match2:
        url = url_match2.group(1)
        return f'[[CICode,url={re.sub("&amp;", "&", url)},name={summary_match}]]'
    return cq_code

def replace_emoji(match):
    emoji_id = match.group(1)
    emoji_display = qq_face_name.get(str(emoji_id))
    return f'[表情: {emoji_display}]' if emoji_display else '[表情]'

def beautify_message(content:str, keep_raw_image_link:bool=False)->str:
    content = re.sub(r'\[CQ:record,file=.*?\]', '[语音]', content)
    content = re.sub(r'\[CQ:video,file=.*?\]', '[视频]', content)
    content = re.sub(r'\[CQ:rps\]', '[猜拳]', content)
    content = re.sub(r'\[CQ:dice\]', '[掷骰子]', content)
    content = re.sub(r'\[CQ:shake\]', '[窗口抖动]', content)
    content = re.sub(r'\[CQ:poke,.*?\]', "[戳一戳]", content)
    content = re.sub(r'\[CQ:anonymous.*?\]', "[匿名消息]", content)
    content = re.sub(r'\[CQ:share,file=.*?\]', '[链接]', content)
    content = re.sub(r'\[CQ:contact,type=qq.*?\]', "[推荐好友]", content)
    content = re.sub(r'\[CQ:contact,type=group.*?\]', "[推荐群]", content)
    content = re.sub(r'\[CQ:location,.*?\]', "[推荐群]", content)
    content = re.sub(r'\[CQ:music,type=.*?\]', '[音乐]', content)
    content = re.sub(r'\[CQ:forward,id=.*?\]', '[转发消息]', content)
    content = re.sub(r'\[CQ:file(?:,.*?)*\]', '[文件]', content)
    content = re.sub(r'\[CQ:redbag,title=.*?\]', '[红包]', content)
    content = re.sub(r'\[CQ:markdown,content=.*?\]', '', content)
    
    content = content.replace('CQ:at,qq=', '@')

    # process emoji
    content = re.sub(r'\[CQ:face,id=(\d+?)\]', replace_emoji, content)

    # process json
    content = re.sub(r'\[CQ:json,.*?data=(\{[^,]*\}).*?\s*\]', process_json, content)

    # process image link
    if keep_raw_image_link:
        content = re.sub(r'\[CQ:image,.*?\]|\[CQ:mface,.*?\]', extract_url, content)
    else:
        content = re.sub(r'\[CQ:image,file=.*?\]', '[图片]', content)
        content = re.sub(r'\[CQ:mface,summary=(?:&#91;)?(.*?)(?:&#93;)?,.*?\]', r'[表情: \1]', content)

    return content

#==================================================================#
#                             Helper                               #
#==================================================================#
# 文字转图片-装饰器
def addTextToImage(func):
    def _newReply(font, font_limit: int, is_main_server, self, info, message: str, force_reply: bool = False):
        if not is_main_server and not force_reply:
            return 

        if font_limit >= 0 and len(message.split("]")[-1]) >= font_limit:
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
        _newReplyWithFont = partial(_newReply, self.font, int(self.config["font_limit"]), self.is_main_server)
        bot.reply = types.MethodType(_newReplyWithFont, bot)
        return func(self, server, info, bot)

    return _addTextToImage

def format_list_response(player_list, bot_list, player_status, server_status, style):
        respond = ""
        count = 0

        if player_status or server_status:
            respond += format_player_list(player_list, style)
            count += len(player_list)

        if not player_status:
            respond += format_bot_list(bot_list)
            count += len(bot_list)

        if count != 0:
            respond = get_style_template('player_list', style).format(
                count,
                '玩家' if player_status else '假人' if not server_status else '人员',
                '\n' + respond
            )
        elif count == 0:
            respond = get_style_template('no_player_ingame', style)

        return respond

def format_player_list(player_list, style):
    if player_list:
        return f"\n---玩家---\n" + '\n'.join(sorted(player_list))
    return get_style_template('no_player_ingame', style)

def format_bot_list(bot_list):
    if bot_list:
        return f"\n\n---假人---\n" + '\n'.join(sorted(bot_list))
    return '\n\n没有假人在线哦!'

def get_latest_group_notice(qq_bot, logger):
    group_notices = qq_bot.bot._get_group_notice(qq_bot.config["group_id"][0])

    if not group_notices:
        logger.warning("无法获取群公告，建议尝试增加 cq_qq_api 的 max_wait_time 参数")
    if not group_notices['data']:
        logger.warning("无群公告可供展示")

    latest_notice = max(group_notices['data'], key = lambda x: x['publish_time'])
    latest_notice_text = latest_notice['message']['text']

    return latest_notice_text

def is_valid_message(info, bot, config):
    condition = [
        info.content,                                                 # 不是空内容
        not info.content.startswith(config['command_prefix']),        # 不是指令
        info.source_id in config.get('group_id', []),                 # 是指定群消息
        not is_robot(bot, info.source_id, info.user_id)               # 不是机器人  
            or config['forward'].get('farward_other_bot', False)      # 是机器人 + 转发机器人
    ]
    return all(condition)

# 判断是否是机器人
def is_robot(bot, group_id, user_id)->bool:
    user_info = bot.get_group_member_info(group_id, user_id)
    if user_info and user_info.get('data', {}) and user_info.get('data', {}).get('is_robot', False):
        return True
    return False

# 读取白名单
def loading_whitelist(whitelist_path, logger)->None:
    try:
        with open(whitelist_path, 'r') as f:
            temp = json.load(f)
        whitelist = {i['uuid']:i['name'] for i in temp} # 解压白名单表
        return whitelist
    except Exception as e:
        logger.warning(f"读取白名单出错：{e}")           # debug信息
        return {}
    
# 生成随机6位数pin
def random_6_digit()->int:
    return random.randint(100000, 999999)

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