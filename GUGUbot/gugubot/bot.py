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
from .utils import get_style_template, get_style
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
        
        self.config = table("./config/GUGUBot/config.json", yaml=True)
        self.data = table("./config/GUGUBot/GUGUBot.json")
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

    def loading_rcon(self) -> None:
        self.rcon = None
        try:
            with open("./config.yml", 'r', encoding='UTF-8') as f: # read server config
                temp_data = yaml.load(f, Loader=yaml.FullLoader)
            if temp_data['rcon']['enable']:                        # read rcon parameters
                address  = str(temp_data['rcon']['address'])
                port     = int(temp_data['rcon']['port'])
                password = str(temp_data['rcon']['password'])
                self.server.logger.info(f"尝试连接rcon，rcon地址：{address}:{port}")
                self.rcon = RconConnection(address, port, password)
                self.rcon.connect()
                return
        except Exception as e:
            self.server.logger.warning(f"Rcon 加载失败：{e}")

    # 离线玩家加入白名单
    def add_offline_whitelist(self, server:PluginServerInterface, info:Info):
        pattern = r".*\[id=([a-z0-9\-]*),name=([^=]+),.*\].*You are not white-listed on this server!$" # 捕获警告
        result = re.match(pattern, info.content)
        if result and self.config['command']['whitelist'] and self.config['whitelist_add_with_bound']: # 不在白名单警告
            uuid, name = result.groups()[0:2]
            if name in self.data.values():                     # 在绑定名单中
                self.loading_whitelist()                       # 获取最新白名单
                if name not in self.whitelist.values():
                    self.whitelist[uuid] = name
                    whitelist_storage = [{'uuid':uuid,'name':name} for uuid, name in self.whitelist.items() ] # 转换至[{},{}]格式

                    retry_times = 3                            # 保存
                    while retry_times > 0:
                        retry_times -= 1
                        try:
                            with open(self.config["dict_address"]['whitelist'], 'w') as f:
                                json.dump(whitelist_storage, f)
                                server.logger.info(f"离线玩家：{name}添加成功！")
                                server.execute(f'/whitelist reload')
                            break
                        except Exception as e:
                            server.logger.debug(f"离线玩家：{name}添加失败 -> {e}")
                            time.sleep(5)

    # 文字转图片-装饰器
    def addTextToImage(func):
        def _newReply(font, font_limit:int, is_main_server, self, info, message: str, force_reply:bool = False):
            # 如果不是主群，且不强制转发
            if not is_main_server and not force_reply:
                return 

            if font_limit >= 0 and len(message.split("]")[-1]) >= font_limit: # check condition
                image_path = text2image(font, message)
                message = f"[CQ:image,file={Path(image_path).as_uri()}]"
            """auto reply"""
            if info.message_type == 'private':
                self.send_private_msg(info.source_id, message)
            elif info.message_type == 'group':
                self.send_group_msg(info.source_id, message)
            elif info.message_type == 'discuss':
                self.send_discuss_msg(info.source_id, message)
            """end reply"""

            try:
                time.sleep(2)
                os.remove(image_path)                                         # remove temp image
            except:
                pass

        def _addTextToImage(self, server:PluginServerInterface, info: Info, bot):
            funcType = types.MethodType
            _newReplyWithFont = partial( _newReply, self.font, int(self.config["font_limit"]), self.is_main_server )
            bot.reply = funcType(_newReplyWithFont, bot)
            return func(self, server, info, bot)

        return _addTextToImage

    # 游戏内@
    def ingame_at(self,src,ctx):
        if not self.config['command']['qq']:
            return 
        # get name
        player = src.player if src.is_player else 'Console'        
        # check ban
        if self.config["command"]["ban_word"] and (ban_response := self.ban_word.check_ban(ctx['message'])):
            respond_warning = '{"text":"' + '消息包含违禁词无法转发到群聊请修改后重发，维护和谐游戏人人有责。违禁理由：' +\
                    ban_response[1] +\
                    '","color":"gray","italic":true}'
            self.server.execute(f'tellraw {player} {respond_warning}')
            return 
        # send
        qq_user_id = ctx['QQ(name/id)'] if ctx['QQ(name/id)'].isdigit() else self.member_dict[ctx['QQ(name/id)']]
        message = f'[{player}] [CQ:at,qq={qq_user_id}] {ctx["message"]}'
        self.send_msg_to_all_qq(message)

    # 游戏内@ 推荐
    def ingame_at_suggestion(self):
        # 添加绑定名单
        self.member_dict = {v:k for k,v in self.data.items()} # 用于后续QQ名字对应
        suggest_content = list(self.data.values())

        try: 
            group_raw_info = []
            for group_id in self.config['group_id']:
                group_raw_info.append(self.bot.get_group_member_list(group_id))
            unpack = [i['data'] for i in group_raw_info if i['status'] == 'ok']
        except:
            unpack = []
        for group in unpack:
            for member in group:
                self.member_dict[member['nickname']] = member['user_id']
                self.member_dict[member['card']]     = member['user_id']
                suggest_content += [member['card'], 
                                    member['nickname'], 
                                    str(member['user_id'])]
        return suggest_content

    # 游戏内指令发送qq
    def ingame_command_qq(self,src,ctx):
        if not self.config['command']['qq']:
            return
        player = src.player if src.is_player else 'Console'
        # 违禁词
        if self.config["command"]["ban_word"] and (ban_response := self.ban_word.check_ban(ctx['message'])):
            respond_warning = '{"text":"' + '消息包含违禁词无法转发到群聊请修改后重发，维护和谐游戏人人有责。违禁理由：' +\
                    ban_response[1] +\
                    '","color":"gray","italic":true}'
            self.server.execute(f'tellraw {player} {respond_warning}')
            return 
        # 正常转发
        self.send_msg_to_all_qq(f'[{player}] {ctx["message"]}')
        # 检测关键词
        if self.config["command"]["key_word"] and ctx['message'] in self.key_word:
            self.send_msg_to_all_qq(f'{self.key_word[ctx["message"]]}')
            self.server.say(f'§a[机器人] §f{self.key_word[ctx["message"]]}')
    
    # 匹配uuid qqid
    def match_id(self) -> None:
        # uuid:qq_id
        self.uuid_qqid = {}
        # 解压whitelist
        whitelist_dict = {game_name:uuid for uuid, game_name in self.whitelist.items()}
        # 匹配    
        for qq_id, qq_name in self.data.items():
            if '(' in qq_name or '（' in qq_name:
                qq_name = qq_name.split('(')[0].split('（')[0]
            if qq_name in whitelist_dict:
                self.uuid_qqid[whitelist_dict[qq_name]] = qq_id

    # 退群处理
    @addTextToImage
    def notification(self, server, info: Info, bot):
        server.logger.debug(f"收到上报提示：{info}")
        # 指定群里 + 是退群消息
        if info.notice_type == 'group_decrease' \
            and info.source_id in self.config['group_id']:
            user_id = str(info.user_id)
            if user_id in self.data.keys():
                del self.data[user_id]
                if self.config["command"]["whitelist"]:
                    server.execute(f"whitelist remove {self.data[user_id]}")
                    bot.reply(info, get_style_template('del_whitelist_when_quit', self.style).format(self.data[user_id]))
                    # 重载白名单
                    time.sleep(5)
                    self.loading_whitelist()
                
    # 通用QQ 指令   
    @addTextToImage
    def on_qq_command(self, server: PluginServerInterface, info: Info, bot):
        server.logger.info(f"收到消息上报：{info.user_id}:{info.raw_message}")
        # 过滤非关注的消息
        if not (info.source_id in self.config['group_id'] 
                or info.source_id in self.config['admin_group_id'] 
                or info.source_id in self.config['admin_id']) \
                or len(info.content)==0 \
                or info.content[0] != self.config['command_prefix']:
            return 

        command = info.content.split(' ')
        command[0] = command[0].replace(self.config['command_prefix'], '')
        
        if stop:=self.common_command(server, info, bot, command):
            return
        
        if info.message_type == 'private' or info.source_id in self.config['admin_group_id']:
            self.private_command(server, info, bot, command)
        elif info.message_type == 'group':
            self.group_command(server, info, bot, command)

    # 公共指令
    def common_command(self, server: PluginServerInterface, info: Info, bot, command:list):
        # 检测违禁词
        if self.config['command']['ban_word'] and (info.message_type == 'group' and info.source_id not in self.config['admin_group_id']):
            if ban_response := self.ban_word.check_ban(' '.join(command)):
                bot.delete_msg(info.message_id)
                bot.reply(info, get_style_template('ban_word_find', self.style).format(ban_response[1]))
                return True

        # 玩家列表
        list_command = ['玩家列表','玩家','player',\
                        '假人列表','假人','fakeplayer',\
                        '服务器','server']
        if self.config['command']['list'] and \
            command[0] in list_command:
            server_status = command[0] in ['服务器', 'server']
            player_status = command[0] in ['玩家','玩家列表']
            bound_list    = self.data.values()
            if self.rcon is not None:
                result = self.rcon.send_command('list')
                instance_list = [i.strip() for i in result.split(": ")[-1].split(", ")]
                server.logger.info(f"rcon获取列表如下：{instance_list}")
            else:
                try:
                    content = requests.get(f'https://api.miri.site/mcPlayer/get.php?ip={self.config["game_ip"]}&port={self.config["game_port"]}').json()
                    instance_list = [i['name'].strip() for i in content['sample']]
                    server.logger.info(f"API获取列表如下：{instance_list}")
                except:
                    bot.reply(info, get_style_template('player_api_fail', self.style))
                    return True
            
            player_list = [i for i in instance_list if i in bound_list]
            bot_list    = [i for i in instance_list if i not in bound_list]

            respond = ""
            count   = 0
            if player_status or server_status:
                respond += f"\n---玩家---\n" + '\n'.join(sorted(player_list)) if len(player_list) != 0 else get_style_template('no_player_ingame', self.style)
                count   += len(player_list)
            if not player_status:
                respond += f"\n---假人---\n" + '\n'.join(sorted(bot_list))    if len(bot_list)    != 0 else '\n没有假人在线哦!'
                count   += len(bot_list)
            
            if count != 0:
                respond = get_style_template('player_list', self.style).format(
                    count,
                    '玩家' if player_status else '假人' if not server_status else '人员',
                    '\n'+ respond)
            respond = self.add_server_name(respond)
            bot.reply(info, respond, force_reply = True)

        # 添加关键词
        elif self.config['command']['key_word'] and command[0] in ["列表", 'list', '添加', 'add', '删除', '移除', 'del']:
            self.key_word.handle_command(info.content, info, bot, reply_style=self.style)

        # 游戏内关键词
        elif self.config['command']['ingame_key_word'] and command[0] == '游戏关键词':
            self.key_word_ingame.handle_command(info.content, info, bot, reply_style=self.style)

        # 添加关键词图片
        elif self.config['command']['key_word'] and command[0] == '添加图片' and len(command)>1:
            image_key_word = info.content.split(maxsplit=1)[-1]
            if image_key_word not in self.key_word.data and info.user_id not in self.picture_record_dict:
                # 正常添加
                self.picture_record_dict[info.user_id] = image_key_word
                respond = get_style_template('add_image_instruction', self.style)
            elif image_key_word in self.key_word.data:
                respond = get_style_template('add_existed', self.style)
            else:
                respond = get_style_template('add_image_previous_no_done', self.style)
            bot.reply(info, respond) 

        # 审核通过 找时间重写
        elif self.config['command']['shenhe'] and command[0] == '同意' and len(self.shenhe[info.user_id]) > 0:
            bot.set_group_add_request(self.shenhe[info.user_id][0][1],self.shenhe[info.user_id][0][2],True)
            with open(self.config["dict_address"]['shenhe_log'],'a+',encoding='utf-8') as f:
                f.write(" ".join([time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    self.shenhe[info.user_id][0][0],
                    info.user_id,
                    '通过'])+'\n')
            bot.reply(info, get_style_template('authorization_pass', self.style).format(self.shenhe[info.user_id][0][0]))
            self.shenhe[info.user_id].pop(0)
        # 审核不通过
        elif self.config['command']['shenhe'] and command[0] == '拒绝' and len(self.shenhe[info.user_id]) > 0:
            bot.set_group_add_request(self.shenhe[info.user_id][0][1],self.shenhe[info.user_id][0][2],False)
            with open(self.config["dict_address"]['shenhe_log'],'a+',encoding='utf-8') as f:
                f.write(" ".join([time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    self.shenhe[info.user_id][0][0],
                    info.user_id,
                    '拒绝'])+'\n')
            bot.reply(info, get_style_template('authorization_reject', self.style).format(self.shenhe[info.user_id][0][0]))
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
                bound_list = [f'{qqid} - {name}' for qqid, name in self.data.items()]
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
                else:
                    bot.reply(info, f'{command[2]} 未绑定')
            # 绑定ID
            elif len(command) == 3 and command[1].isdigit():
                self.data[command[1]] = command[2]
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
                        '\n'.join([str(k)+'-'+str(v)+'-'+self.data[v] for k,v in self.uuid_qqid.items() if v in self.data]))
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

                for gid in self.config['group_id']:
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

    # 群指令
    def group_command(self, server, info: Info, bot, command:list):
        if info.content == f"{self.config['command_prefix']}帮助":  # 群帮助
            server.execute("list")
            bot.reply(info, group_help_msg)
        elif self.config['command']['mc'] and command[0] == 'mc': # qq发送到游戏内消息
            user_id = str(info.user_id)
            message = info.content.replace(f"{self.config['command_prefix']}mc ","", 1)
            # 检测绑定
            if user_id in self.data.keys():
                # 正常转发
                server.say(f'§6[QQ] §a[{self.find_game_name(user_id, bot, info.source_id)}] §f{message}')
                # 回复关键词
                if self.config["command"]["ingame_key_word"] and (response := self.key_word_ingame.check_response(message)):
                    bot.reply(info, response)
                    server.say(f'§a[机器人] §f{response}')
            elif self.config.data.get("bound_notice", True):
                bot.reply(info, f'[CQ:at,qq={user_id}][CQ:image,file={Path(self.config["dict_address"]["bound_image_path"]).resolve().as_uri()}]')
        # 绑定功能
        elif len(command) == 2 and command[0] == '绑定':
            user_id = str(info.user_id)
            # 已绑定
            if user_id in self.data.keys():
                _id = self.data[user_id]
                bot.reply(info, f'[CQ:at,qq={user_id}] {get_style_template("bound_exist", self.style).format(_id)}')
                return
            # 未绑定
            self.data[user_id] = command[1]
            bot.reply(info, f'[CQ:at,qq={user_id}] {get_style_template("bound_success", self.style)}')
            # 更换群名片
            bot.set_group_card(info.source_id, user_id, self.data[user_id])
            # 自动加白名单
            if self.config['whitelist_add_with_bound']:
                server.execute(f'whitelist add {command[1]}')
                bot.reply(info, f'[CQ:at,qq={user_id}] {get_style_template("bound_add_whitelist", self.style)}')
                time.sleep(2)
                # 重新匹配
                self.loading_whitelist()
                self.match_id()
            
        # 机器人风格相关
        elif command[0] == '风格':
            style = get_style()
            # 风格帮助
            if info.content == f"{self.config['command_prefix']}风格":
                bot.reply(info, style_help)
            # 风格列表
            elif command[1] == '列表':
                bot.reply(info, "现有如下风格：\n"+'\n'.join(style.keys()))
            # 切换风格
            elif command[1] in style.keys():
                self.style = command[1]
                self.config['style'] = command[1]
                bot.reply(info, f'已切换为 {self.style}')

    # 进群处理
    @addTextToImage
    def on_qq_request(self, server, info: Info, bot):
        server.logger.debug(f"收到上报请求：{info}")
        if info.message_type == "group" \
            and info.source_id in self.config["group_id"] \
            and self.config["command"]["shenhe"]:
            # 获取名称
            stranger_name = bot.get_stranger_info(info.user_id)["data"]["nickname"]
            # 审核人
            at_id = self.shenheman[info.comment] if info.comment in self.shenheman else self.config['admin_id'][0]
            # 通知
            bot.reply(info, f"[CQ:at,qq={at_id}] {get_style_template('authorization_request', self.style).format(stranger_name)}")
            server.say(f'§6[QQ] §b[@{at_id}] {get_style_template("authorization_request", self.style).format("§f" + stranger_name)}')
            self.shenhe[at_id].append((stranger_name, info.flag, info.message_type))

    # 转发消息
    @addTextToImage
    def send_msg_to_mc(self, server:PluginServerInterface, info: Info, bot):
        # 判断是否转发
        if len(info.content) == 0 or \
            info.content.startswith(self.config['command_prefix']) or \
            not self.config['forward']['qq_to_mc'] or \
            info.source_id not in self.config['group_id']:
            return 
        # 判断是否绑定
        if  str(info.user_id) not in self.data.keys():
            # 提示绑定
            if self.config.data.get("bound_notice", True):
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
                is_picture = self.key_word[info.content].startswith('[CQ:image')
                server.say(f'§6[QQ] §a[机器人] §f{self.key_word[info.content] if not is_picture else "图片"}')
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
        if '@' in info.content:
            def _get_name(qq_id:str, previous_message_content=None):
                # 是绑定玩家
                if str(qq_id) in self.data:
                    return self.find_game_name(qq_id, bot, info.source_id)
                # 是机器人
                elif str(qq_id) == str(bot.get_login_info()['data']['user_id']) and previous_message_content is not None:
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
                target_name = target_data['card'] if target_data['card'] != '' else target_data['nickname']
                return f"{target_name}(未绑定)"
            sender = _get_name(str(info.user_id))
            # 回复 -> 正则匹配
            if "[CQ:reply" in info.content:
                # 提取回复id
                pattern = r"(?:\[CQ:reply,id=(-?\d+).*?\])"
                match_result = re.search(pattern, info.content.replace("CQ:at,qq=","@"), re.DOTALL).groups()
                # 提取回复消息
                previous_message = bot.get_msg(match_result[0])['data']
                # 寻找被回复人名字
                receiver_id = previous_message['sender']['user_id']
                receiver = _get_name(str(receiver_id), previous_message['message'])
                # 获取转发内容
                forward_content = re.search(r'\[CQ:reply,id=-?\d+.*?\](?:\[@\d+\])?(.*)', info.content).group(1).strip()
                server.say(f'§6[QQ] §a[{sender}] §b[@{receiver}] §f{forward_content}')
                return 
            # only @ -> 正则替换
            at_pattern = r"\[@(\d+).*?\]|\[CQ:at,qq=(\d+).*?\]"
            sub_string = re.sub(
                at_pattern, 
                lambda id: f"§b[@{_get_name(str(id.group(1) or id.group(2)))}]", 
                info.content
            )
            server.say(f'§6[QQ] §a[{sender}]§f {sub_string}')
        # 普通消息
        else: 
            # 提取链接中标题
            if info.content.startswith('[CQ:json'):
                json_data = re.search(r'\[CQ:json,data=(\{.*\}).*?\]', info.content).group(1)
                json_data = json_data.replace('&#44;', ',').replace('&#91;', '[').replace('&#93;', ']')
                info.content = '[链接]'+ json.loads(json_data)['meta']['detail_1']['desc']
            server.say(f'§6[QQ] §a[{self.find_game_name(str(user_id), bot, info.source_id)}] §f{info.content}')
            
    # 转发消息
    def send_msg_to_qq(self, server:PluginServerInterface, info:Info):
        if not info.is_player or\
            not self.config['forward']['mc_to_qq']:
            return
        # 检查违禁词
        if self.config['command']['ban_word'] and (ban_response := self.ban_word.check_ban(info.content)):
            # 有违禁词 -> 不转发 + 警告
            temp = '{"text":"' + '消息包含违禁词无法转发到群聊请修改后重发，维护和谐游戏人人有责。\n违禁理由：'+\
                ban_response[1] + '","color":"gray","italic":true}'
            server.execute(f'tellraw {info.player} {temp}')
            return
        # 游戏内关键词添加
        if self.config['command']['ingame_key_word'] and info.content.startswith('!!add '):
            temp = info.content.replace("!!add ", "", 1).split(maxsplit=1)
            if len(temp) == 2 and temp[0] not in self.key_word_ingame.data:
                self.key_word_ingame.data[temp[0]] = temp[1]
                server.say(get_style_template('add_success', self.style))
            else:
                server.say('关键词重复或者指令无效~')
        # 游戏内关键词删除
        elif self.config['command']['ingame_key_word'] and info.content.startswith('!!del '):
            key_word = info.content.replace("!!del ", "", 1)
            if  key_word in self.key_word_ingame.data:
                del self.key_word_ingame.data[key_word]
                server.say(get_style_template('delete_success', self.style))
            else:
                server.say('未找到对应关键词~')
        # 转发
        elif info.content[:2] not in [ '@ ','!!']:
            # 转发原句
            roll_number = random.randint(0, 9999+1)
            template_index = (roll_number % (len(mc2qq_template)-1)) if roll_number >= 3 else -1
            message = mc2qq_template[template_index].format(info.player, info.content)
            self.send_msg_to_all_qq(message)
            # 判断游戏内关键词
            if self.config['command']['ingame_key_word'] and info.content in self.key_word_ingame:
                # 游戏内回复
                response = self.key_word_ingame.check_response(info.content)
                server.say(f'§a[机器人] §f{response}')    

    ################################################################################
    # 辅助functions
    ################################################################################
    # 添加服务器名字
    def add_server_name(self, message):
        if self.server_name != "":
            return f"|{self.server_name}| {message}"
        return message
    
    # 通过QQ号找到绑定的游戏ID
    def find_game_name(self, qq_id:str, bot, group_id:str=None) -> str:
        group_id = group_id if group_id in self.config['group_id'] else self.config['group_id'][0]
        qq_uuid = {v:k for k,v in self.uuid_qqid.items()}
        # 未启用白名单
        if not self.config['command']['whitelist']:
            return self.data[qq_id]
        # 如果绑定 且 启动白名单
        if qq_id in qq_uuid:
            uuid = qq_uuid[qq_id]
            if uuid in self.whitelist:
                return self.whitelist[uuid]
        # 未匹配到名字 -> 寻找QQ名片
        target_data = bot.get_group_member_info(group_id, qq_id)['data']
        target_name = target_data['card'] or target_data['nickname']
        self.match_id()
        return f'{target_name}'

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
        __copyFile("gugubot/data/config_default.yml", "./config/GUGUbot/config.yml")        # 绑定图片
        __copyFile("gugubot/data/bound.jpg", "./config/GUGUbot/bound.jpg")        # 绑定图片
        __copyFile("gugubot/font/MicrosoftYaHei-01.ttf", "./config/GUGUbot/MicrosoftYaHei-01.ttf") # 默认字体

    # 转发消息到指定群
    def send_group_msg(self, msg, group):
        self.bot.send_group_msg(group, msg)

    # 转发消息到所有群
    def send_msg_to_all_qq(self, msg:str):
        msg = self.add_server_name(msg)

        for group in self.config['group_id']:
            self.send_group_msg(msg, group)

    # 机器人名称显示游戏内人数
    def set_number_as_name(self, server:PluginServerInterface):
        bound_list = self.data.values()
        if self.rcon: # rcon 命令获取（准确）
            number = len([i for i in self.rcon.send_command("list").split(": ")[-1].split(", ") if i in bound_list])
            server.logger.debug(f'rcon获取列表如下：{self.rcon.send_command("list").split(": ")[-1].split(", ")}')
        else:
            try:      # 使用API获取，高版本可能无效
                content = requests.get(f'https://api.miri.site/mcPlayer/get.php?ip={self.config["game_ip"]}&port={self.config["game_port"]}').json()
                number = len([i["name"] for i in content['sample'] if i["name"] in bound_list])
                server.logger.debug(f"API获取列表如下：{[i['name'] for i in content['sample']]}")
            except:
                server.logger.info("API接口错误/请配置game_ip & game_port参数")
                number = 0
        name = " "
        if number != 0:     
            name = "在线人数: {}".format(number)
        # 更新名字
        for gid in self.config['group_id']:
            self.bot.set_group_card(gid, self.bot.get_login_info()["data"]['user_id'], name)
#+---------------------------------------------------------------------+
# 文字转图片函数，一定程度防止风控？
def text2image(font, input_string:str)->str:
    # 分割成行
    message = input_string.split("\n")
    line_image = [ font.render(text, True, (0, 0, 0), (255 ,255 ,255)) for text in message ]
    # 寻找图片长度 + 宽度
    max_length = max([i.get_width() for i in line_image])
    root = pygame.Surface((max_length,len(message)*33))
    root.fill((255,255,255))
    # 写入
    for i, image in enumerate(line_image):
        root.blit(image, (0, i*33))
    # 保存本地
    if not os.path.exists("./config/GUGUbot/image"):
        os.makedirs("./config/GUGUbot/image")
    image_path = "{}/config/GUGUbot/image/{}.jpg".format(os.getcwd(), int(time.time()))
    pygame.image.save(root, image_path)
    # 返回图片路径
    return image_path
#+---------------------------------------------------------------------+