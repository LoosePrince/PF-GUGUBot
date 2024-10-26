# -*- coding: utf-8 -*-
#+----------------------------------------------------------------------+
import json
import os
import random
import re
import time

from collections import defaultdict
from pathlib import Path

import pygame

from mcdreforged.api.types import PluginServerInterface, Info
from mcdreforged.minecraft.rcon.rcon_connection import RconConnection
from ruamel.yaml import YAML

from .ban_word_system import ban_word_system
from .data.text import (
    admin_help_msg,
    bound_help,
    group_help_msg,
    ingame_key_word_help,
    name_help,
    shenhe_help,
    style_help,
    uuid_help,
    whitelist_help,
    mc2qq_template
)
from .key_word_system import key_word_system
from .start_command_system import start_command_system
from .table import table
from .utils import *

yaml = YAML()
yaml.preserve_quotes = True
#+----------------------------------------------------------------------+

class qbot_helper:
    # A helper class saves all the helper functions for internal usage.
    #===================================================================#
    #                         init functions                            #
    #===================================================================#
    def __init__(self, server, bot):
        """
        init function for qbot

        Args:
            server (mcdreforged.api.types.PluginServerInterface): The MCDR game interface.
            bot (cq_qq_api.bot): API class for QQ.
        """
        self.server = server
        self.bot = bot

        self._packing_copy()
        
        # read config & bound data
        self.config = table("./config/GUGUbot/config.json", yaml=True)
        self.data = table("./config/GUGUbot/GUGUbot.json")

        self.server_name = self.config.data.get("server_name")
        self.server_name = self.server_name if self.server_name else ""
        self.is_main_server = self.config.data.get("is_main_server", True)
        self.style = self.config.data.get("style") if self.config.data.get("style") != "" else "正常"
        # init params
        self.picture_record_dict = {}
        self.shenhe = defaultdict(list)
        self.member_dict = None
        self.suggestion = self._ingame_at_suggestion()
        
        pygame.init()              # for text to image
        self._loading_dicts()      # read data for qqbot functions
        self._add_missing_config() # Add missing config
        self._loading_rcon()       # connecting the rcon

        self._list_callback = [] # used for list & qqbot's name function
        self._empty_double_check = None # used for empty boundlist and whitelist function
        self.last_style_change = 0

    def _loading_dicts(self) -> None:
        """ Loading the data for qqbot functions """
        self.font = pygame.font.Font(self.config["dict_address"]["font_path"], 26)
        self.start_command   = start_command_system(self.config["dict_address"]["start_command_dict"])                     # 开服指令
        self.key_word        = key_word_system(self.config["dict_address"]['key_word_dict'])                               # QQ 关键词
        self.key_word_ingame = key_word_system(self.config["dict_address"]['key_word_ingame_dict'], ingame_key_word_help)  # MC 关键词
        self.ban_word        = ban_word_system(self.config["dict_address"]['ban_word_dict'])                               # 违禁词
        self.uuid_qqid       = table(self.config["dict_address"]['uuid_qqid'])                                             # uuid - qqid 表
        self.whitelist = loading_whitelist(self.config["dict_address"]['whitelist'], self.server.logger)                                                                # 白名单
        self.shenheman = table(self.config["dict_address"]['shenheman'])                        # 群审核人员

    def _loading_rcon(self) -> None:
        """ connecting the rcon server for command execution """
        self.rcon = None
        try:
            with open("./config.yml", 'r', encoding='UTF-8') as f:
                config = yaml.load(f)
            
            rcon_config = config.get('rcon', {})
            if rcon_config.get('enable'):
                address = str(rcon_config['address'])
                port = int(rcon_config['port'])
                password = str(rcon_config['password'])
                
                self.server.logger.info(f"尝试连接rcon，rcon地址：{address}:{port}")
                self.rcon = RconConnection(address, port, password)
                self.rcon.connect()
        except Exception as e:
            self.server.logger.warning(f"Rcon 加载失败：{e}")

    #===================================================================#
    #                        Helper functions                           #
    #===================================================================#

    def add_offline_whitelist(self, server: PluginServerInterface, info: Info):
        """ Adding offline player to the whitelist """

        # catch the failture for first entering
        pattern = r".*\[id=([a-z0-9\-]*),name=([^=]+),.*\].*You are not white-listed on this server!$"
        result = re.match(pattern, info.content)
        if not (result and self.config['command']['whitelist'] and self.config['whitelist_add_with_bound']):
            return

        uuid, name = result.groups()[:2]
        # If name not found in bound list -> DO NOTHING
        if name not in [name for sublist in self.data.values() for name in sublist]:
            return
        # If name already in the whitelist -> DO NOTHING
        self.whitelist = loading_whitelist(self.config["dict_address"]['whitelist'])
        if name in self.whitelist.values():
            return

        self.whitelist[uuid] = name
        whitelist_storage = [{'uuid': u, 'name': n} for u, n in self.whitelist.items()]

        for _ in range(3):
            try:
                with open(self.config["dict_address"]['whitelist'], 'w') as f:
                    json.dump(whitelist_storage, f)
                server.logger.info(f"离线玩家：{name}添加成功！")
                server.execute('/whitelist reload')
                break
            except Exception as e:
                server.logger.debug(f"离线玩家：{name}添加失败 -> {e}")
                time.sleep(5)
        else:
            server.logger.error(f"离线玩家：{name}添加失败，已重试3次")

    def send_msg_to_all_qq(self, msg:str)->None:
        """
        Send message to all the QQ group

        Args:
            msg (str): the forward message
        """
        msg = self._add_server_name(msg)

        for group in self.config.get('group_id', []):
            self._send_group_msg(msg, group)

    def set_number_as_name(self, server:PluginServerInterface)->None:
        """
        Set the number of online player as bot's groupcard

        Args:
            server (mcdreforged.api.types.PluginServerInterface): The MCDR game interface.
        """
        bound_list = [name for names in self.data.values() for name in names]

        def list_callback(content:str):
            instance_list = [i.strip() for i in content.split(": ")[-1].split(", ") if i.strip()]
            instance_list = [i.split(']')[-1].split('】')[-1].strip() for i in instance_list] # for [123] player_name & 【123】player_name

            online_player_api = self.server.get_plugin_instance("online_player_api")
            if any(["players online" in i for i in instance_list]) and online_player_api: # multiline_return
                instance_list = online_player_api.get_player_list()
            elif any(["players online" in i for i in instance_list]):
                server.logger.warning("无法解析多行返回，开启 rcon 或下载 online_player_api 来解析")
                server.logger.warning("下载命令: !!MCDR plugin install online_player_api")

            # Obtain the real player name list  
            ip_logger = server.get_plugin_instance("player_ip_logger")
            if ip_logger:
                player = [i for i in instance_list if ip_logger.is_player(i)]
            else:
                player = [i for i in instance_list if i in bound_list or not bound_list]
            number = len(player)

            name = " "
            if number != 0:     
                name = "在线人数: {}".format(number)
            # Call update API
            for gid in self.config.get('group_id', []):
                self.bot.set_group_card(gid, self.bot.get_login_info()["data"]['user_id'], name)

        if self.rcon: # use rcon to get command return 
            list_callback(self.rcon.send_command("list"))
        else:         # use MCDR's on_info to get command return
            self._list_callback.append(list_callback)
            server.execute("list")

    #===================================================================#
    #                    Helper functions (inclass)                     #
    #===================================================================#
    
    def _add_ingame_keyword(self, server, info):
        temp = info.content.replace("!!add ", "", 1).split(maxsplit=1)
        if len(temp) == 2 and temp[0] not in self.key_word_ingame.data:
            self.key_word_ingame.data[temp[0]] = temp[1]
            server.say(get_style_template('add_success', self.style))
        else:
            server.say('关键词重复或者指令无效~')
        return True
    
    # 添加缺失的配置
    def _add_missing_config(self):
        try:
            with self.server.open_bundled_file("gugubot/data/config_default.yml") as file_handler:
                message = file_handler.read()
                message_unicode = message.decode('utf-8').replace('\r\n', '\n')
                yaml_data = yaml.load(message_unicode)

            for key, value in self.config.items():
                if isinstance(value, dict):
                    for sub_k, sub_v in value.items():
                        yaml_data[key][sub_k] = sub_v
                else:
                    yaml_data[key] = value

            for key in ['group_id', 'admin_id', 'admin_group_id']:
                if key not in self.config:
                    del yaml_data[key]

            self.config.data = yaml_data
            self.config.save()
        except Exception as e:
            self.server.logger.error(f"Error loading default config: {e}")

    # 添加服务器名字
    def _add_server_name(self, message):
        if self.server_name != "":
            return f"|{self.server_name}| {message}"
        return message

    def _add_to_whitelist(self, server, info, bot, user_id, game_id):
        server.execute(f'whitelist add {game_id}')
        bot.reply(info, f'[CQ:at,qq={user_id}] {get_style_template("bound_add_whitelist", self.style)}')
        time.sleep(2)
        self.whitelist = loading_whitelist(self.config["dict_address"]['whitelist'])
        self._match_id()

    def _check_ingame_keyword(self, server, info, bot, message):
        if self.config["command"]["ingame_key_word"]:
            response = self.key_word_ingame.check_response(message)
            if response:
                bot.reply(info, response)
                server.say(f'§a[机器人] §f{response}')

    def _delete_ingame_keyword(self, server, info):
        key_word = info.content.replace("!!del ", "", 1).strip()
        if key_word in self.key_word_ingame.data:
            del self.key_word_ingame.data[key_word]
            server.say(get_style_template('delete_success', self.style))
        else:
            server.say('未找到对应关键词~')
        return True
    
    # 通过QQ号找到绑定的游戏ID
    def _find_game_name(self, qq_id: str, bot, group_id: str = None) -> str:
        group_id = group_id if group_id in self.config.get('group_id', []) else self.config.get('group_id', [])[0]
        
        # 启用白名单，返回绑定的游戏ID
        if self.config['command']['whitelist']:
            # 检查是否绑定且在白名单中
            uuid = self.uuid_qqid.get(qq_id)
            if uuid and uuid in self.whitelist:
                return self.whitelist[uuid]
        
        if str(qq_id) in self.data:
            return self.data[str(qq_id)][0]
        
        # 未匹配到名字，尝试获取QQ名片
        try:
            target_data = bot.get_group_member_info(group_id, qq_id).get('data', {})
            target_name = target_data.get('card') or target_data.get('nickname', qq_id)
        except Exception as e:
            self.server.logger.error(f"获取QQ名片失败：{e}, 请检查cq_qq_api链接是否断开")
            target_name = qq_id
        
        self._match_id()
        return target_name

    def _forward_message(self, server, info):
        roll_number = random.randint(0, 10000)
        template_index = (roll_number % (len(mc2qq_template) - 1)) if roll_number >= 3 else -1
        message = mc2qq_template[template_index].format(info.player, info.content)
        self.send_msg_to_all_qq(message)

        if self.config['command']['ingame_key_word']:
            response = self.key_word_ingame.check_response(info.content)
            if response:
                server.say(f'§a[机器人] §f{response}')

    def _forward_message_to_game(self, server, info, bot, message):
        sender = self._find_game_name(str(info.user_id), bot, str(info.source_id))
        message = beautify_message(message, self.config.get('forward', {}).get('keep_raw_image_link', False))
        server.say(f'§6[QQ] §a[{sender}] §f{message}')

    def _get_previous_sender_name(self, qq_id: str, group_id: str, bot, previous_message_content):
        bot_info = bot.get_login_info()['data']['user_id']
        if str(qq_id) == str(bot_info['user_id']):
            # remove server_name in reply
            if self.server_name:
                previous_message_content = previous_message_content.replace(f"|{self.server_name}| ", "", 1)

            # find player name
            pattern = r"^\((.*?)\)|^\[(.*?)\]|^(.*?) 说：|^(.*?) : |^冒着爱心眼的(.*?)说："
            match = re.search(pattern, previous_message_content)
            if match:
                receiver_name = next(group for group in match.groups() if group is not None)
                return receiver_name
            return bot_info['nickname']
        
        return self._find_game_name(qq_id, bot, group_id)

    def _handle_add_image_keyword(self, info, bot):
        image_key_word = info.content.split(maxsplit=1)[-1].strip()
        if image_key_word == "取消" and info.user_id in self.picture_record_dict:
            del self.picture_record_dict[info.user_id]
            respond = get_style_template('add_cancel', self.style)
        elif image_key_word in self.key_word:
            respond = get_style_template('add_existed', self.style)
        elif info.user_id not in self.picture_record_dict:
            self.picture_record_dict[info.user_id] = (image_key_word, time.time())
            respond = get_style_template('add_image_instruction', self.style)
        else:
            respond = get_style_template('add_image_previous_no_done', self.style)
        bot.reply(info, respond)

    def _handle_adding_image(self, server, info, bot):
        # 添加图片
        if info.user_id in self.picture_record_dict and \
                (info.raw_message.startswith('[CQ:image') \
                    or info.raw_message.startswith("[CQ:mface")):
            if  time.time() - self.picture_record_dict[info.user_id][1] >= 30:
                bot.reply(f"添加图片 <{self.picture_record_dict[info.user_id][0]}> 已超时")
                del self.picture_record_dict[info.user_id]
            else:
                try:
                    url = re.search(r'url=([^,\]]+)|file=([^\s,\]]+)', info.raw_message)
                    url = url.group(1) or url.group(2) if url else None
                    url = re.sub('&amp;', "&", url)
                    
                    self.key_word[self.picture_record_dict[info.user_id][0]]=f"[CQ:image,file={url}]"
                    
                    bot.reply(info, get_style_template('add_success', self.style))
                except Exception as e:
                    bot.reply(info, get_style_template('add_image_fail', self.style))
                    server.logger.warning(f"保存图片失败：{info.raw_message}\n报错如下： {e}")
                            # 缓存中移除用户
            return True
        return False

    def _handle_at(self, server, info, bot):
        sender = self._find_game_name(str(info.user_id), bot, str(info.source_id))
        if 'CQ:at' in info.raw_message or 'CQ:reply' in info.raw_message:
            # reply message -> get previous message id -> get previous sender name(receiver)
            previous_message_id = re.search(r"\[CQ:reply,id=(-?\d+).*?\]", info.content, re.DOTALL)
            if previous_message_id:
                previous_message = bot.get_msg(previous_message_id.group(1))['data']
                receiver = self._get_previous_sender_name(str(previous_message['sender']['user_id']), str(info.source_id), bot, previous_message['message'])
                forward_content = re.search(r'\[CQ:reply,id=-?\d+.*?\](?:\[@\d+[^\]]*?\])?(.*)', info.content).group(1).strip()
                server.say(f'§6[QQ] §a[{sender}] §b[@{receiver}] §f{forward_content}')
                
            # @ only -> substitute all the @123 to @player_name 
            else:
                at_pattern = r"\[@(\d+).*?\]|\[CQ:at,qq=(\d+).*?\]"
                forward_content = re.sub(
                    at_pattern, 
                    lambda id: f"§b[@{self._find_game_name(str(id.group(1) or id.group(2)), bot, str(info.source_id))}]", 
                    info.content
                )
                server.say(f'§6[QQ] §a[{sender}] §f{forward_content}')
            return True
        return False

    # 检查违禁词
    def _handle_banned_word(self, server, player, message):
        if self.config['command']['ban_word']:
            ban_response = self.ban_word.check_ban(message)
            if ban_response:
                temp = json.dumps({
                    "text": f"消息包含违禁词无法转发到群聊请修改后重发，维护和谐游戏人人有责。\n违禁理由：{ban_response[1]}",
                    "color": "gray",
                    "italic": True
                })
                server.execute(f'tellraw {player} {temp}')
                return True
        return False

    def _handle_bannedword_command(self, info, bot, command):
        if info.content.startswith(f"{self.config['command_prefix']}违禁词"):
            if len(command)>1 and command[1] == '开':
                self.config['command']['ban_word'] = True
                self.config.save()
                bot.reply(info, '已开启违禁词！')
            # 关闭违禁词
            elif len(command)>1 and command[1] == '关':
                self.config['command']['ban_word'] = False
                self.config.save()
                bot.reply(info, '已关闭违禁词！')
            else:
                self.ban_word.handle_command(info.content, info, bot, reply_style=self.style)
            return True
        
        return False

    def _handle_banned_word_qq(self, info, bot):
        if self.config['command']['ban_word'] and (ban_response := self.ban_word.check_ban(info.content)):
            # 包含违禁词 -> 撤回 + 提示 + 不转发
            bot.delete_msg(info.message_id)
            bot.reply(info, get_style_template('ban_word_find', self.style).format(ban_response[1]))
            return True
        return False

    def _handle_binding(self, server, info, bot, game_id):
        user_id = str(info.user_id)
        # reach maximum number of bound
        if user_id in self.data and len(self.data[user_id]) >= self.config.get("max_bound", 2):
            bot.reply(info, f'[CQ:at,qq={user_id}] {get_style_template("bound_exist", self.style).format(self.data[user_id])}')
            return
        # duplicated name
        if game_id in {name for names in self.data.values() for name in names}:
            bot.reply(info, f'[CQ:at,qq={user_id}] 该名称已被绑定')
            return
        # bound logic
        self.data[user_id] = self.data.get(user_id, []) + [game_id]
        bot.reply(info, f'[CQ:at,qq={user_id}] {get_style_template("bound_success", self.style)}')
        if len(self.data[user_id]) == 1:                                   # change name when first bound
            bot.set_group_card(info.source_id, user_id, game_id)
        if self.config['whitelist_add_with_bound']:                        # bound with adding whitelist
            self._add_to_whitelist(server, info, bot, user_id, game_id)

    def _handle_bound_command(self, info, bot, command):
        if info.content.startswith(f"{self.config['command_prefix']}绑定"):
            if len(command) == 1:
                bot.reply(info, bound_help)
            # 已绑定的名单    
            elif len(command) == 2 and command[1] == '列表':
                bound_list = [f'{qqid} - {", ".join(name)}' for qqid, name in self.data.items()]
                reply_msg = "\n".join(f'{i + 1}. {name}' for i, name in enumerate(bound_list))
                reply_msg = '还没有人绑定' if reply_msg == '' else reply_msg
                bot.reply(info, reply_msg)
            # 查寻绑定的ID
            elif len(command) == 3 and command[1] == '查询':
                if command[2] in self.data:
                    bot.reply(info,
                            f'{command[2]} 绑定的ID是{self.data[command[2]]}')
                else:
                    bot.reply(info, f'{command[2]} 未绑定')
            # 解除绑定
            elif len(command) == 3 and command[1] == '解绑':
                if command[2] in self.data:
                    del self.data[command[2]]
                    bot.reply(info, f'已解除 {command[2]} 绑定的ID')
                elif command[2] in {name for names in self.data.values() for name in names}:
                    for qq_id, game_name in self.data.items():
                        if command[2] in game_name and len(game_name) == 1:
                            del self.data[qq_id]
                            break
                        if command[2] in game_name:
                            self.data[qq_id].remove(command[2])
                            break
                    self.data.save()
                    bot.reply(info, f'已解除 {command[2]} 绑定的ID')
                else:
                    bot.reply(info, f'{command[2]} 未绑定')
            # 绑定ID
            elif len(command) == 3 and command[1].isdigit():
                if len(self.data.get(command[1], []) ) >= self.config.get("max_bound", 2):
                    bot.reply(info, '绑定数量已达上限')
                    return
                if command[2] in {name for names in self.data.values() for name in names}:
                    bot.reply(info, f'该名称已被绑定')
                    return
                self.data[command[1]] = self.data.get(command[1], []) + [command[2]]
                bot.reply(info, '已成功绑定')
            # 清空
            elif len(command) >= 2 and command[1] == "清空":
                if self._empty_double_check == None:
                    self._empty_double_check = str(random_6_digit())
                    bot.reply(info, 
                              f'请输入 {self.config["command_prefix"]}绑定 清空 {self._empty_double_check} 来清空')
                elif self._empty_double_check == command[2]:
                    self.data.data = {}
                    self.data.save() # 清空绑定

                    with open(self.config["dict_address"]['whitelist'],'w') as f:
                        json.dump({}, f) # 清空白名单

                    bot.reply(info, '已成功清除')
                    self._empty_double_check = None
            return True
        return False

    def _handle_bound_notice(self, info, bot)->bool:
        if self.config.get('bound_notice', True) \
            and str(info.user_id) not in self.data.keys() \
            and not is_robot(bot, info.source_id, info.user_id):
            bot.reply(info, f'[CQ:at,qq={info.user_id}][CQ:image,file={Path(self.config["dict_address"]["bound_image_path"]).resolve().as_uri()}]')
            return True
        return False
    
    def _handle_execute_command(self, info, bot):
        if info.content.startswith(f"{self.config['command_prefix']}执行"):
            if self.config['command'].get('execute_command', False) and self.rcon:
                content = self.rcon.send_command(info.content.replace(f"{self.config['command_prefix']}执行", "").strip())
                bot.reply(info, content)
            else:
                bot.reply(info, "服务器未开启RCON")
            return True
        return False

    def _handle_ingame_keyword(self, server, info):
        if self.config['command']['ingame_key_word']:
            if info.content.startswith('!!add '):
                return self._add_ingame_keyword(server, info)
            elif info.content.startswith('!!del '):
                return self._delete_ingame_keyword(server, info)
        return False
    
    def _handle_ingame_keyword_command(self, info, bot, command):
        if info.content.startswith(f"{self.config['command_prefix']}游戏关键词"):
            # 开启游戏关键词
            if len(command)>1 and command[1] == '开':
                self.config['command']['ingame_key_word'] = True
                self.config.save()
                bot.reply(info, '已开启游戏关键词！')
            # 关闭游戏关键词
            elif len(command)>1 and command[1] == '关':
                self.config['command']['ingame_key_word'] = False
                self.config.save()
                bot.reply(info, '已关闭游戏关键词！')
            else:
                self.key_word_ingame.handle_command(info.content, info, bot, reply_style=self.style)
            return True
        return False

    def _handle_keyword(self, server, info, bot):
        # 检测到关键词 -> 转发原文 + 转发回复
        if info.content in self.key_word:
            sender_name = self._find_game_name(str(info.user_id), bot, info.source_id)
            server.say(f'§6[QQ] §a[{sender_name}] §f{info.content}')

            key_word_reply = self.key_word[info.content]
            bot.reply(info, key_word_reply)
            
            # 过滤图片
            if key_word_reply.startswith('[CQ:image'):
                key_word_reply = beautify_message(key_word_reply, self.config.get('forward', {}).get('keep_raw_image_link', False))

            server.say(f'§6[QQ] §a[机器人] §f{key_word_reply}')
            return True
        return False
    
    def _handle_keyword_command(self, info, bot, command):
        if info.content.startswith(f"{self.config['command_prefix']}关键词"):
            # 开启关键词
            if len(command)>1 and command[1] in ['开','on']:
                self.config['command']['key_word'] = True
                self.config.save()
                bot.reply(info, '已开启关键词！')
            # 关闭关键词
            elif len(command)>1 and command[1] in ['关', 'off']:
                self.config['command']['key_word'] = False
                self.config.save()
                bot.reply(info, '已关闭关键词！')
            else:
                self.key_word.handle_command(info.content, info, bot, reply_style=self.style)
            return True
        return False
    
    def _handle_list_command(self, server, info, bot, command):
        def list_callback(content: str):
            server_status = command[0] in ['服务器', 'server']
            player_status = command[0] in ['玩家', '玩家列表']
            bound_list = {i for player_names in self.data.values() for i in player_names}

            instance_list = [i.strip() for i in content.split(": ", 1)[-1].split(", ") if i.strip()]
            instance_list = [i.split(']')[-1].split('】')[-1].strip() for i in instance_list] # 针对 [123] 玩家 和 【123】玩家 这种人名
            
            online_player_api = self.server.get_plugin_instance("online_player_api")
            if any(["players online" in i for i in instance_list]) and online_player_api: # multiline_return
                instance_list = online_player_api.get_player_list()
            elif any(["players online" in i for i in instance_list]):
                server.logger.warning("无法解析多行返回，开启 rcon 或下载 online_player_api 来解析")
                server.logger.warning("下载命令: !!MCDR plugin install online_player_api")

            # 有人绑定 -> 识别假人
            ip_logger = self.server.get_plugin_instance("player_ip_logger")
            
            if ip_logger:
                player_list = [i for i in instance_list if ip_logger.is_player(i)]
                bot_list = [i for i in instance_list if not ip_logger.is_player(i)]
            elif bound_list:
                player_list = [i for i in instance_list if i in bound_list]
                bot_list = [i for i in instance_list if i not in bound_list]
            # 无人绑定 -> 不识别假人 ==> 下版本使用 ip_logging 来识别假人
            else:
                player_list = instance_list
                bot_list = []

            respond = format_list_response(player_list, bot_list, player_status, server_status, self.style)
            respond = self._add_server_name(respond)
            bot.reply(info, respond, force_reply=True)

        if self.rcon: # use rcon to get command return 
            list_callback(self.rcon.send_command("list"))
        else:
            self._list_callback.append(list_callback)
            server.execute("list")

    def _handle_mc_command(self, server, info, bot):
        user_id = str(info.user_id)
        message = info.content.replace(f"{self.config['command_prefix']}mc ", "", 1).strip()
        if user_id in self.data or not self.config.get('bound_notice', True):
            self._forward_message_to_game(server, info, bot, message)
            self._check_ingame_keyword(server, info, bot, message)
        elif self.config.get("bound_notice", True):
            bot.reply(info, f'[CQ:at,qq={user_id}][CQ:image,file={Path(self.config["dict_address"]["bound_image_path"]).resolve().as_uri()}]')

    def _handle_name_command(self, server, info, bot, command):
        if info.content.startswith(f"{self.config['command_prefix']}名字"):

            if info.content == f"{self.config['command_prefix']}名字":
                bot.reply(info, name_help)

            elif len(command)>1 and command[1] == '开':
                self.config['command']['name'] = True
                self.config.save()
                self.set_number_as_name(server)
                bot.reply(info, "显示游戏内人数已开启")

            elif len(command)>1 and command[1] == '关':
                self.config['command']['name'] = False
                self.config.save()
                for gid in self.config.get('group_id', []):
                    bot.set_group_card(gid, int(bot.get_login_info()["data"]['user_id']), " ")
                bot.reply(info, "显示游戏内人数已关闭")
            return True
        return False   
    
    def _handle_reload_command(self, server, info, bot):
        if info.content == f"{self.config['command_prefix']}重启":
            bot.reply(info, "重启中...(请等待10秒)")
            server.reload_plugin("gugubot")
            return True
        return False

    def _handle_shenhe(self, info, bot, action: str):
        if self.shenhe[info.user_id]:
            request = self.shenhe[info.user_id].pop(0)
            bot.set_group_add_request(request[1], request[2], action == '同意')
            
            with open(self.config["dict_address"]['shenhe_log'], 'a+', encoding='utf-8') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} {request[0]} {info.user_id} {'通过' if action == '同意' else '拒绝'}\n")
            
            template = 'authorization_pass' if action == '同意' else 'authorization_reject'
            bot.reply(info, get_style_template(template, self.style).format(request[0]))

    def _handle_shenhe_command(self, info, bot, command):
        if info.content.startswith(f"{self.config['command_prefix']}审核"):
            if len(command)==1:
                bot.reply(info, shenhe_help)
            elif len(command)>1 and command[1] == '开':
                self.config['command']['shenhe'] = True
                self.config.save()
                bot.reply(info, '自动审核开启')
            elif len(command)>1 and command[1] == '关':
                self.config['command']['shenhe'] = False
                self.config.save()
                bot.reply(info, '自动审核关闭')
            elif len(command)>=4 and command[1] == '添加':
                if command[3] not in self.shenheman:
                    self.shenheman[command[3]] = command[2] # 别名：QQ号
                    bot.reply(info, get_style_template('add_success', self.style))
                elif command[3] in self.shenheman:
                    bot.reply(info,'已存在该别名')
            elif command[1] == '删除' and len(command) >= 3:
                
                if command[2] in self.shenheman.values():
                    for k,v in self.shenheman.items():
                        if v == command[2]:
                            del self.shenheman[k]
                    bot.reply(info, get_style_template('delete_success', self.style))
                else:
                    bot.reply(info,'审核员不存在哦！')
            elif len(command)>=2 and command[1] == '列表':
                temp = defaultdict(list)
                for name,qq_id in self.shenheman.items():
                    temp[qq_id].append(name)
                bot.reply(info, "有如下审核员：\n"+"\n".join([k+'-'+",".join(v) for k,v in temp.items()]))
            return True
        return False

    def _handle_startcommand_command(self, info, bot, command):
        if info.content.startswith(f"{self.config['command_prefix']}启动指令"):
            # 开启开服指令
            if len(command)>1 and command[1] == '开':
                self.config['command']['start_command'] = True
                self.config.save()
                bot.reply(info, '已开启开服指令！')
            # 关闭开服指令
            elif len(command)>1 and command[1] == '关':
                self.config['command']['start_command'] = False
                self.config.save()
                bot.reply(info, '已关闭开服指令！')
            else:
                self.start_command.handle_command(info.content, info, bot, reply_style=self.style)
            return True
        return False

    def _handle_style_command(self, info, bot, command):
        style = get_style()
        if len(command) == 1:
            bot.reply(info, style_help)
        elif command[1] == '列表':
            bot.reply(info, "现有如下风格：\n" + '\n'.join(style.keys()))
        elif command[1] in style:
            # 普通成员冷却
            time_diff = int(time.time() - self.last_style_change)
            cooldown = self.config.get("style_cooldown", 0)
            if  time_diff <= cooldown \
                and info.user_id not in self.config['admin_id']:
                bot.reply(info, f"{cooldown - time_diff}秒后才能换风格哦！")
                return
            self.style = command[1]
            self.config['style'] = command[1]
            bot.reply(info, f'已切换为 {self.style}')
            self.last_style_change = time.time()

    def _handle_uuid_command(self, info, bot, command):
        if info.content.startswith(f"{self.config['command_prefix']}uuid"):
            # uuid 帮助
            if len(command)==1:
                bot.reply(info, uuid_help)
            # 查看uuid 匹配表
            elif len(command)>1 and command[1] == '列表':
                bot.reply(info, "uuid匹配如下：\n"+ \
                        '\n'.join([str(k)+'-'+str(v)+'-'+str(self.data[v]) for k,v in self.uuid_qqid.items() if v in self.data]))
            # 更新匹配表
            elif len(command)>1 and command[1] == '重载':
                self.whitelist = loading_whitelist(self.config["dict_address"]['whitelist'])
                self._match_id()
                bot.reply(info, '已重新匹配~')
            # 更改白名单名字
            elif len(command)>=4 and command[1] in ['修改','更改','更新']:
                pre_name = command[2]
                cur_name = command[3]
                with open(self.config["dict_address"]['whitelist'],'r') as f:
                    whitelist = json.load(f) # [{uuid:value,name:value}]
                changed = False
                for index in range(len(whitelist)):
                    if pre_name == whitelist[index]['name']:
                        changed = True
                        whitelist[index]['name'] = cur_name
                        bot.reply(info,'已将 {} 改名为 {}'.format(pre_name,cur_name))
                        with open(self.config["dict_address"]['whitelist'],'w') as f:
                            whitelist = json.dump(whitelist,f) # [{uuid:value,name:value}]
                        self._match_id()
                        bot.reply(info, '已重新匹配~')
                        break
                if not changed:
                    bot.reply(info, '未找到对应名字awa！')      
            return True
        return False          

    def _handle_whitelist_command(self, server, info, bot, command):
        if info.content.startswith(f"{self.config['command_prefix']}白名单"):
            if len(command) == 1:
                bot.reply(info, whitelist_help)
            # 执行指令
            elif len(command)>1 and command[1] in ['添加', '删除','移除', '列表', '开', '关', '重载']:
                if command[1] == '添加':
                    server.execute(f'/whitelist add {command[2]}')
                    bot.reply(info, get_style_template('add_success', self.style))
                    time.sleep(2)
                    self.whitelist = loading_whitelist(self.config["dict_address"]['whitelist'])
                    self._match_id()
                elif command[1] in ['删除','移除']:
                    server.execute(f'/whitelist remove {command[2]}')
                    bot.reply(info, get_style_template('delete_success', self.style))
                    time.sleep(2)
                    self.whitelist = loading_whitelist(self.config["dict_address"]['whitelist'])
                elif command[1] == '开':
                    self.config['command']['whitelist'] = True
                    self.config.save()
                    server.execute(f'/whitelist on')
                    bot.reply(info, '白名单已开启！')
                elif command[1] == '关':
                    self.config['command']['whitelist'] = False
                    self.config.save()
                    server.execute(f'/whitelist off')
                    bot.reply(info, '白名单已关闭！')
                elif command[1] == '重载':
                    server.execute(f'/whitelist reload')
                    self.whitelist = loading_whitelist(self.config["dict_address"]['whitelist'])
                    bot.reply(info, '白名单已重载~')
                else:
                    bot.reply(info,'白名单如下：\n'+'\n'.join(sorted(self.whitelist.values())))
            return True
        return False
    
     # 游戏内@ 推荐
    def _ingame_at_suggestion(self):
        # 初始化成员字典和建议内容
        self.member_dict = {name: qq_id for qq_id, name_list in self.data.items() for name in name_list}
        suggest_content = set(self.member_dict.keys())

        try:
            group_raw_info = [self.bot.get_group_member_list(group_id) for group_id in self.config.get('group_id', [])]
            unpack = [i['data'] for i in group_raw_info if i and i['status'] == 'ok']
        except Exception as e:
            self.server.logger.warning(f"获取群成员列表失败: {e}")
            unpack = []

        for group in unpack:
            for member in group:
                user_id = str(member['user_id'])
                self.member_dict.update({
                    member['nickname']: user_id,
                    member['card']: user_id
                })
                suggest_content.update([member['card'], member['nickname'], user_id])

        return list(suggest_content)

    def _is_valid_command_source(self, info) -> bool:
        return (info.source_id in self.config.get('group_id', []) or
                info.source_id in self.config.get('admin_group_id', []) or
                info.source_id in self.config.get('admin_id', [])) 

    # 匹配uuid和qqid
    def _match_id(self) -> None:
        self.uuid_qqid = {}
        whitelist_dict = {game_name: uuid for uuid, game_name in self.whitelist.items()}
        
        for qq_id, names in self.data.items():
            for name in names:
                clean_name = name.split('(')[0].split('（')[0]
                if clean_name in whitelist_dict:
                    self.uuid_qqid[whitelist_dict[clean_name]] = qq_id

    # 转发消息到指定群
    def _send_group_msg(self, msg, group):
        self.bot.send_group_msg(group, msg)

    # 解包字体，绑定图片
    def _packing_copy(self) -> None:
        def __copyFile(path, target_path):            
            if os.path.exists(target_path):
                return
            target_path = Path(target_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with self.server.open_bundled_file(path) as file_handler: # 从包内解包文件
                message = file_handler.read()
            with open(target_path, 'wb') as f:                        # 复制文件
                f.write(message)
        
        __copyFile("gugubot/data/config_default.yml", "./config/GUGUbot/config.yml")        # 默认设置
        __copyFile("gugubot/data/bound.jpg", "./config/GUGUbot/bound.jpg")        # 绑定图片
        __copyFile("gugubot/font/MicrosoftYaHei-01.ttf", "./config/GUGUbot/font/MicrosoftYaHei-01.ttf") # 默认字体

#+----------------------------------------------------------------------+

class qbot(qbot_helper):
    #===================================================================#
    #                        ingame @ command                           #
    #===================================================================#

    # 游戏内@
    def ingame_at(self, src, ctx):
        if not self.config['command']['qq']:
            return 
        
        player = src.player if src.is_player else 'Console'
        message = ctx['message']
        
        # 检查违禁词
        if self._handle_banned_word(self.server, player, message): return
        
        qq_user_id = ctx['QQ(name/id)'] if ctx['QQ(name/id)'].isdigit() else self.member_dict.get(ctx['QQ(name/id)'])
        if qq_user_id:
            message = f'[{player}] [CQ:at,qq={qq_user_id}] {message}'
            self.send_msg_to_all_qq(message)
        else:
            src.reply(f"无法找到对应的QQ用户ID: {ctx['QQ(name/id)']}")

    #===================================================================#
    #                          ingame !!qq                              #
    #===================================================================#

    # 游戏内指令发送qq
    def ingame_command_qq(self, src, ctx):
        if not self.config['command']['qq']:
            return
        
        player = src.player if src.is_player else 'Console'
        message = ctx['message']

        # 检查违禁词
        if self._handle_banned_word(self.server, player, message): return

        # 正常转发
        self.send_msg_to_all_qq(f'[{player}] {message}')

        # 检测关键词
        if self.config["command"]["key_word"] and message in self.key_word:
            response = self.key_word[message]
            self.send_msg_to_all_qq(response)
            self.server.say(f'§a[机器人] §f{response}')
    
    #===================================================================#
    #                         ingame !!klist                            #
    #===================================================================#

    # 游戏内关键词列表显示
    def ingame_key_list(self):
        temp = '现在有以下关键词:\n' + '\n'.join(self.key_word_ingame.keys())
        self.server.say(temp)

    #===================================================================#
    #                          on_qq_notice                             #
    #===================================================================#

    # 退群处理
    @addTextToImage
    def on_qq_notice(self, server, info, bot):
        server.logger.debug(f"收到上报提示：{info}")
        # 指定群里 + 是退群消息
        if info.notice_type == 'group_decrease' \
            and info.source_id in self.config.get('group_id', []):
            user_id = str(info.user_id)
            if user_id in self.data.keys():
                if self.config["command"]["whitelist"]:
                    for player_name in self.data[user_id]:
                        server.execute(f"whitelist remove {player_name}")
                    bot.reply(info, get_style_template('del_whitelist_when_quit', self.style).format(",".join(self.data[user_id])))
                    # 重载白名单
                    time.sleep(5)
                    self.whitelist = loading_whitelist(self.config["dict_address"]['whitelist'])
                del self.data[user_id]

    #===================================================================#
    #                          on_qq_command                            #
    #===================================================================#

    # 通用QQ 指令   
    @addTextToImage
    def on_qq_command(self, server: PluginServerInterface, info, bot):
        # 检查消息是否来自关注的来源和是否以命令前缀开头
        if not self._is_valid_command_source(info) or not info.content.startswith(self.config['command_prefix']):
            return
        
        if self.config.get('show_message_in_console', True):
            server.logger.info(f"收到消息上报：{info.user_id}:{info.raw_message}")

        if info.content == self.config['command_prefix']:
            info.content += '帮助'

        command = info.content[len(self.config['command_prefix']):].split()
        
        if self.common_command(server, info, bot, command):
            return
        
        if info.message_type == 'private' or info.source_id in self.config.get('admin_group_id', []):
            self.private_command(server, info, bot, command)
        elif info.message_type == 'group':
            self.group_command(server, info, bot, command)

    # 公共指令
    def common_command(self, server: PluginServerInterface, info, bot, command: list) -> bool:
        # 检测违禁词
        if info.message_type == 'group' \
            and info.source_id not in self.config.get('admin_group_id', []) \
            and self._handle_banned_word_qq(info, bot):
            return True

        # 玩家列表
        if self.config['command']['list'] and command[0] in ['玩家列表', '玩家', 'player', '假人列表', '假人', 'fakeplayer', '服务器', 'server']:
            self._handle_list_command(server, info, bot, command)
            return True

        # 禁止群员执行指令
        if self.config['command'].get("group_admin", False) \
            and info.user_id not in self.config['admin_id'] \
            and info.source_id not in self.config.get('admin_group_id', []):
            return True

        # 关键词操作
        if self.config['command']['key_word'] and command[0] in ["列表", 'list', '添加', 'add', '删除', '移除', 'del']:
            self.key_word.handle_command(f"{self.config['command_prefix']}关键词 {' '.join(command)}", info, bot, reply_style=self.style)
            return True

        # 游戏内关键词
        if self.config['command']['ingame_key_word'] and command[0] == '游戏关键词':
            self.key_word_ingame.handle_command(info.content, info, bot, reply_style=self.style)
            return True

        # 添加关键词图片
        if self.config['command']['key_word'] and command[0] == '添加图片' and len(command) > 1:
            self._handle_add_image_keyword(info, bot)
            return True

        # 审核操作
        if self.config['command']['shenhe'] and command[0] in ['同意', '拒绝'] and self.shenhe[info.user_id]:
            self._handle_shenhe(info, bot, command[0])
            return True

        return False
    

    # 管理员指令
    def private_command(self, server, info, bot, command:list):
        # 全部帮助菜单
        if info.content == f"{self.config['command_prefix']}帮助":
            bot.reply(info, admin_help_msg)

        # bound 
        if self._handle_bound_command(info, bot, command): return

        # whitelist
        if self._handle_whitelist_command(server, info, bot, command): return
                    
        # startup command
        if self._handle_startcommand_command(info, bot, command): return
            
        # ban word
        if self._handle_bannedword_command(info, bot, command): return

        # key word
        if self._handle_keyword_command(info, bot, command): return
            
        # ingame key word
        if self._handle_ingame_keyword_command(info, bot, command): return
            
        # uuid
        if self._handle_uuid_command(info, bot, command): return

        # bot's name
        if self._handle_name_command(server, info, bot, command): return 

        # 审核
        if self._handle_shenhe_command(info, bot, command): return
        
        # execute command
        if self._handle_execute_command(info, bot): return 

        # reload plugin
        if self._handle_reload_command(server, info, bot): return


    # group command
    def group_command(self, server, info, bot, command: list):
        if info.content == f"{self.config['command_prefix']}帮助":  # 群帮助
            bot.reply(info, group_help_msg)

        elif self.config['command']['mc'] and command[0] == 'mc':   # qq发送到游戏内消息
            self._handle_mc_command(server, info, bot)
        
        elif len(command) == 2 and command[0] == '绑定':            # 绑定功能
            self._handle_binding(server, info, bot, command[1])
        
        elif command[0] == '风格':                                  # 机器人风格相关
            self._handle_style_command(info, bot, command)

    #===================================================================#
    #                          on_qq_request                            #
    #===================================================================#

    # 进群处理
    @addTextToImage
    def on_qq_request(self, server, info, bot):
        server.logger.debug(f"收到上报请求：{info}")
        if info.request_type == "group" \
            and info.group_id in self.config.get("group_id", []) \
            and self.config["command"]["shenhe"]:
            # 获取名称
            stranger_name = bot.get_stranger_info(info.user_id)["data"]["nickname"]
            # 审核人
            at_id = self.shenheman.get(info.comment, list(self.shenheman.keys())[0])
            # 通知
            bot.reply(info, f"[CQ:at,qq={at_id}] {get_style_template('authorization_request', self.style).format(stranger_name)}")
            server.say(f'§6[QQ] §b[@{at_id}] {get_style_template("authorization_request", self.style).format("§f" + stranger_name)}')
            self.shenhe[at_id].append((stranger_name, info.flag, info.request_type))

    #===================================================================#
    #                           on_qq_message                           #
    #===================================================================#
    # 转发消息
    @addTextToImage
    def on_qq_message(self, server:PluginServerInterface, info, bot):
        # 判断是否转发
        if not is_forward_to_mc_msg(info, bot, self.config): return
        
        if self.config.get('show_message_in_console', True):
            server.logger.info(f"收到消息上报：{info.user_id}:{info.raw_message}")

        # 绑定提示
        if self._handle_bound_notice(info, bot): return
        
        # 违禁词
        if self._handle_banned_word_qq(info, bot): return 
        
        # 检测关键词
        if self.config['command']['key_word']:
            # 检测关键词 -> 转发原文 + 转发回复
            if self._handle_keyword(server, info, bot): return
            # 添加图片
            if self._handle_adding_image(server, info, bot): return

        # @ 模块（回复 + @人）
        if self._handle_at(server, info, bot): return
    
        # 普通转发
        self._forward_message_to_game(server, info, bot, info.raw_message)

    #===================================================================#
    #                          on_mc_message                            #
    #===================================================================#

    # 转发消息
    def on_mc_message(self, server: PluginServerInterface, info: Info):
        if not info.is_player or not self.config['forward']['mc_to_qq']:
            return

        # 检查违禁词
        if self._handle_banned_word(server, info.player, info.content):
            return

        # 处理游戏内关键词
        if self._handle_ingame_keyword(server, info):
            return

        # 转发消息
        if info.content[:2] not in ['@ ', '!!'] or self.config['forward'].get('mc_to_qq_command', False):
            self._forward_message(server, info)