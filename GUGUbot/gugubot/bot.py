# -*- coding: utf-8 -*-
#+----------------------------------------------------------------------+
import asyncio
import random
import re
import time

from pathlib import Path

import pygame

from mcdreforged.api.types import PluginServerInterface, Info
from mcdreforged.api.rtext import RText, RAction, RColor
from packaging import version
from ruamel.yaml import YAML

from gugubot.data.text import (
    admin_help_msg,
    group_help_msg,
    name_help,
    style_help,
    mc2qq_template,
    achievement_tr,
    achievement_template,
    death_template
)
from gugubot.config import autoSaveDict, botConfig
from gugubot.utils import *
from gugubot.system import (
    ban_word_system,
    bound_system,
    ingame_key_word_system,
    key_word_system,
    shenhe_system,
    start_command_system,
    uuid_system,
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

        packing_copy(server)
        
        # read config & bound data
        self.config = botConfig("./config/GUGUbot/config.json", yaml=True, logger=server.logger)
        self.config.addNewConfig(server)
        
        self.server_name = self.config.get("server_name", "")
        self.is_main_server = self.config.get("is_main_server", True)
        self.style = self.config.get("style") if self.config.get("style") != "" else "正常"

        if self.config.get("font_limit", -1) > 0:
            pygame.init()              # for text to image
            self.font = pygame.font.Font(self.config["dict_address"]["font_path"], 26)
            
        self.__loading_systems()      # read data for qqbot functions
        self.customize_help()      # loading customized help msg

        # init params
        self.member_dict = None
        self.last_style_change = 0
        self._list_callback = [] # used for list & qqbot's name function

        self.group_name = self.config['custom_group_name'] \
            if isinstance(self.config['custom_group_name'], dict) else {}

        server.schedule_task(self.__set_ingame_at_suggestion)
        
    async def __set_ingame_at_suggestion(self):
        self.suggestion = await self._ingame_at_suggestion()

    def __loading_systems(self) -> None:
        """ Loading the data for qqbot functions """
        self.whitelist = whitelist(self.server, self.config) # 白名单
        self.data = bound_system("./config/GUGUbot/GUGUbot.json", self.server, self.config, self.whitelist)
        self.key_word = key_word_system(self.config["dict_address"]['key_word_dict'], self.server, self.config) # QQ 关键词
        self.key_word_ingame = ingame_key_word_system(self.config["dict_address"]['key_word_ingame_dict'], self.server, self.config) # MC 关键词
        self.ban_word = ban_word_system(self.config["dict_address"]['ban_word_dict'], self.server, self.config) # 违禁词
        self.start_command = start_command_system(self.config["dict_address"]["start_command_dict"], self.server, self.config) # 开服指令
        self.shenheman = shenhe_system(self.config["dict_address"]['shenheman'], self.server, self.config) # 群审核人员
        self.uuid_qqid = uuid_system(self.config["dict_address"]['uuid_qqid'], self.server, self.config, self.data, self.whitelist) # uuid - qqid 表

    def customize_help(self)->None:
        """ Read customized_help """
        global admin_help_msg, group_help_msg
        content = {
            "admin_help_msg": admin_help_msg,
            "group_help_msg": group_help_msg,
            "A": "\n是换行的意思（没办法解析成多行，不便之处，敬请谅解！）",
            "w": "#开头不用换, 机器人会自动转成指定的前缀"
        }
        temp = autoSaveDict(self.config["dict_address"].get('customized_help_path', "./config/GUGUbot/help_msg.json"),
                            default_content=content)
        admin_help_msg = temp.get("admin_help_msg", admin_help_msg)
        group_help_msg = temp.get("group_help_msg", group_help_msg)

    #===================================================================#
    #                        Helper functions                           #
    #===================================================================#

    # 添加服务器名字
    def _add_server_name(self, message):
        if self.server_name != "":
            return f"{self.server_name} {message}"
        return message

    # 转发消息到指定群
    def _send_group_msg(self, msg, group):
        self.bot.send_group_msg(group, msg)

    def send_msg_to_all_qq(self, msg:str)->None:
        """
        Send message to all the QQ group

        Args:
            msg (str): the forward message
        """
        msg = self._add_server_name(msg)

        for group in self.config.get('group_id', []):
            self._send_group_msg(msg, group)

    def send_msg_to_admin_groups(self, msg:str)->None:
        """
        Send message to all the admin QQ group

        Args:
            msg (str): the forward message
        """
        for group in self.config.get('admin_group_id', []):
            self._send_group_msg(msg, group)

    def _forward_message(self, server, info):
        roll_number = random.randint(0, 10000)
        template_index = (roll_number % (len(mc2qq_template) - 1)) if roll_number >= 3 else -1

        if not self.config.get("random_template", True):
            template_index = 3

        message = mc2qq_template[template_index].format(info.player, info.content)
        # convert @ to CQ:at
        message = convert_to_CQ_at(message, member_dict=self.member_dict)

        self.send_msg_to_all_qq(message)

        if self.config['command']['ingame_key_word']:
            response = self.key_word_ingame.check_response(info.content)
            if response:
                server.say(f'§a[机器人] §f{response}')

    def _forward_message_to_game(self, server:PluginServerInterface, info, bot, message):
        sender = self._find_game_name(str(info.user_id), bot, str(info.source_id))
        message = beautify_message(message,
                                   self.config.get('forward', {}).get('keep_raw_image_link', False),
                                   version.parse(server.get_server_information().version or "1.12") < version.parse("1.12"))

        group_name = self.group_name.get(info.source_id, "QQ") 
        group_id = str(info.source_id)
        
        rtext = RText(f"[{group_name}] ", color=RColor.gold) \
                .set_hover_text(group_id) \
                .set_click_event(action=RAction.copy_to_clipboard, value=group_id) \
            + RText(f"[{sender}]", color=RColor.green) \
            + RText(f" {message}", color=RColor.white)
        server.say(rtext)

    def set_number_as_name(self, server:PluginServerInterface, reset:bool=False)->None:
        """
        Set the number of online player as bot's groupcard

        Args:
            server (mcdreforged.api.types.PluginServerInterface): The MCDR game interface.
        """

        bot_data = asyncio.run(self.bot.get_login_info())["data"]
        bot_qq_id = int(bot_data['user_id'])
        bot_name = bot_data['nickname']

        if reset:
            for gid in self.config.get('group_id', []):
                self.bot.set_group_card(gid, bot_qq_id, bot_name)
            return

        def list_callback(content:str, use_rcon:bool=False):
            player_list, _ = parse_list_content(self.data, server, content, use_rcon)

            number = len(player_list)
            
            bot_data = self.bot.get_login_info_sync()["data"]
            bot_qq_id = int(bot_data['user_id'])
            bot_name = bot_data['nickname']
            
            if number != 0:     
                bot_name = "在线人数: {}".format(number) if \
                    not self.server_name else \
                    f"{self.server_name} {number} 人在线"
            # Call update API
            for gid in self.config.get('group_id', []):
                self.bot.set_group_card(gid, bot_qq_id, bot_name)

        if server.is_rcon_running(): # use rcon to get command return 
            list_callback(server.rcon_query("list"), use_rcon=True)
        else:         # use MCDR's on_info to get command return
            self._list_callback.append(list_callback)
            server.execute("list")

    #===================================================================#
    #                    Helper functions (inclass)                     #
    #===================================================================#

    # 通过QQ号找到绑定的游戏ID
    def _find_game_name(self, qq_id: str, bot, group_id: str = None) -> str:
        group_id = group_id if int(group_id) in self.config.get('group_id', []) else self.config.get('group_id', [])[0]
        
        # 启用白名单，返回绑定的游戏ID
        if self.config['command']['whitelist']: 
            uuid = self.uuid_qqid.get(qq_id)
            if uuid and uuid in self.whitelist: # 检查是否绑定且在白名单中
                return self.whitelist[uuid]
        
        if str(qq_id) in self.data:
            return self.data[str(qq_id)][0]
        
        try:  # 未匹配到名字，尝试获取QQ名片
            target_data = bot.get_group_member_info_sync(group_id, qq_id).get('data', {})
            target_name = target_data.get('card') or target_data.get('nickname', qq_id)
        except Exception as e:
            self.server.logger.error(f"获取QQ名片失败：{e}, 请检查cq_qq_api链接是否断开")
            target_name = qq_id
        
        return target_name

    def _get_previous_sender_name(self, qq_id: str, group_id: str, bot, previous_message_content):
        bot_info = bot.get_login_info_sync()['data']
        if str(qq_id) == str(bot_info['user_id']):
            
            if isinstance(previous_message_content, list):
                self.server.logger.warning("请检查QQ机器人消息格式! 需要: CQ码 或 text")
                # FIXME: 临时兼容 LLOneBot 消息段返回格式
                previous_message_content = previous_message_content[0].get("data",{}).get("text", qq_id).replace(f"{self.server_name} ", "", 1)

            # remove server_name in reply
            if self.server_name:
                previous_message_content = previous_message_content.replace(f"{self.server_name} ", "", 1)

            # find player name
            pattern = r"^\((.*?)\)|^\[(.*?)\]|^(.*?) 说：|^(.*?) : |^冒着爱心眼的(.*?)说："
            match = re.search(pattern, previous_message_content)

            if match:
                receiver_name = next(group for group in match.groups() if group is not None)
                return receiver_name
            
            return bot_info['nickname']
        
        return self._find_game_name(qq_id, bot, group_id)

    def _handle_at(self, server:PluginServerInterface, info, bot):
        sender = self._find_game_name(str(info.user_id), bot, str(info.source_id))
        if 'CQ:at' in info.raw_message or 'CQ:reply' in info.raw_message:
            # reply message -> get previous message id -> get previous sender name(receiver)
            previous_message_id = re.search(r"\[CQ:reply,id=(-?\d+).*?\]", info.content, re.DOTALL)

            group_id = str(info.source_id)
            group_name = self.group_name.get(info.source_id, "QQ") 

            if previous_message_id:
                previous_message = bot.get_msg_sync(previous_message_id.group(1))['data']
                receiver = self._get_previous_sender_name(str(previous_message['sender']['user_id']), str(info.source_id), bot, previous_message['message'])
                forward_content = re.search(r'\[CQ:reply,id=-?\d+.*?\](?:\[@\d+[^\]]*?\])?(.*)', info.content).group(1).strip()

                rtext = RText(f"[{group_name}] ", color=RColor.gold) \
                        .set_hover_text(group_id) \
                        .set_click_event(action=RAction.copy_to_clipboard, value=group_id) \
                    + RText(f"[{sender}]", color=RColor.green) \
                    + RText(f"[@{receiver}]", color=RColor.aqua) \
                    + RText(f" {forward_content}", color=RColor.white)
                server.say(rtext)
                
            # @ only -> substitute all the @123 to @player_name 
            else:
                at_pattern = r"\[@(\d+).*?\]|\[CQ:at,qq=(\d+).*?\]"
                forward_content = re.sub(
                    at_pattern, 
                    lambda id: f' §b[@{self._find_game_name(str(id.group(1) or id.group(2)), bot, str(info.source_id))}] §f', 
                    info.content
                )
                
                rtext = RText(f"[{group_name}] ", color=RColor.gold) \
                        .set_hover_text(group_id) \
                        .set_click_event(action=RAction.copy_to_clipboard, value=group_id) \
                    + RText(f"[{sender}]", color=RColor.green) \
                    + RText(f" {forward_content}", color=RColor.white)
                server.say(rtext)
            return True
        return False

    def _handle_keyword(self, server, info, bot, is_forward_to_mc:bool):
        # 检测到关键词 -> 转发原文 + 转发回复
        if info.content in self.key_word:
            sender_name = self._find_game_name(str(info.user_id), bot, info.source_id)

            if is_forward_to_mc:
                group_name = self.group_name.get(info.source_id, "QQ") 
                group_id = str(info.source_id)

                rtext = RText(f"[{group_name}] ", color=RColor.gold) \
                        .set_hover_text(group_id) \
                        .set_click_event(action=RAction.copy_to_clipboard, value=group_id) \
                    + RText(f"[{sender_name}]", color=RColor.green) \
                    + RText(f" {info.content}", color=RColor.white)
                server.say(rtext)

            key_word_reply = self.key_word[info.content]
            bot.reply(info, key_word_reply)
            
            if is_forward_to_mc:
                # 过滤图片
                if key_word_reply.startswith('[CQ:image'):
                    key_word_reply = beautify_message(key_word_reply, 
                                                      self.config.get('forward', {}).get('keep_raw_image_link', False),
                                                      version.parse(server.get_server_information().version or "1.12") < version.parse("1.12"))
                
                group_name = self.group_name.get(info.source_id, "QQ") 
                group_id = str(info.source_id)
                rtext = RText(f"[{group_name}] ", color=RColor.gold) \
                        .set_hover_text(group_id) \
                        .set_click_event(action=RAction.copy_to_clipboard, value=group_id) \
                    + RText(f"[机器人]", color=RColor.green) \
                    + RText(f" {key_word_reply}", color=RColor.white)
                server.say(rtext)

            return True
        return False

    def _handle_list_command(self, server:PluginServerInterface, info, bot, command:list[str]):
        def list_callback(content: str, use_rcon:bool=False):
            server_status = command[0] in ['服务器', 'server']
            player_status = command[0] in ['玩家', '玩家列表']
            
            player_list, bot_list = parse_list_content(self.data, server, content, use_rcon)

            respond = format_list_response(player_list, bot_list, player_status, server_status, self.style)
            respond = self._add_server_name(respond)
            bot.reply(info, respond, force_reply=True)

        if server.is_rcon_running(): # use rcon to get command return 
            list_callback(server.rcon_query("list"), use_rcon=True)
        else:
            self._list_callback.append(list_callback)
            server.execute("list")
    
     # 游戏内@ 推荐
    async def _ingame_at_suggestion(self):
        # 初始化成员字典和建议内容
        self.member_dict = {name: qq_id for qq_id, name_list in self.data.items() for name in name_list}
        suggest_content = set(self.member_dict.keys())

        try:
            group_raw_info = [await self.bot.get_group_member_list(group_id) for group_id in self.config.get('group_id', []) if group_id]
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
    
    #===================================================================#
    #                      group command helper                         #
    #===================================================================#

    def _handle_style_command(self, info, bot, command):
        style = get_style()
        if len(command) == 1:
            bot.reply(info, style_help.replace("#", self.config["command_prefix"]))
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

    def _handle_mc_command(self, server, info, bot):
        user_id = str(info.user_id)
        message = info.content.replace(f"{self.config['command_prefix']}mc ", "", 1).strip()
        if user_id in self.data or not self.config.get('bound_notice', True):
            self._forward_message_to_game(server, info, bot, message)
            self.key_word_ingame.check_ingame_keyword(server, info, bot, message)
        elif self.config.get("bound_notice", True):
            bot.reply(info, f'[CQ:at,qq={user_id}][CQ:image,file={Path(self.config["dict_address"]["bound_image_path"]).resolve().as_uri()}]')

    #===================================================================#
    #                     private command helper                        #
    #===================================================================#

    def _handle_name_command(self, server, info, bot, command):
        command_prefix = self.config['command_prefix']
        if info.content.startswith(f"{command_prefix}名字"):
            if info.content == f"{command_prefix}名字":
                bot.reply(info, name_help.replace("#", command_prefix))

            elif len(command)>1 and command[1] == '开':
                self.config['command']['name'] = True
                self.config.save()
                self.set_number_as_name(server)
                bot.reply(info, "显示游戏内人数已开启")

            elif len(command)>1 and command[1] == '关':
                self.config['command']['name'] = False
                self.config.save()

                bot_data = bot.get_login_info_sync()["data"]
                bot_qq_id = int(bot_data['user_id'])
                bot_name = bot_data['nickname']

                for gid in self.config.get('group_id', []):
                    bot.set_group_card(gid, bot_qq_id, bot_name)

                bot.reply(info, "显示游戏内人数已关闭")

            return True
        return False   
    
    def _handle_execute_command(self, info, bot):
        """ execute command handler """
        for exec_keyword in ["exec", "执行"]:
            if info.content.startswith(f"{self.config['command_prefix']}{exec_keyword}"):
                # switch = off
                if not self.config['command'].get('execute_command', False):
                    bot.reply(info, "执行指令已关闭")
                # check switch & rcon status
                elif self.server.is_rcon_running():
                    command = info.content.replace(f"{self.config['command_prefix']}{exec_keyword}", "", 1).strip()
                    content = self.server.rcon_query(command)
                    bot.reply(info, content)
                # rcon disconnect
                else:
                    command = info.content.replace(f"{self.config['command_prefix']}{exec_keyword}", "", 1).strip()
                    self.server.execute(command)
                    bot.reply(info, "指令已执行（开启RCON以显示结果）")
                return True
        return False

    def _handle_mcdr_command(self, info, bot):
        """ execute command handler """
        for exec_keyword in ["MCDR", "mcdr"]:
            if info.content.startswith(f"{self.config['command_prefix']}{exec_keyword}"):

                command = info.content.replace(f"{self.config['command_prefix']}{exec_keyword}", "", 1).strip()
                if self.config['command'].get('execute_command', False) and command:  # check switch & valid command
                    
                    command = command if command.startswith("!!") else f"!!{command}"
                    self.server.execute_command(command)
                    bot.reply(info, f"{command} 指令已执行")
                
                else:  # switch = off
                    bot.reply(info, "执行指令已关闭")

                return True
        return False

    def _handle_reload_command(self, server, info, bot):
        """ reload command handler """
        for restart_keyword in ["restart", "重启"]:
            if info.content == f"{self.config['command_prefix']}{restart_keyword}":
                bot.reply(info, "重启中...(请等待10秒)")
                server.reload_plugin("gugubot")
                return True
        return False

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
            and info.group_id in self.config.get('group_id', []):
            user_id = str(info.user_id)
            if user_id in self.data.keys():
                # Remove whitelist
                if self.config["command"]["whitelist"] or self.config.get("whitelist_remove_with_leave", False):
                    for player_name in self.data[user_id]:
                        self.whitelist.remove_player(player_name)
                
                # bot notice
                bot.send_group_msg(group_id = info.group_id, 
                                message = get_style_template('del_whitelist_when_quit', self.style)\
                                .format(",".join(self.data[user_id]) )
                )

                bot.send_msg_to_admin_groups( get_style_template('del_whitelist_when_quit', self.style)\
                                .format(",".join(self.data[user_id]) )
                )
                
                # Remove bound
                del self.data[user_id]

    #===================================================================#
    #                          on_qq_command                            #
    #===================================================================#

    # 通用QQ 指令   
    @addTextToImage
    def on_qq_command(self, server: PluginServerInterface, info, bot):
        # 检查消息是否来自关注的来源和是否以命令前缀开头
        if not is_valid_command_source(info, self.config) or not info.content.startswith(self.config['command_prefix']):
            return
        
        if self.config.get('show_message_in_console', True):
            server.logger.info(f"收到命令上报：{info.user_id}:{info.raw_message}")

        if info.content == self.config['command_prefix']:
            info.content += '帮助'

        command = info.content[len(self.config['command_prefix']):].split()
        
        if self.common_command(server, info, bot, command):
            return
        
        if info.message_type == 'group':
            self.group_command(server, info, bot, command)

        if info.message_type == 'private' or \
            (info.user_id in get_admin_id_list(bot, self.config)):
            self.private_command(server, info, bot, command)
        
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
            and info.user_id not in get_admin_id_list(bot, self.config):
            return True
        # 关键词操作
        elif self.config['command']['key_word'] and command[0] in ["列表", 'list', '添加', 'add', '删除', '移除', 'del', '添加图片', '取消']:
            self.key_word.handle_command(f"关键词 {' '.join(command)}", info, bot, admin=False)

        # 游戏内关键词
        elif self.config['command']['ingame_key_word'] and command[0] == '游戏关键词':
            self.key_word_ingame.handle_command(info.content, info, bot)

        # 审核操作
        elif self.config['command']['shenhe'] and not self.shenheman.respond(info.content, info, bot, self.style):
            return True

        else:
            return False


    # 管理员指令
    def private_command(self, server, info, bot, command:list):
        # 全部帮助菜单
        command_prefix = self.config['command_prefix']
        if info.content == f"{command_prefix}帮助":
            bot.reply(info, admin_help_msg.replace("#", command_prefix))

        raw_command = info.content
        admin = True

        function_list = [
            self.data, # bound
            self.whitelist,
            self.start_command,
            self.ban_word,
            self.key_word,
            self.key_word_ingame,
            self.shenheman, # review invite request
            self.uuid_qqid
        ]

        for func in function_list:
            if func.handle_command(
                raw_command, info, bot, admin
            ): return

        # bot's name
        if self._handle_name_command(server, info, bot, command): return 
        
        # execute command
        if self._handle_execute_command(info, bot): return 

        # execute command
        if self._handle_mcdr_command(info, bot): return 

        # reload plugin
        if self._handle_reload_command(server, info, bot): return


    # group command
    def group_command(self, server, info, bot, command: list):
        command_prefix = self.config['command_prefix']
        if info.content == f"{command_prefix}帮助":  # 群帮助
            bot.reply(info, group_help_msg.replace("#", command_prefix))

        elif self.config['command']['mc'] and command[0] == 'mc':   # qq发送到游戏内消息
            self._handle_mc_command(server, info, bot)
        
        elif len(command) >= 2 and command[0] == '绑定' and info.user_id not in self.config['admin_id']:            # 绑定功能
            self.data.handle_command(
                info.content, info, bot, admin = False
            )
        
        elif command[0] == '风格':                                  # 机器人风格相关
            self._handle_style_command(info, bot, command)

    #===================================================================#
    #                          on_qq_request                            #
    #===================================================================#

    # 进群处理
    @addTextToImage
    def on_qq_request(self, server:PluginServerInterface, info, bot):
        server.logger.debug(f"收到上报请求：{info}")
        if info.request_type == "group" \
            and info.group_id in self.config.get("group_id", []) \
            and self.config["command"]["shenhe"] \
            and self.shenheman.data:
            # 获取名称
            stranger_name = bot.get_stranger_info_sync(info.user_id)["data"]["nickname"]
            # 审核人
            at_id = self.shenheman.get_id(info.comment, list(self.shenheman.keys())[0])
            # 通知
            bot.reply(info, f"[CQ:at,qq={at_id}] {get_style_template('authorization_request', self.style).format(stranger_name)}")
            group_name = self.group_name.get(info.source_id, "QQ") 
            group_id = str(info.source_id)
            rtext = RText(f"[{group_name}] ", color=RColor.gold) \
                    .set_hover_text(group_id) \
                    .set_click_event(action=RAction.copy_to_clipboard, value=group_id) \
                + RText(f"[@{at_id}]", color=RColor.aqua) \
                + RText(f" {get_style_template('authorization_request', self.style).format(stranger_name)}", color=RColor.white)
            server.say(rtext)
            
            self.shenheman.review_queue[at_id].append((stranger_name, info.flag, info.request_type))

    #===================================================================#
    #                           on_qq_message                           #
    #===================================================================#
    # 转发消息
    @addTextToImage
    def on_qq_message(self, server:PluginServerInterface, info, bot):
        self.data.trigger_time_functions(bot)  # 检测未绑定任务
        # 判断是否转发
        if not is_valid_message(info, bot, self.config): return
        
        if self.config.get('show_message_in_console', True):
            server.logger.info(f"收到消息上报：{info.user_id}")#:{info.raw_message}")

        # 绑定提示
        if self.data.handle_bound_notice(info, bot): return
        
        # 违禁词
        if self.ban_word.handle_banned_word_qq(info, bot, self.style): return 
        
        # 是否转发消息
        is_forward_to_mc = self.config['forward']['qq_to_mc']

        if info.source_id not in self.group_name:
            temp = asyncio.run(
                get_group_name(bot, self.config['group_id'])
            )
            temp.update(self.group_name)
            self.group_name = temp

        # 检测关键词
        if self.config['command']['key_word']:

            # 检测关键词 -> 转发原文 + 转发回复
            if self._handle_keyword(server, info, bot, is_forward_to_mc): return

            # 添加图片
            if not self.key_word.add_image_handler(info, bot, self.style): return

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
        self.data.trigger_time_functions(self.bot)  # 检测未绑定任务
        if not info.is_player or not self.config['forward']['mc_to_qq']:
            return

        # 检查违禁词
        if self.ban_word.handle_banned_word_mc(info.player, info.content):
            return

        # 处理游戏内关键词
        if self.key_word_ingame.handle_ingame_keyword(server, info):
            return

        # ISSUE 168
        patterns = self.config.get('ignore_mc_command_patterns', [])
        for pattern in patterns:
            if re.match(pattern, info.content.strip()):
                server.logger.debug(f"忽略游戏内指令: {info.content}")
                return

        # 转发消息
        if info.content[:2] not in ['@ ', '!!'] or self.config['forward'].get('mc_to_qq_command', False):
            self._forward_message(server, info)

    #===================================================================#
    #                        on_mc_achievement                          #
    #===================================================================#

    # 转发成就
    def on_mc_achievement(self, server:PluginServerInterface, player, event, content):
        if self.config["forward"].get("mc_achievement", True):
            player: str = player
            event: str = event # achievement event
            for i in content:
                if i.locale == self.server.get_mcdr_language(): # get the correct language
                    self.send_msg_to_all_qq(i.raw) # forward corresponding achievement message
    #===================================================================#
    #                           on_mc_death                             #
    #===================================================================#

    # 转发死亡
    def on_mc_death(self, server:PluginServerInterface, player, event, content):
        if self.config["forward"].get("mc_death", True):
            player: str = player
            event: str = event # death event
            for i in content:
                if i.locale == self.server.get_mcdr_language(): # get the correct language
                    self.send_msg_to_all_qq(i.raw) # forward corresponding death message