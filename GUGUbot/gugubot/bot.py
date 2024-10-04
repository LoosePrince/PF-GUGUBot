#encoding=utf-8
# The definition of the QQ Chat robot:
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
from .utils import get_style_template, get_style, beautify_message
from collections import defaultdict
from functools import partial
from mcdreforged.api.types import PluginServerInterface, Info
from mcdreforged.minecraft.rcon.rcon_connection import RconConnection
from pathlib import Path
import json
import os
import types
import pygame
import random
import re
import requests
import time
import yaml

class qbot(object):
    def __init__(self, server, bot):
        # 添加初始参数
        self.server = server
        
        self.packing_copy()
        
        self.config = table("./config/GUGUbot/config.json", yaml=True)
        self.data = table("./config/GUGUbot/GUGUbot.json")
        self.bot = bot

        self.server_name = self.config.data.get("server_name","")
        self.is_main_server = self.config.data.get("is_main_server", True)
        self.picture_record_dict = {}
        self.shenhe = defaultdict(list)
        self.style = self.config.data.get("style") if self.config.data.get("style") != "" else "正常"
        self.member_dict = None
        self.suggestion = self.ingame_at_suggestion()
        
        # 读取文件
        pygame.init()
        self.loading_dicts()
        self.loading_rcon()

        self._list_callback = []

    # 读取文件
    def loading_dicts(self) -> None:
        self.font = pygame.font.Font(self.config["dict_address"]["font_path"], 26)
        self.start_command   = start_command_system(self.config["dict_address"]["start_command_dict"])                     # 开服指令
        self.key_word        = key_word_system(self.config["dict_address"]['key_word_dict'])                               # QQ 关键词
        self.key_word_ingame = key_word_system(self.config["dict_address"]['key_word_ingame_dict'], ingame_key_word_help)  # MC 关键词
        self.ban_word        = ban_word_system(self.config["dict_address"]['ban_word_dict'])                               # 违禁词
        self.uuid_qqid       = table(self.config["dict_address"]['uuid_qqid'])                                             # uuid - qqid 表
        self.loading_whitelist()                                                                # 白名单
        self.shenheman = table(self.config["dict_address"]['shenheman'])                        # 群审核人员

        self.add_missing_config()

    def loading_rcon(self) -> None:
        self.rcon = None
        try:
            with open("./config.yml", 'r', encoding='UTF-8') as f:
                config = yaml.safe_load(f)
            
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

    # 离线玩家加入白名单
    def add_offline_whitelist(self, server: PluginServerInterface, info: Info):
        pattern = r".*\[id=([a-z0-9\-]*),name=([^=]+),.*\].*You are not white-listed on this server!$"
        result = re.match(pattern, info.content)
        if not (result and self.config['command']['whitelist'] and self.config['whitelist_add_with_bound']):
            return

        uuid, name = result.groups()[:2]
        if name not in [item for sublist in self.data.values() for item in sublist]:
            return

        self.loading_whitelist()
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

        def _addTextToImage(self, server: PluginServerInterface, info: Info, bot):
            _newReplyWithFont = partial(_newReply, self.font, int(self.config["font_limit"]), self.is_main_server)
            bot.reply = types.MethodType(_newReplyWithFont, bot)
            return func(self, server, info, bot)

        return _addTextToImage

    # 游戏内@
    def ingame_at(self, src, ctx):
        if not self.config['command']['qq']:
            return 
        
        player = src.player if src.is_player else 'Console'
        
        if self.config["command"]["ban_word"]:
            ban_response = self.ban_word.check_ban(ctx['message'])
            if ban_response:
                respond_warning = {
                    "text": f"消息包含违禁词无法转发到群聊请修改后重发，维护和谐游戏人人有责。违禁理由：{ban_response[1]}",
                    "color": "gray",
                    "italic": True
                }
                self.server.execute(f'tellraw {player} {json.dumps(respond_warning)}')
                return 
        
        qq_user_id = ctx['QQ(name/id)'] if ctx['QQ(name/id)'].isdigit() else self.member_dict.get(ctx['QQ(name/id)'])
        if qq_user_id:
            message = f'[{player}] [CQ:at,qq={qq_user_id}] {ctx["message"]}'
            self.send_msg_to_all_qq(message)
        else:
            self.server.logger.warning(f"无法找到对应的QQ用户ID: {ctx['QQ(name/id)']}")

    # 游戏内@ 推荐
    def ingame_at_suggestion(self):
        # 初始化成员字典和建议内容
        self.member_dict = {v: k for k, v_list in self.data.items() for v in v_list}
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

    # 游戏内指令发送qq
    def ingame_command_qq(self, src, ctx):
        if not self.config['command']['qq']:
            return
        
        player = src.player if src.is_player else 'Console'
        message = ctx['message']

        # 检查违禁词
        if self.config["command"]["ban_word"]:
            ban_response = self.ban_word.check_ban(message)
            if ban_response:
                respond_warning = {
                    "text": f"消息包含违禁词无法转发到群聊请修改后重发，维护和谐游戏人人有责。违禁理由：{ban_response[1]}",
                    "color": "gray",
                    "italic": True
                }
                self.server.execute(f'tellraw {player} {json.dumps(respond_warning)}')
                return 

        # 正常转发
        self.send_msg_to_all_qq(f'[{player}] {message}')

        # 检测关键词
        if self.config["command"]["key_word"] and message in self.key_word:
            response = self.key_word[message]
            self.send_msg_to_all_qq(response)
            self.server.say(f'§a[机器人] §f{response}')
    
    # 匹配uuid和qqid
    def match_id(self) -> None:
        self.uuid_qqid = {}
        whitelist_dict = {game_name: uuid for uuid, game_name in self.whitelist.items()}
        
        for qq_id, qq_names in self.data.items():
            for qq_name in qq_names:
                clean_name = qq_name.split('(')[0].split('（')[0]
                if clean_name in whitelist_dict:
                    self.uuid_qqid[whitelist_dict[clean_name]] = qq_id

    # 退群处理
    @addTextToImage
    def notification(self, server, info: Info, bot):
        server.logger.debug(f"收到上报提示：{info}")
        # 指定群里 + 是退群消息
        if info.notice_type == 'group_decrease' \
            and info.source_id in self.config.get('group_id', []):
            user_id = str(info.user_id)
            if user_id in self.data.keys():
                if self.config["command"]["whitelist"]:
                    for player_name in self.data[user_id]:
                        server.execute(f"whitelist remove {player_name}")
                    bot.reply(info, get_style_template('del_whitelist_when_quit', self.style).format(self.data[user_id][0]))
                    # 重载白名单
                    time.sleep(5)
                    self.loading_whitelist()
                del self.data[user_id]

    def is_valid_command_source(self, info: Info) -> bool:
        return (info.source_id in self.config.get('group_id', []) or
                info.source_id in self.config.get('admin_group_id', []) or
                info.source_id in self.config.get('admin_id', []))                

    # 通用QQ 指令   
    @addTextToImage
    def on_qq_command(self, server: PluginServerInterface, info: Info, bot):
        # 检查消息是否来自关注的来源和是否以命令前缀开头
        if not self.is_valid_command_source(info) or not info.content.startswith(self.config['command_prefix']):
            return
        
        if self.config.get('show_message_in_console', True):
            server.logger.info(f"收到消息上报：{info.user_id}:{info.raw_message}")

        if info.content == self.config['command_prefix']:
            info.content = '#帮助'

        command = info.content[len(self.config['command_prefix']):].split()
        
        if self.common_command(server, info, bot, command):
            return
        
        if info.message_type == 'private' or info.source_id in self.config.get('admin_group_id', []):
            self.private_command(server, info, bot, command)
        elif info.message_type == 'group':
            self.group_command(server, info, bot, command)

    # 公共指令
    def common_command(self, server: PluginServerInterface, info: Info, bot, command: list) -> bool:
        # 检测违禁词
        if self.config['command']['ban_word'] and info.message_type == 'group' and info.source_id not in self.config.get('admin_group_id', []):
            if ban_response := self.ban_word.check_ban(' '.join(command)):
                bot.delete_msg(info.message_id)
                bot.reply(info, get_style_template('ban_word_find', self.style).format(ban_response[1]))
                return True

        # 玩家列表
        if self.config['command']['list'] and command[0] in ['玩家列表', '玩家', 'player', '假人列表', '假人', 'fakeplayer', '服务器', 'server']:
            self.handle_list_command(server, info, bot, command)
            return True

        # 关键词操作
        if self.config['command']['key_word'] and command[0] in ["列表", 'list', '添加', 'add', '删除', '移除', 'del']:
            self.key_word.handle_command(info.content, info, bot, reply_style=self.style)
            return True

        # 游戏内关键词
        if self.config['command']['ingame_key_word'] and command[0] == '游戏关键词':
            self.key_word_ingame.handle_command(info.content, info, bot, reply_style=self.style)
            return True

        # 添加关键词图片
        if self.config['command']['key_word'] and command[0] == '添加图片' and len(command) > 1:
            self.handle_add_image_keyword(info, bot)
            return True

        # 审核操作
        if self.config['command']['shenhe'] and command[0] in ['同意', '拒绝'] and self.shenhe[info.user_id]:
            self.handle_shenhe(info, bot, command[0])
            return True

        return False

    def handle_list_command(self, server, info, bot, command):
        def list_callback(content: str):
            server_status = command[0] in ['服务器', 'server']
            player_status = command[0] in ['玩家', '玩家列表']
            bound_list = {i for player_names in self.data.values() for i in player_names}

            instance_list = [i.strip() for i in content.split(": ")[-1].split(", ") if i.strip()]
            instance_list = [i.split(']')[-1].split('】')[-1].strip() for i in instance_list] # 针对 [123] 玩家 和 【123】玩家 这种人名
            
            # 有人绑定 -> 识别假人
            if bound_list:
                player_list = [i for i in instance_list if i in bound_list]
                bot_list = [i for i in instance_list if i not in bound_list]
            # 无人绑定 -> 不识别假人 ==> 下版本使用 ip_logging 来识别假人
            else:
                player_list = instance_list
                bot_list = []

            respond = self.format_list_response(player_list, bot_list, player_status, server_status)
            respond = self.add_server_name(respond)
            bot.reply(info, respond, force_reply=True)

        self._list_callback.append(list_callback)
        server.execute("list")

    def format_list_response(self, player_list, bot_list, player_status, server_status):
        respond = ""
        count = 0

        if player_status or server_status:
            respond += self.format_player_list(player_list)
            count += len(player_list)

        if not player_status:
            respond += self.format_bot_list(bot_list)
            count += len(bot_list)

        if count != 0:
            respond = get_style_template('player_list', self.style).format(
                count,
                '玩家' if player_status else '假人' if not server_status else '人员',
                '\n' + respond
            )
        elif count == 0:
            respond = get_style_template('no_player_ingame', self.style)

        return respond

    def format_player_list(self, player_list):
        if player_list:
            return f"\n---玩家---\n" + '\n'.join(sorted(player_list))
        return get_style_template('no_player_ingame', self.style)

    def format_bot_list(self, bot_list):
        if bot_list:
            return f"\n\n---假人---\n" + '\n'.join(sorted(bot_list))
        return '\n\n没有假人在线哦!'

    def handle_add_image_keyword(self, info, bot):
        image_key_word = info.content.split(maxsplit=1)[-1]
        if image_key_word not in self.key_word.data and info.user_id not in self.picture_record_dict:
            self.picture_record_dict[info.user_id] = image_key_word
            respond = get_style_template('add_image_instruction', self.style)
        elif image_key_word in self.key_word.data:
            respond = get_style_template('add_existed', self.style)
        else:
            respond = get_style_template('add_image_previous_no_done', self.style)
        bot.reply(info, respond)

    def handle_shenhe(self, info, bot, action: str):
        request = self.shenhe[info.user_id][0]
        bot.set_group_add_request(request[1], request[2], action == '同意')
        
        with open(self.config["dict_address"]['shenhe_log'], 'a+', encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} {request[0]} {info.user_id} {'通过' if action == '同意' else '拒绝'}\n")
        
        template = 'authorization_pass' if action == '同意' else 'authorization_reject'
        bot.reply(info, get_style_template(template, self.style).format(request[0]))
        self.shenhe[info.user_id].pop(0)

    # 管理员指令
    def private_command(self, server, info: Info, bot, command:list):
        # 全部帮助菜单
        if info.content == f"{self.config['command_prefix']}帮助":
            bot.reply(info, admin_help_msg)
        # bound 帮助菜单
        elif info.content.startswith(f"{self.config['command_prefix']}绑定"):
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
                elif command[2] in set(name for names in self.data.values() for name in names):
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
                self.data[command[1]] = self.data.get(command[1], []).append(command[2])
                bot.reply(info, '已成功绑定')

        # 白名单
        elif info.content.startswith(f"{self.config['command_prefix']}白名单"):
            if len(command) == 1:
                bot.reply(info, whitelist_help)
            # 执行指令
            elif len(command)>1 and command[1] in ['添加', '删除','移除', '列表', '开', '关', '重载']:
                if command[1] == '添加':
                    server.execute(f'/whitelist add {command[2]}')
                    bot.reply(info, get_style_template('add_success', self.style))
                    time.sleep(2)
                    self.loading_whitelist()
                    self.match_id()
                elif command[1] in ['删除','移除']:
                    server.execute(f'/whitelist remove {command[2]}')
                    bot.reply(info, get_style_template('delete_success', self.style))
                    time.sleep(2)
                    self.loading_whitelist()
                elif command[1] == '开':
                    server.execute(f'/whitelist on')
                    bot.reply(info, '白名单已开启！')
                elif command[1] == '关':
                    server.execute(f'/whitelist off')
                    bot.reply(info, '白名单已关闭！')
                elif command[1] == '重载':
                    server.execute(f'/whitelist reload')
                    self.loading_whitelist()
                    bot.reply(info, '白名单已重载~')
                else:
                    bot.reply(info,'白名单如下：\n'+'\n'.join(sorted(self.whitelist.values())))
                    
        # 启动指令相关
        elif info.content.startswith(f"{self.config['command_prefix']}启动指令"):
            # 开启开服指令
            if len(command)>1 and command[1] == '开':
                self.config['command']['start_command'] = True
                bot.reply(info, '已开启开服指令！')
            # 关闭开服指令
            elif len(command)>1 and command[1] == '关':
                self.config['command']['start_command'] = False
                bot.reply(info, '已关闭开服指令！')
            else:
                self.start_command.handle_command(info.content, info, bot, reply_style=self.style)
            
        # 违禁词相关
        elif info.content.startswith(f"{self.config['command_prefix']}违禁词"):
            if len(command)>1 and command[1] == '开':
                self.config['command']['ban_word'] = True
                bot.reply(info, '已开启违禁词！')
            # 关闭违禁词
            elif len(command)>1 and command[1] == '关':
                self.config['command']['ban_word'] = False
                bot.reply(info, '已关闭违禁词！')
            else:
                self.ban_word.handle_command(info.content, info, bot, reply_style=self.style)
        
        # 关键词相关
        elif info.content.startswith(f"{self.config['command_prefix']}关键词"):
            # 开启关键词
            if len(command)>1 and command[1] in ['开','on']:
                self.config['command']['key_word'] = True
                bot.reply(info, '已开启关键词！')
            # 关闭关键词
            elif len(command)>1 and command[1] in ['关', 'off']:
                self.config['command']['key_word'] = False
                bot.reply(info, '已关闭关键词！')
            else:
                self.key_word.handle_command(info.content, info, bot, reply_style=self.style)
            
        # 游戏内关键词相关
        elif info.content.startswith(f"{self.config['command_prefix']}游戏关键词"):
            # 开启游戏关键词
            if len(command)>1 and command[1] == '开':
                self.config['command']['ingame_key_word'] = True
                bot.reply(info, '已开启游戏关键词！')
            # 关闭游戏关键词
            elif len(command)>1 and command[1] == '关':
                self.config['command']['ingame_key_word'] = False
                bot.reply(info, '已关闭游戏关键词！')
            else:
                self.key_word_ingame.handle_command(info.content, info, bot, reply_style=self.style)

        # uuid匹配相关
        elif info.content.startswith(f"{self.config['command_prefix']}uuid"):
            # uuid 帮助
            if len(command)==1:
                bot.reply(info, uuid_help)
            # 查看uuid 匹配表
            elif len(command)>1 and command[1] == '列表':
                bot.reply(info, "uuid匹配如下：\n"+ \
                        '\n'.join([str(k)+'-'+str(v)+'-'+str(self.data[v]) for k,v in self.uuid_qqid.items() if v in self.data]))
            # 更新匹配表
            elif len(command)>1 and command[1] == '重载':
                self.loading_whitelist()
                self.match_id()
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
                        self.match_id()
                        bot.reply(info, '已重新匹配~')
                        break
                if not changed:
                    bot.reply(info, '未找到对应名字awa！')                

        # 机器人名字 <- 服务器人数
        elif info.content.startswith(f"{self.config['command_prefix']}名字"):

            if info.content == f"{self.config['command_prefix']}名字":
                bot.reply(info, name_help)

            elif len(command)>1 and command[1] == '开':
                self.config['command']['name'] = True
    
                self.set_number_as_name(server)
                bot.reply(info, "显示游戏内人数已开启")

            elif len(command)>1 and command[1] == '关':
                self.config['command']['name'] = False

                for gid in self.config.get('group_id', []):
                    bot.set_group_card(gid, int(bot.get_login_info()["data"]['user_id']), " ")
                bot.reply(info, "显示游戏内人数已关闭")     

        elif info.content.startswith(f"{self.config['command_prefix']}审核"):
            if len(command)==1:
                bot.reply(info, shenhe_help)
            elif len(command)>1 and command[1] == '开':
                self.config['command']['shenhe'] = True
                bot.reply(info, '自动审核开启')
            elif len(command)>1 and command[1] == '关':
                self.config['command']['shenhe'] = False
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
        
        # 执行指令
        elif info.content.startswith(f"{self.config['command_prefix']}执行"):
            if self.config['command'].get('execute_command', False) and self.rcon:
                content = self.rcon.send_command(info.content.replace(f"{self.config['command_prefix']}执行", "").strip())
                bot.reply(info, content)
            else:
                bot.reply(info, "服务器未开启RCON")

    # 群指令
    def group_command(self, server, info: Info, bot, command: list):
        if info.content == f"{self.config['command_prefix']}帮助":  # 群帮助
            bot.reply(info, group_help_msg)
        elif self.config['command']['mc'] and command[0] == 'mc': # qq发送到游戏内消息
            self.handle_mc_command(server, info, bot)
        # 绑定功能
        elif len(command) == 2 and command[0] == '绑定':
            self.handle_binding(server, info, bot, command[1])
        # 机器人风格相关
        elif command[0] == '风格':
            self.handle_style_command(info, bot, command)

    def handle_mc_command(self, server, info: Info, bot):
        user_id = str(info.user_id)
        message = info.content.replace(f"{self.config['command_prefix']}mc ", "", 1)
        if user_id in self.data or not self.config.get('bound_notice', True):
            self.forward_message_to_game(server, user_id, message)
            self.check_ingame_keyword(server, bot, info, message)
        elif self.config.data.get("bound_notice", True):
            self.send_binding_notice(bot, info, user_id)

    def forward_message_to_game(self, server, user_id, message):
        message = beautify_message(message, self.config.get('forward', {}).get('keep_raw_image_link', False))
        server.say(f'§6[QQ] §a[{self.find_game_name(user_id, server, None)}] §f{message}')

    def check_ingame_keyword(self, server, bot, info, message):
        if self.config["command"]["ingame_key_word"]:
            response = self.key_word_ingame.check_response(message)
            if response:
                bot.reply(info, response)
                server.say(f'§a[机器人] §f{response}')

    def send_binding_notice(self, bot, info, user_id):
        bot.reply(info, f'[CQ:at,qq={user_id}][CQ:image,file={Path(self.config["dict_address"]["bound_image_path"]).resolve().as_uri()}]')

    def handle_binding(self, server, info: Info, bot, game_id):
        user_id = str(info.user_id)
        if user_id in self.data and len(self.data[user_id]) >= self.config.get("max_bound", 2):
            bot.reply(info, f'[CQ:at,qq={user_id}] {get_style_template("bound_exist", self.style).format(self.data[user_id])}')
            return
        if game_id in {name for names in self.data.values() for name in names}:
            bot.reply(info, f'[CQ:at,qq={user_id}] 该名称已被绑定')
            return
        self.data[user_id] = self.data.get(user_id, []).append(game_id)
        bot.reply(info, f'[CQ:at,qq={user_id}] {get_style_template("bound_success", self.style)}')
        bot.set_group_card(info.source_id, user_id, game_id)
        if self.config['whitelist_add_with_bound']:
            self.add_to_whitelist(server, bot, info, user_id, game_id)

    def add_to_whitelist(self, server, bot, info, user_id, game_id):
        server.execute(f'whitelist add {game_id}')
        bot.reply(info, f'[CQ:at,qq={user_id}] {get_style_template("bound_add_whitelist", self.style)}')
        time.sleep(2)
        self.loading_whitelist()
        self.match_id()

    def handle_style_command(self, info, bot, command):
        style = get_style()
        if len(command) == 1:
            bot.reply(info, style_help)
        elif command[1] == '列表':
            bot.reply(info, "现有如下风格：\n" + '\n'.join(style.keys()))
        elif command[1] in style:
            self.style = command[1]
            self.config['style'] = command[1]
            bot.reply(info, f'已切换为 {self.style}')

    # 进群处理
    @addTextToImage
    def on_qq_request(self, server, info: Info, bot):
        server.logger.debug(f"收到上报请求：{info}")
        if info.request_type == "group" \
            and info.group_id in self.config.get("group_id", []) \
            and self.config["command"]["shenhe"]:
            # 获取名称
            stranger_name = bot.get_stranger_info(info.user_id)["data"]["nickname"]
            # 审核人
            at_id = self.shenheman[info.comment] if info.comment in self.shenheman else self.config['admin_id'][0]
            # 通知
            bot.reply(info, f"[CQ:at,qq={at_id}] {get_style_template('authorization_request', self.style).format(stranger_name)}")
            server.say(f'§6[QQ] §b[@{at_id}] {get_style_template("authorization_request", self.style).format("§f" + stranger_name)}')
            self.shenhe[at_id].append((stranger_name, info.flag, info.request_type))

    # 转发消息
    @addTextToImage
    def send_msg_to_mc(self, server:PluginServerInterface, info: Info, bot):
        # 判断是否转发
        if len(info.content) == 0 \
            or info.content.startswith(self.config['command_prefix']) \
            or not self.config['forward']['qq_to_mc'] \
            or info.source_id not in self.config.get('group_id', []) \
            or (
                is_robot(bot, info.source_id, info.user_id) \
                and not self.config['forward'].get('farward_other_bot', False)
            ):
            return 
        
        if self.config.get('show_message_in_console', True):
            server.logger.info(f"收到消息上报：{info.user_id}:{info.raw_message}")

        # 判断是否绑定
        if self.config.get('bound_notice', True) \
            and str(info.user_id) not in self.data.keys() \
            and not is_robot(bot, info.source_id, info.user_id):
            bot.reply(info, f'[CQ:at,qq={info.user_id}][CQ:image,file={Path(self.config["dict_address"]["bound_image_path"]).resolve().as_uri()}]')
            return 
        # 如果开启违禁词
        if self.config['command']['ban_word'] and (ban_response := self.ban_word.check_ban(info.content)):
            # 包含违禁词 -> 撤回 + 提示 + 不转发
            bot.delete_msg(info.message_id)
            bot.reply(info, get_style_template('ban_word_find', self.style).format(ban_response[1]))
            return 
        user_id = str(info.user_id)
        # 检测关键词
        if self.config['command']['key_word']:
            # 检测到关键词 -> 转发原文 + 转发回复
            if info.content in self.key_word:
                server.say(f'§6[QQ] §a[{self.find_game_name(user_id, bot, info.source_id)}] §f{info.content}')
                bot.reply(info,self.key_word[info.content])
                # 过滤图片
                reply_message = self.key_word[info.content]
                if reply_message.startswith('[CQ:image'):
                    reply_message = beautify_message(reply_message, self.config.get('forward', {}).get('keep_raw_image_link', False))
                server.say(f'§6[QQ] §a[机器人] §f{reply_message}')
                return
            # 添加图片
            if info.user_id in self.picture_record_dict and \
                    (info.raw_message.startswith('[CQ:image') \
                     or info.raw_message.startswith("[CQ:mface")):
                pattern = r'url=([^,\]]+)'
                try:
                    url = re.search(pattern, info.raw_message).groups()[-1] 
                    url = re.sub('&amp;', "&", url)
                    
                    self.key_word.data[self.picture_record_dict[info.user_id]]=f"[CQ:image,file={url}]"
                    del self.picture_record_dict[info.user_id]                # 缓存中移除用户
                    
                    bot.reply(info, get_style_template('add_success', self.style))
                except Exception as e:
                    bot.reply(info, get_style_template('add_image_fail', self.style))
                    server.logger.warning(f"保存图片失败：{info.raw_message}\n报错如下： {e}")
                return
        # @ 模块
        if 'CQ:at' in info.raw_message:
            def _get_name(qq_id: str, previous_message_content=None):
                if str(qq_id) in self.data:
                    return self.find_game_name(qq_id, bot, info.source_id)
                elif str(qq_id) == str(bot.get_login_info()['data']['user_id']) and previous_message_content:
                    if self.server_name:
                        previous_message_content = previous_message_content.replace(f"|{self.server_name}| ", "", 1)
                    pattern = r"^\((.*?)\)|^\[(.*?)\]|^(.*?) 说：|^(.*?) : |^冒着爱心眼的(.*?)说："
                    match = re.search(pattern, previous_message_content)
                    if match:
                        receiver_name = next(group for group in match.groups() if group is not None)
                        return receiver_name
                    return bot.get_login_info()['data']['nickname']
                # 未绑定
                target_data = bot.get_group_member_info(info.source_id, qq_id)['data']
                return f"{target_data['card'] or target_data['nickname']}"

            sender = _get_name(str(info.user_id))
            
            if "[CQ:reply" in info.content:
                match_result = re.search(r"\[CQ:reply,id=(-?\d+).*?\]", info.content.replace("CQ:at,qq=","@"), re.DOTALL)
                if match_result:
                    previous_message = bot.get_msg(match_result.group(1))['data']
                    receiver = _get_name(str(previous_message['sender']['user_id']), previous_message['message'])
                    forward_content = re.search(r'\[CQ:reply,id=-?\d+.*?\](?:\[@\d+[^\]]*?\])?(.*)', info.content).group(1).strip()
                    server.say(f'§6[QQ] §a[{sender}] §b[@{receiver}] §f{forward_content}')
                    return 
            
            at_pattern = r"\[@(\d+).*?\]|\[CQ:at,qq=(\d+).*?\]"
            sub_string = re.sub(
                at_pattern, 
                lambda id: f"§b[@{_get_name(str(id.group(1) or id.group(2)))}]", 
                info.content
            )
            server.say(f'§6[QQ] §a[{sender}]§f {sub_string}')
        else: 
            info.content = beautify_message(info.raw_message, self.config.get('forward', {}).get('keep_raw_image_link', False))
            server.say(f'§6[QQ] §a[{self.find_game_name(str(info.user_id), bot, info.source_id)}] §f{info.content}')
            
    # 转发消息
    def send_msg_to_qq(self, server: PluginServerInterface, info: Info):
        if not info.is_player or not self.config['forward']['mc_to_qq']:
            return

        # 检查违禁词
        if self.config['command']['ban_word']:
            ban_response = self.ban_word.check_ban(info.content)
            if ban_response:
                self._handle_banned_message(server, info, ban_response)
                return

        # 处理游戏内关键词
        if self.config['command']['ingame_key_word']:
            if self._handle_ingame_keyword(server, info):
                return

        # 转发消息
        if info.content[:2] not in ['@ ', '!!'] or self.config['forward'].get('mc_to_qq_command', False):
            self._forward_message(server, info)

    def _handle_banned_message(self, server, info, ban_response):
        temp = json.dumps({
            "text": f"消息包含违禁词无法转发到群聊请修改后重发，维护和谐游戏人人有责。\n违禁理由：{ban_response[1]}",
            "color": "gray",
            "italic": True
        })
        server.execute(f'tellraw {info.player} {temp}')

    def _handle_ingame_keyword(self, server, info):
        if info.content.startswith('!!add '):
            return self._add_ingame_keyword(server, info)
        elif info.content.startswith('!!del '):
            return self._delete_ingame_keyword(server, info)
        return False

    def _add_ingame_keyword(self, server, info):
        temp = info.content.replace("!!add ", "", 1).split(maxsplit=1)
        if len(temp) == 2 and temp[0] not in self.key_word_ingame.data:
            self.key_word_ingame.data[temp[0]] = temp[1]
            server.say(get_style_template('add_success', self.style))
        else:
            server.say('关键词重复或者指令无效~')
        return True

    def _delete_ingame_keyword(self, server, info):
        key_word = info.content.replace("!!del ", "", 1)
        if key_word in self.key_word_ingame.data:
            del self.key_word_ingame.data[key_word]
            server.say(get_style_template('delete_success', self.style))
        else:
            server.say('未找到对应关键词~')
        return True

    def _forward_message(self, server, info):
        roll_number = random.randint(0, 10000)
        template_index = (roll_number % (len(mc2qq_template) - 1)) if roll_number >= 3 else -1
        message = mc2qq_template[template_index].format(info.player, info.content)
        self.send_msg_to_all_qq(message)

        if self.config['command']['ingame_key_word']:
            response = self.key_word_ingame.check_response(info.content)
            if response:
                server.say(f'§a[机器人] §f{response}')

    ################################################################################
    # 辅助functions
    ################################################################################
    # 添加缺失的配置
    def add_missing_config(self):
        try:
            with self.server.open_bundled_file("gugubot/data/config_default.yml") as file_handler:
                message = file_handler.read()
                message_unicode = message.decode('utf-8')
                yaml_data = yaml.safe_load(message_unicode)
                
                for key, value in yaml_data.items():
                    if key not in self.config and key not in ['group_id', 'admin_id', 'admin_group_id']:
                        self.config[key] = value
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if sub_key not in self.config[key]:
                                self.config[key][sub_key] = sub_value
                
                self.config.save()
        except Exception as e:
            self.server.logger.error(f"Error loading default config: {e}")

    # 添加服务器名字
    def add_server_name(self, message):
        if self.server_name != "":
            return f"|{self.server_name}| {message}"
        return message
    
    # 通过QQ号找到绑定的游戏ID
    def find_game_name(self, qq_id: str, bot, group_id: str = None) -> str:
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
        
        self.match_id()
        return target_name
    
    # 推迟至 1.1.8 
    # 获取最新群公告
    # def get_group_notice(self):
    #     group_id = self.config.get('group_id', [])[0]
    #     if group_id:
    #         notices = self.bot._get_group_notice(group_id)
    #         print(notices)
    #         if notices:
    #             latest_notice = max(notices, key=lambda x: json.loads(x).get('publish_time', 0))
    #             return latest_notice.get('message', {}).get('text', '')
    #     return ''

    # 游戏内关键词列表显示
    def ingame_key_list(self):
        temp = '现在有以下关键词:\n' + '\n'.join(self.key_word_ingame.data.keys())
        self.server.say(temp)

    # 读取json文件 -> 返回dict
    def loading_file(self, path:str) -> dict:
        try:
            with open(path,'r') as f:
                return json.load(f)
        except:
            with open(path,'w') as f:
                return {}

    # 读取白名单
    def loading_whitelist(self)->None:
        try:
            temp = self.loading_file(self.config["dict_address"]['whitelist'])
            self.whitelist = {i['uuid']:i['name'] for i in temp} # 解压白名单表
        except Exception as e:
            self.server.logger.warning(f"读取白名单出错：{e}")                       # debug信息

    # 解包字体，绑定图片
    def packing_copy(self) -> None:
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
            
    # 转发消息到指定群
    def send_group_msg(self, msg, group):
        self.bot.send_group_msg(group, msg)

    # 转发消息到所有群
    def send_msg_to_all_qq(self, msg:str):
        msg = self.add_server_name(msg)

        for group in self.config.get('group_id', []):
            self.send_group_msg(msg, group)

    # 机器人名称显示游戏内人数
    def set_number_as_name(self, server:PluginServerInterface):
        bound_list = [name for names in self.data.values() for name in names]

        def list_callback(content:str):
            instance_list = [i.strip() for i in content.split(": ")[-1].split(", ") if i.strip()]
            instance_list = [i.split(']')[-1].split('】')[-1].strip() for i in instance_list] # 针对 [123] 玩家 和 【123】玩家 这种人名

            # 获取玩家列表  
            player = [i for i in instance_list if i in bound_list or not bound_list]
            number = len(player)

            name = " "
            if number != 0:     
                name = "在线人数: {}".format(number)
            # 更新名字
            for gid in self.config.get('group_id', []):
                self.bot.set_group_card(gid, self.bot.get_login_info()["data"]['user_id'], name)

        if self.rcon: # rcon 命令获取（准确）
            list_callback(self.rcon.send_command("list"))
        else:
            self._list_callback.append(list_callback)
            server.execute("list")
#+---------------------------------------------------------------------+

# 判断是否是机器人
def is_robot(bot, group_id, user_id)->bool:
    user_info = bot.get_group_member_info(group_id, user_id)
    if user_info and user_info.get('data', {}).get('is_robot', False):
        return True
    return False

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
#+---------------------------------------------------------------------+