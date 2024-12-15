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

from .data.text import (
    admin_help_msg,
    group_help_msg,
    name_help,
    style_help,
    uuid_help,
    mc2qq_template
)
from .config import autoSaveDict, botConfig
from .utils import *
from .system import (
    ban_word_system,
    bound_system,
    ingame_key_word_system,
    key_word_system,
    shenhe_system,
    start_command_system,
    whitelist
)

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
        self.config = botConfig("./config/GUGUbot/config.json", yaml=True, logger=server.logger)
        self.config.addNewConfig(server)
        self.whitelist = whitelist(self.server, self.config) # 白名单
        self.data = bound_system("./config/GUGUbot/GUGUbot.json", 
                                 server, self.config, self.whitelist)

        self.server_name = self.config.get("server_name", "")
        self.is_main_server = self.config.get("is_main_server", True)
        self.style = self.config.get("style") if self.config.get("style") != "" else "正常"
        # init params
        self.picture_record_dict = {}
        self.shenhe = defaultdict(list)
        self.member_dict = None
        self.suggestion = self._ingame_at_suggestion()
        
        pygame.init()              # for text to image
        self._loading_dicts()      # read data for qqbot functions
        self.rcon = rcon_connector(server)       # connecting the rcon

        self._list_callback = [] # used for list & qqbot's name function
        self.last_style_change = 0

    def _loading_dicts(self) -> None:
        """ Loading the data for qqbot functions """
        self.font = pygame.font.Font(self.config["dict_address"]["font_path"], 26)
        
        self.key_word = key_word_system(self.config["dict_address"]['key_word_dict'], self.server, self.config) # QQ 关键词
        self.key_word_ingame = ingame_key_word_system(self.config["dict_address"]['key_word_ingame_dict'], self.server, self.config) # MC 关键词
        self.ban_word = ban_word_system(self.config["dict_address"]['ban_word_dict'], self.server, self.config) # 违禁词
        self.start_command = start_command_system(self.config["dict_address"]["start_command_dict"], self.server, self.config) # 开服指令
        self.shenheman = shenhe_system(self.config["dict_address"]['shenheman'], self.server, self.config) # 群审核人员
        self.uuid_qqid = autoSaveDict(self.config["dict_address"]['uuid_qqid']) # uuid - qqid 表

    #===================================================================#
    #                        Helper functions                           #
    #===================================================================#

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

        if server.is_rcon_running(): # use rcon to get command return 
            list_callback(self.rcon.send_command("list"))
        else:         # use MCDR's on_info to get command return
            self._list_callback.append(list_callback)
            server.execute("list")

    #===================================================================#
    #                    Helper functions (inclass)                     #
    #===================================================================#

    # 添加服务器名字
    def _add_server_name(self, message):
        if self.server_name != "":
            return f"|{self.server_name}| {message}"
        return message
    
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
        bot_info = bot.get_login_info()['data']
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
                bot.reply(info, f"添加图片 <{self.picture_record_dict[info.user_id][0]}> 已超时")
                del self.picture_record_dict[info.user_id]
            else:
                try:
                    url_match = re.search(r'url=([^,\]]+)', info.raw_message)
                    url = url_match.group(1) if url_match else None

                    if not url:
                        file_match = re.search(r'file=([^\s,\]]+)', info.raw_message)
                        url = file_match.group(1) if file_match else None
                        
                    url = re.sub('&amp;', "&", url)
                    
                    self.key_word[self.picture_record_dict[info.user_id][0]]=f"[CQ:image,file={url}]"
                    
                    bot.reply(info, get_style_template('add_success', self.style))
                    del self.picture_record_dict[info.user_id] # 缓存中移除用户
                except Exception as e:
                    bot.reply(info, get_style_template('add_image_fail', self.style))
                    server.logger.warning(f"保存图片失败：{info.raw_message}\n报错如下： {e}")
                            
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
    
    def _handle_execute_command(self, info, bot):
        if info.content.startswith(f"{self.config['command_prefix']}执行"):
            if self.config['command'].get('execute_command', False) and self.server.is_rcon_running():
                content = self.rcon.send_command(info.content.replace(f"{self.config['command_prefix']}执行", "").strip())
                bot.reply(info, content)
            else:
                bot.reply(info, "服务器未开启RCON")
            return True
        return False

    def _handle_keyword(self, server, info, bot, is_forward_to_mc:bool):
        # 检测到关键词 -> 转发原文 + 转发回复
        if info.content in self.key_word:
            sender_name = self._find_game_name(str(info.user_id), bot, info.source_id)

            if is_forward_to_mc:
                server.say(f'§6[QQ] §a[{sender_name}] §f{info.content}')

            key_word_reply = self.key_word[info.content]
            bot.reply(info, key_word_reply)
            
            if is_forward_to_mc:
                # 过滤图片
                if key_word_reply.startswith('[CQ:image'):
                    key_word_reply = beautify_message(key_word_reply, self.config.get('forward', {}).get('keep_raw_image_link', False))
                    
                server.say(f'§6[QQ] §a[机器人] §f{key_word_reply}')

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
            if "online: " not in content and online_player_api: # multiline_return
                instance_list = online_player_api.get_player_list()
            elif "online: " not in content:
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

        if server.is_rcon_running(): # use rcon to get command return 
            list_callback(self.rcon.send_command("list"))
        else:
            self._list_callback.append(list_callback)
            server.execute("list")

    def _handle_mc_command(self, server, info, bot):
        user_id = str(info.user_id)
        message = info.content.replace(f"{self.config['command_prefix']}mc ", "", 1).strip()
        if user_id in self.data or not self.config.get('bound_notice', True):
            self._forward_message_to_game(server, info, bot, message)
            self.key_word_ingame.check_ingame_keyword(server, info, bot, message)
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
                self._match_id()
                bot.reply(info, '已重新匹配~')
            return True
        return False          
    
     # 游戏内@ 推荐
    def _ingame_at_suggestion(self):
        # 初始化成员字典和建议内容
        self.member_dict = {name: qq_id for qq_id, name_list in self.data.items() for name in name_list}
        suggest_content = set(self.member_dict.keys())

        try:
            group_raw_info = [self.bot.get_group_member_list(group_id) for group_id in self.config.get('group_id', []) if group_id]
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
                (self.config.get('admin_group_id') and info.source_id in self.config.get('admin_group_id')) or
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
        if self.ban_word.handle_banned_word_mc(player, message): return
        
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
        if self.ban_word.handle_banned_word_mc(player, message): return

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
                        self.whitelist.remove_player(player_name)
                    bot.reply(info, get_style_template('del_whitelist_when_quit', self.style).format(",".join(self.data[user_id])))
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
            server.logger.info(f"收到命令上报：{info.user_id}:{info.raw_message}")

        if info.content == self.config['command_prefix']:
            info.content += '帮助'

        command = info.content[len(self.config['command_prefix']):].split()
        
        if self.common_command(server, info, bot, command):
            return
        
        if info.message_type == 'private' or (self.config.get('admin_group_id') and info.source_id in self.config.get('admin_group_id', [])):
            self.private_command(server, info, bot, command)
        elif info.message_type == 'group':
            self.group_command(server, info, bot, command)

    # 公共指令
    def common_command(self, server: PluginServerInterface, info, bot, command: list) -> bool:
        admin_group_id = self.config.get('admin_group_id') if self.config.get('admin_group_id') else []
        # 检测违禁词
        if info.message_type == 'group' \
            and info.source_id not in admin_group_id \
            and self.ban_word.handle_banned_word_qq(info, bot, self.style):
            return True
        # 玩家列表
        elif self.config['command']['list'] and command[0] in ['玩家列表', '玩家', 'player', '假人列表', '假人', 'fakeplayer', '服务器', 'server']:
            self._handle_list_command(server, info, bot, command)

        # 禁止群员执行指令
        elif self.config['command'].get("group_admin", False) \
            and info.user_id not in self.config['admin_id'] \
            and info.source_id not in admin_group_id:
            return True
        # 关键词操作
        elif self.config['command']['key_word'] and command[0] in ["列表", 'list', '添加', 'add', '删除', '移除', 'del']:
            self.key_word.handle_command(f"关键词 {' '.join(command)}", info, bot, admin=False)

        # 游戏内关键词
        elif self.config['command']['ingame_key_word'] and command[0] == '游戏关键词':
            self.key_word_ingame.handle_command(info.content, info, bot, reply_style=self.style)

        # 添加关键词图片
        elif self.config['command']['key_word'] and command[0] == '添加图片' and len(command) > 1:
            self._handle_add_image_keyword(info, bot)

        # 审核操作
        elif self.config['command']['shenhe'] and command[0] in ['同意', '拒绝'] and self.shenhe[info.user_id]:
            self._handle_shenhe(info, bot, command[0])

        else:
            return False

        return True

    # 管理员指令
    def private_command(self, server, info, bot, command:list):
        # 全部帮助菜单
        if info.content == f"{self.config['command_prefix']}帮助":
            bot.reply(info, admin_help_msg)

        raw_command = info.content
        admin = True

        function_list = [
            self.data, # bound
            self.whitelist,
            self.start_command,
            self.ban_word,
            self.ban_word, 
            self.key_word_ingame,
            self.shenheman # review invite request
        ]

        for func in function_list:
            if func.handle_command(
                raw_command, info, bot, admin
            ): return

        # uuid
        if self._handle_uuid_command(info, bot, command): return

        # bot's name
        if self._handle_name_command(server, info, bot, command): return 
        
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
            self.data.handle_command(
                info.content, info, bot, admin = info.user_id in self.config['admin_id']
            )
        
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
        if not is_valid_message(info, bot, self.config): return
        
        if self.config.get('show_message_in_console', True):
            server.logger.info(f"收到消息上报：{info.user_id}:{info.raw_message}")

        # 绑定提示
        if self.data.handle_bound_notice(info, bot): return
        
        # 违禁词
        if self.ban_word.handle_banned_word_qq(info, bot, self.style): return 
        
        # 是否转发消息
        is_forward_to_mc = self.config['forward']['qq_to_mc']

        # 检测关键词
        if self.config['command']['key_word']:

            # 检测关键词 -> 转发原文 + 转发回复
            if self._handle_keyword(server, info, bot, is_forward_to_mc): return

            # 添加图片
            if self._handle_adding_image(server, info, bot): return

        # 转发消息
        if is_forward_to_mc:

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
        if self.ban_word.handle_banned_word_mc(info.player, info.content):
            return

        # 处理游戏内关键词
        if self.key_word_ingame.handle_ingame_keyword(server, info):
            return

        # 转发消息
        if info.content[:2] not in ['@ ', '!!'] or self.config['forward'].get('mc_to_qq_command', False):
            self._forward_message(server, info)