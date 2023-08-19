#encoding=utf-8
# The definition of the QQ Chat robot:
from .ban_word_system import ban_word_system
from .key_word_system import key_word_system
from .start_command_system import start_command_system
from .table import table
from data.text import *
from collections import defaultdict
from mcdreforged.api.types import PluginServerInterface, Info
from mcdreforged.minecraft.rcon.rcon_connection import RconConnection
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
    def __init__(self, server, config, data, host, port):
        # 添加初始参数
        self.server = server
        self.config = config
        self.data = data
        self.host = host
        self.port = port
        self.picture_record_dict = {}
        self.shenhe = defaultdict(list)
        self.style = "正常"
        self.suggestion = self.ingame_at_suggestion()
        # 读取文件
        self.loading_dicts()
        self.loading_rcon()
        pygame.init()

    # 读取文件
    def loading_dicts(self) -> None:
        self.font = pygame.font.Font(self.config["dict_address"]["font_path"], 26)
        self.start_command   = start_command_system(self.config["dict_address"]["start_command_dict"])                     # 开服指令
        self.key_word        = key_word_system(self.config["dict_address"]['key_word_dict'])                               # QQ 关键词
        self.key_word_ingame = key_word_system(self.config["dict_address"]['key_word_ingame_dict'], ingame_key_word_help)  # MC 关键词
        self.ban_word        = ban_word_system(self.config["dict_address"]['ban_word_dict'])                               # 违禁词
        self.uuid_qqid       = table(self.config["dict_address"]['uuid_qqid'])                                             # uuid - qqid 表
        temp = self.loading_file(self.config["dict_address"]['whitelist'])                      # 白名单表 [{uuid:value, name: value}]
        self.whitelist = {list(i.values())[0]:list(i.values())[1] for i in temp}                # 解压白名单表
        self.shenheman = table(self.config["dict_address"]['shenheman'])                        # 群审核人员

    def loading_rcon(self) -> None:
        try:
            with open("./config.yml", 'r', encoding='UTF-8') as f:
                temp_data = yaml.load(f, Loader=yaml.FullLoader)
            if temp_data['rcon']['enable']:
                address = temp_data['rcon']['address']
                port = temp_data['rcon']['port']
                password = temp_data['rcon']['password']
                self.rcon = RconConnection(address, port, password)
                self.rcon.connect()
                return
            self.rcon = None
        except Exception as e:
            print(f"Rcon 加载失败：{e}")
            self.rcon = None

    # 文字转图片-装饰器
    def addTextToImage(func):
        def _newReply(self, info, message: str):
            if len(message) >= 150:
                image_path = self.text2image(message)
                message = f"[CQ:image,file=file:///{image_path}]"
            """auto reply"""
            if info.source_type == 'private':
                self.send_private_msg(info.source_id, message)
            elif info.source_type == 'group':
                self.send_group_msg(info.source_id, message)
            elif info.source_type == 'discuss':
                self.send_discuss_msg(info.source_id, message)

            try:
                os.remove(image_path)
            except:
                pass

        def _addTextToImage(self, server:PluginServerInterface, info: Info, bot):
            funcType = types.MethodType
            bot.reply = funcType(_newReply, bot)
            return func(self, server, info, bot)

        return _addTextToImage

    def text2image(self, input_string:str):
        message = input_string.split("\n")
        line_image = [ self.font.render(text, True, (0, 0, 0), (255 ,255 ,255)) for text in message ]

        max_length = max([i.get_width() for i in line_image])
        root = pygame.Surface((max_length,len(message)*30))
        root.fill((255,255,255))

        for i, image in enumerate(line_image):
            root.blit(image, (0, i*30))

        if not os.path.exists("./config/GUGUbot/image"):
            os.makedirs("./config/GUGUbot/image")
        image_path = "./config/GUGUbot/image/{}.jpg".format(int(time.time()))
        pygame.image.save(root, image_path)

        return image_path

    # 通用QQ 指令
    @addTextToImage
    def on_qq_command(self,server: PluginServerInterface, info: Info, bot):
        # 过滤非关注的消息
        if not (info.source_id in self.config['group_id'] or
            info.source_id in self.config['admin_id']) or info.raw_content[0] != '#':
            return 
        command = info.content.split(' ')
        command[0] = command[0].replace('#', '')
        # 检测违禁词
        if self.config['command']['ban_word'] and info.source_type == 'group':
            ban_result = self.ban_word.check_ban(' '.join(command))
            if ban_result:
                bot.delete_msg(info.message_id)
                bot.reply(info, style[self.style]['ban_word_find'].format(ban_result[1]))
                return 

        # 玩家列表
        if self.config['command']['list'] and (command[0] in ['玩家列表','玩家'] or command[0] in ['假人列表','假人']):
            player = command[0] in ['玩家','玩家列表']
            if self.rcon:
                result = self.rcon.send_command('list')
                player_list = result.split(": ")[-1].split(", ")
                t_player = [i for i in player_list if "假的" not in i] if player else [i for i in player_list if "假的" in i]
            else:
                try:
                    content = requests.get(f'https://api.miri.site/mcPlayer/get.php?ip={self.config["game_ip"]}&port={self.config["game_port"]}').json()
                    
                    if player: # 过滤假人
                        t_player = [i["name"] for i in content['sample'] if i["name"] in self.whitelist.values()]
                    else: # 过滤真人
                        t_player = [i["name"] for i in content['sample'] if i["name"] not in self.whitelist.values()] 
                except:
                    bot.reply(info, "未能获取到服务器信息，请检查服务器参数设置！（推荐开启rcon精准获取玩家信息）")

            if len(t_player) == 0 :
                respond = style[self.style]['no_player_ingame'] if player else '没有假人在线哦！'
            else:
                t_player.sort() # 名字排序
                respond = style[self.style]['player_list'].format(
                    len(t_player),
                    '玩家' if player else '假人',
                    ', '.join(t_player))
            bot.reply(info, respond)

        # 添加关键词
        elif self.config['command']['key_word'] and command[0] in ["列表",'添加','删除']:
            self.key_word.handle_command(info.content, info, bot, style=self.style)

        # 游戏内关键词
        elif self.config['command']['ingame_key_word'] and command[0] == '游戏关键词':
            if self.config['command']['ban_word']:
                ban_result = self.ban_word.check_ban(''.join(command[1:]))
                if ban_result:
                    bot.delete_msg(info.message_id)
                    bot.reply(info, style[self.style]['ban_word_find'].format(ban_result[1]))
                    return 
            self.key_word_ingame.handle_command(info.content, info, bot, style=self.style)

        # 添加关键词图片
        elif self.config['command']['key_word'] and command[0] == '添加图片' and len(command)>1:
            if command[1] not in self.key_word.data and info.user_id not in self.picture_record_dict:
                ban_result = self.ban_word.check_ban(command[1])
                if ban_result:
                    bot.delete_msg(info.message_id)
                    bot.reply(info, style[self.style]['ban_word_find'].format(ban_result[1]))
                    return 
                else: # 正常添加
                    self.picture_record_dict[info.user_id] = command[1]
                    bot.reply(info, '请发送要添加的图片~')
            elif command[1] in self.key_word.data:
                bot.reply(info, '已存在该关键词~')
            else:
                bot.reply(info,'上一个关键词还未绑定，添加哒咩！') 

        # 审核通过
        elif self.config['command']['shenhe'] and command[0] == '同意' and len(self.shenhe[info.user_id]) > 0:
            bot.set_group_add_request(self.shenhe[info.user_id][0][1],self.shenhe[info.user_id][0][2],True)
            with open(self.config["dict_address"]['shenhe_log'],'a+',encoding='utf-8') as f:
                f.write(" ".join([time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    self.shenhe[info.user_id][0][0],
                    info.user_id,
                    '通过'])+'\n')
            bot.reply(info,f"已通过{self.shenhe[info.user_id][0][0]}的申请awa")
            self.shenhe[info.user_id].pop(0)
        # 审核不通过
        elif self.config['command']['shenhe'] and command[0] == '拒绝' and len(self.shenhe[info.user_id]) > 0:
            bot.set_group_add_request(self.shenhe[info.user_id][0][1],self.shenhe[info.user_id][0][2],False)
            with open(self.config["dict_address"]['shenhe_log'],'a+',encoding='utf-8') as f:
                f.write(" ".join([time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    self.shenhe[info.user_id][0][0],
                    info.user_id,
                    '拒绝'])+'\n')
            bot.reply(info,f"已拒绝{self.shenhe[info.user_id][0][0]}的申请awa")
            self.shenhe[info.user_id].pop(0)
        
        if info.source_type == 'private':
            self.private_command(server, info, bot, command)
        elif info.source_type == 'group':
            self.group_command(server, info, bot, command)

    # 管理员指令
    def private_command(self, server, info: Info, bot, command:list):
        # 全部帮助菜单
        if info.content == '#帮助':
            bot.reply(info, admin_help_msg)
        # bound 帮助菜单
        elif info.content.startswith('#绑定'):
            if info.content == '#绑定':
                bot.reply(info, bound_help)
            # 已绑定的名单    
            elif len(command) == 2 and command[1] == '列表':
                bound_list = [f'{a} - {b}' for a, b in self.data.items()]
                reply_msg = ''
                for i in range(0, len(bound_list)):
                    reply_msg += f'{i + 1}. {bound_list[i]}\n'
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
                    self.data.save()
                    bot.reply(info, f'已解除 {command[2]} 绑定的ID')
                else:
                    bot.reply(info, f'{command[2]} 未绑定')
            # 绑定ID
            elif len(command) == 3 and command[1].isdigit():
                self.data[command[1]] = command[2]
                self.data.save()
                bot.reply(info, '已成功绑定')

        # 白名单
        elif info.content.startswith('#白名单'):
            if info.content == '#白名单':
                bot.reply(info, whitelist_help)
            # 执行指令
            elif len(command)>1 and command[1] in ['添加', '删除','移除', '列表', '开', '关', '重载']:
                if command[1] == '添加':
                    server.execute(f'/whitelist add {command[2]}')
                    bot.reply(info, style[self.style]['add_success'])
                    while command[2] not in self.whitelist:
                        temp = self.loading_file(self.config["dict_address"]['whitelist'])
                        # 解压白名单表
                        self.whitelist = {list(i.values())[0]:list(i.values())[1] for i in temp}
                        time.sleep(2)
                    self.match_id()
                elif command[1] in ['删除','移除']:
                    server.execute(f'/whitelist remove {command[2]}')
                    bot.reply(info ,style[self.style]['delete_success'])
                    temp = self.loading_file(self.config["dict_address"]['whitelist'])
                    # 解压白名单表
                    self.whitelist = {list(i.values())[0]:list(i.values())[1] for i in temp}
                elif command[1] == '开':
                    server.execute(f'/whitelist on')
                    bot.reply(info, '白名单已开启！')
                elif command[1] == '关':
                    server.execute(f'/whitelist off')
                    bot.reply(info, '白名单已关闭！')
                elif command[1] == '重载':
                    server.execute(f'/whitelist reload')
                    temp = self.loading_file(self.config["dict_address"]['whitelist'])
                    # 解压白名单表
                    self.whitelist = {list(i.values())[0]:list(i.values())[1] for i in temp}
                    bot.reply(info, '白名单已重载~')
                else:
                    bot.reply(info,'白名单如下：\n'+'\n'.join(sorted(self.whitelist.values())))
                    
        # 启动指令相关
        elif info.content.startswith('#启动指令'):
            # 开启开服指令
            if len(command)>1 and command[1] == '开':
                self.config['command']['start_command'] = True
                bot.reply(info, '已开启开服指令！')
            # 关闭开服指令
            elif len(command)>1 and command[1] == '关':
                self.config['command']['start_command'] = False
                bot.reply(info, '已关闭开服指令！')
            else:
                self.start_command.handle_command(info.content, info, bot, style=self.style)
              
        # 违禁词相关
        elif info.content.startswith('#违禁词'):
            if len(command)>1 and command[1] == '开':
                self.config['command']['ban_word'] = True
                bot.reply(info, '已开启违禁词！')
            # 关闭违禁词
            elif len(command)>1 and command[1] == '关':
                self.config['command']['ban_word'] = False
                bot.reply(info, '已关闭违禁词！')
            else:
                self.ban_word.handle_command(info.content, info, bot, style=self.style)
        
        # 关键词相关
        elif info.content.startswith('#关键词'):
            # 开启关键词
            if len(command)>1 and command[1] in ['开','on']:
                self.config['command']['key_word'] = True
                bot.reply(info, '已开启关键词！')
            # 关闭关键词
            elif len(command)>1 and command[1] in ['关', 'off']:
                self.config['command']['key_word'] = False
                bot.reply(info, '已关闭关键词！')
            else:
                self.key_word.handle_command(info.content, info, bot, style=self.style)
            
        # 游戏内关键词相关
        elif info.content.startswith('#游戏关键词'):
            # 开启游戏关键词
            if len(command)>1 and command[1] == '开':
                self.config['command']['ingame_key_word'] = True
                bot.reply(info, '已开启游戏关键词！')
            # 关闭游戏关键词
            elif len(command)>1 and command[1] == '关':
                self.config['command']['ingame_key_word'] = False
                bot.reply(info, '已关闭游戏关键词！')
            else:
                self.key_word_ingame.handle_command(info.content, info, bot, style=self.style)

        # uuid匹配相关
        elif info.content.startswith('#uuid'):
            # uuid 帮助
            if info.content == '#uuid':
                bot.reply(info, uuid_help)
            # 查看uuid 匹配表
            elif len(command)>1 and command[1] == '列表':
                bot.reply(info, "uuid匹配如下：\n"+'\n'.join([str(k)+'-'+str(v)+'-'+self.data[v] for k,v in self.uuid_qqid.items() if v in self.data]))
            # 更新匹配表
            elif len(command)>1 and command[1] == '重载':
                # 白名单表 [{uuid:value, name: value}]
                temp = self.loading_file(self.config["dict_address"]['whitelist'])
                # 解压白名单表
                self.whitelist = {list(i.values())[0]:list(i.values())[1] for i in temp}
                self.match_id()
                bot.reply(info, '已重新匹配~')
            # 更改白名单名字
            elif len(command)>1 and command[1] in ['修改','更改','更新']:
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
        elif info.content.startswith('#名字'):
            if info.content == '#名字':
                bot.reply(info, name_help)
            elif len(command)>1 and command[1] == '开':
                self.config['command']['name'] = True
    
                # 创造全局变量
                global past_info,past_bot
                past_info = info
                past_bot = bot

                self.set_number_as_name(server, info, bot)

                bot.reply(info, "显示游戏内人数已开启")
            elif len(command)>1 and command[1] == '关':
                self.config['command']['name'] = False
                for gid in self.config['group_id']:
                    bot.set_group_card(gid, int(info.self_id), " ")
                bot.reply(info, "显示游戏内人数已关闭")     

        elif info.content.startswith('#审核'):
            if info.content == '#审核':
                bot.reply(info, shenhe_help)
            elif len(command)>1 and command[1] == '开':
                self.config['command']['shenhe'] = True
                bot.reply(info, '自动审核开启')
            elif len(command)>1 and command[1] == '关':
                self.config['command']['shenhe'] = False
                bot.reply(info, '自动审核关闭')
            elif len(command)>1 and command[1] == '添加':
                if len(command) == 4 and command[3] not in self.shenheman:
                    self.shenheman[command[3]] = command[2] # 别名：QQ号
                    bot.reply(info,style[self.style]['add_success'])
                elif command[3] in self.shenheman:
                    bot.reply(info,'已存在该别名')
            elif command[1] == '删除' and len(command) > 2:
                
                if command[2] in self.shenheman.values():
                    for k,v in self.shenheman.items():
                        if v == command[2]:
                            del self.shenheman[k]
                    bot.reply(info,style[self.style]['delete_success'])
                else:
                    bot.reply(info,'审核员不存在哦！')
            elif len(command)>1 and command[1] == '列表':
                temp = defaultdict(list)
                for name,qq_hao in self.shenheman.items():
                    temp[qq_hao].append(name)
                bot.reply(info, "有如下审核员：\n"+"\n".join([k+'-'+",".join(v) for k,v in temp.items()]))

    # 群指令
    def group_command(self, server, info: Info, bot, command:list):
        if info.content == '#帮助':  # 群帮助
            bot.reply(info, group_help_msg)
        elif self.config['command']['mc'] and command[0] == 'mc': # qq发送到游戏内消息
            user_id = str(info.user_id)
            message = info.content[4:]
            # 检测绑定
            if user_id in self.data.keys():
                # 正常转发
                server.say(f'§6[QQ] §a[{self.find_game_name(user_id, bot, info.source_id)}] §f{message}')
                # 回复关键词
                response = self.key_word_ingame.check_response(message)
                if response: 
                    bot.reply(info, response)
                    server.say(f'§a[机器人] §f{response}')
            else:
                bot.reply(info, f'[CQ:at,qq={user_id}][CQ:image,file=file:///{os.getcwd()+"/plugins/GUGUbot/bound.jpg"}]')
        # 绑定功能
        elif len(command) == 2 and command[0] == '绑定':
            user_id = str(info.user_id)
            # 已绑定
            if user_id in self.data.keys():
                _id = self.data[user_id]
                bot.reply(info, f'[CQ:at,qq={user_id}] 您已绑定ID: {_id}, 请联系管理员修改')
            # 未绑定
            else:
                self.data[user_id] = command[1]
                self.data.save()
                bot.reply(info, f'[CQ:at,qq={user_id}] 已成功绑定')
                # 更换群名片
                bot.set_group_card(info.user_id,user_id, self.data[user_id])
                # 自动加白名单
                if self.config['whitelist_add_with_bound']:
                    server.execute(f'whitelist add {command[1]}')
                    bot.reply(info, f'[CQ:at,qq={user_id}] 已将您添加到服务器白名单')
                    # 重载白名单
                    server.execute(f'whitelist reload')
                    while command[1] not in self.whitelist:
                        # 白名单表 [{uuid:value, name: value}]
                        temp = self.loading_file(self.config["dict_address"]['whitelist'])
                        # 解压白名单表
                        self.whitelist = {list(i.values())[0]:list(i.values())[1] for i in temp}
                        time.sleep(5)
                    # 重新匹配
                    self.match_id()
        # 机器人风格相关
        elif command[0] == '风格':
            # 风格帮助
            if info.content == '#风格':
                bot.reply(info, style_help)
            # 风格列表
            elif command[1] == '列表':
                bot.reply(info, "现有如下风格：\n"+'\n'.join(style.keys()))
            # 切换风格
            elif command[1] in style.keys():
                self.style = command[1]
                bot.reply(info, f'已切换为 {self.style}')

    # 退群处理
    @addTextToImage
    def notification(self, server, info: Info, bot):
        # 指定群里 + 是退群消息
        if info.user_id in self.config['group_id'] \
            and info.sub_type == 'group_decrease':
            user_id = str(info.user_id)
            if user_id in self.data.keys():
                server.execute(f"whitelist remove {self.data[user_id]}")
                bot.reply(info, f"{self.data[user_id]}已退群，白名单同步删除")
                del self.data[user_id]

    # 进群处理
    @addTextToImage
    def on_qq_request(self,server, info: Info, bot):
        if info.source_id in self.config["group_id"] \
            and info.source_type == "group" and self.config["command"]["shenhe"]:
            # 获取名称
            stranger_name = requests.post(f"http://{self.host}:{self.port}/get_stranger_info",
                json = {
                    "user_id":info.user_id
            }).json()["data"]["nickname"]
            # 审核人
            at_id = self.shenheman[info.comment] if info.comment in self.shenheman else self.config['admin_id'][0]
            # 通知
            bot.reply(info, f"喵！[CQ:at,qq={at_id}] {stranger_name} 申请进群, 请审核")
            server.say(f'§6[QQ] §b[@{at_id}] §f{stranger_name} 申请进群, 请审核')
            self.shenhe[at_id].append((stranger_name, info.flag, info.sub_type))
                        
    # 匹配uuid qqid
    def match_id(self) -> None:
        # uuid:qq_id
        self.uuid_qqid = {}
        # 解压whitelist
        whitelist_dict = {}
        for uuid, game_name in self.whitelist.items():
            whitelist_dict[game_name] = uuid   
        # 匹配    
        for qq_id, qq_name in self.data.items():
            if '(' in qq_name or '（' in qq_name:
                qq_name = qq_name.split('(')[0].split('（')[0]
            if qq_name in whitelist_dict:
                self.uuid_qqid[whitelist_dict[qq_name]] = qq_id

    # 转发消息
    @addTextToImage
    def send_msg_to_mc(self, server:PluginServerInterface, info: Info, bot):
        self.server = server
        # 判断是否转发
        if info.content[0] != '#' and self.config['forward']['qq_to_mc'] \
            and info.source_id in self.config['group_id']:
            # 判断是否绑定
            if  str(info.user_id) not in self.data.keys():
                # 提示绑定
                bot.reply(info, f'[CQ:at,qq={info.user_id}][CQ:image,file=file:///{os.getcwd()+"/plugins/GUGUbot/data/bound.jpg"}]')
                return 
            # 如果开启违禁词
            if self.config['command']['ban_word']:
                reason = self.ban_word.check_ban(info.content)
                # 包含违禁词 -> 撤回 + 提示 + 不转发
                if reason:
                    bot.delete_msg(info.message_id)
                    bot.reply(info, style[self.style]['ban_word_find'].format(reason[1]))
                    return 
            user_id = str(info.user_id)
            # 检测关键词
            if self.config['command']['key_word']:
                # 检测到关键词 -> 转发原文 + 转发回复
                if info.content in self.key_word.data:
                    server.say(f'§6[QQ] §a[{self.find_game_name(user_id, bot, info.source_id)}] §f{info.content}')
                    bot.reply(info,self.key_word.data[info.content])
                    # 过滤图片
                    is_picture = self.key_word.data[info.content][:9] != '[CQ:image'
                    server.say(f'§6[QQ] §a[机器人] §f{self.key_word.data[info.content] if not is_picture else "图片"}')
                # 添加图片
                elif info.user_id in self.picture_record_dict and info.raw_content[:9]=='[CQ:image':
                    # save pic
                    pattern = "\[CQ:image.+url=(.+)\]"
                    try:
                        url = re.match(pattern, info.raw_content).groups()[-1]
                        response = requests.get(url)
                        if not os.path.exists("./config/GUGUbot/image/"):
                            os.makedirs("./config/GUGUbot/image/")
                        with open(f"./config/GUGUbot/image/{self.picture_record_dict[info.user_id]}.jpg", "wb") as f:
                            f.write(response.content)
                        # save dict
                        self.key_word.data[self.picture_record_dict[info.user_id]]=re.sub(pattern, "[CQ:image\\1file=file:///{}]".format(f"./config/GUGUbot/image/{self.picture_record_dict[info.user_id]}.jpg"), info.raw_content)
                        del self.picture_record_dict[info.user_id]
                        bot.reply(info, style[self.style]['add_success'])
                    except Exception as e:
                        bot.reply(info, e)
                # @ 模块
                elif '@' in info.content:
                    def _get_name(qq_id:str):
                        if str(qq_id) in self.data:
                            return self.find_game_name(qq_id, bot, info.source_id)
                        target_data = bot.get_group_member_info(info.source_id, qq_id).json()['data']
                        target_name = target_data['card'] if target_data['card'] != '' else target_data['nickname']
                        return f"{target_name}(未绑定)"
                    sender = _get_name(info.user_id)
                    # reply
                    if "[CQ:reply,id=" in info.content:
                        pattern = r"(?:\[CQ:reply,id=(\d+)\])(?:\[@(\d+)\])(.*)"
                        match_result = re.match(pattern, info.content, re.DOTALL).groups()
                        # get receiver name
                        query = {'message_id': match_result[0]}
                        pre_message = requests.post(f'http://{self.host}:{self.port}/get_msg',json=query).json()['data']['message']
                        pattern = r"\[@(\d+)\].*|\[CQ:at,qq=(\d+)\].*"
                        receiver_result = re.match(pattern, pre_message, re.DOTALL).groups()
                        receiver_id = str(receiver_result[0]) if receiver_result[0] else str(receiver_result[1])
                        receiver = _get_name(receiver_id)
                        server.say(f'§6[QQ] §a[{sender}] §b[@{receiver}] §f{match_result[-1]}')
                        return 
                    # only @
                    at_pattern = r"\[@(\d+)\]|\[CQ:at,qq=(\d+)\]"
                    sub_string = re.sub(at_pattern, lambda id: f"§b[@{str(_get_name(id.groups()[0])) if id.groups()[0] else str(id.groups()[1])}]", info.raw_content)
                    server.say(f'§6[QQ] §a[{sender}]§f {sub_string}')
                # 普通消息
                else: 
                    # 提取链接中标题
                    if info.content[:8] == '[CQ:json':
                        info.content = '[链接]'+info.content.split('"desc":"')[2].split('&#44')[0][1:]
                    server.say(f'§6[QQ] §a[{self.find_game_name(str(user_id), bot, info.source_id)}] §f{info.content}')
            
    # 转发消息
    def send_msg_to_qq(self, server:PluginServerInterface, info:Info):
        if info.is_player and self.config['forward']['mc_to_qq']:
            # check ban
            if self.config['command']['ban_word']:
                response = self.ban_word.check_ban(info.content)
                if response:
                    temp = '{"text":"' + '消息包含违禁词无法转发到群聊请修改后重发，维护和谐游戏人人有责。\n违禁理由：'+\
                        response[1] + '","color":"gray","italic":true}'
                    self.server.execute(f'tellraw {info.player} {temp}')
                    return
            # 游戏内关键词添加
            if self.config['command']['ingame_key_word'] and info.content[:6] == '!!add ':
                temp = info.content[6:].split(' ',1)
                if len(temp) == 2 and temp[0] not in self.key_word_ingame.data:
                    self.key_word_ingame.data[temp[0]] = temp[1]
                    self.server.say(style[self.style]['add_success'])
                else:
                    self.server.say('关键词重复或者指令无效~')
            # 游戏内关键词删除
            elif self.config['command']['ingame_key_word'] and info.content[:6] == '!!del ':
                if info.content[6:] in self.key_word_ingame.data:
                    del self.key_word_ingame.data[info.content[6:]]
                    self.server.say(style[self.style]['delete_success'])
                else:
                    self.server.say('未找到对应关键词~')
            # 检测关键词
            elif info.content[:2] not in [ '@ ','!!']:
                # 转发原句
                roll_number = random.randint(0, 999+1)
                template_index = roll_number % (len(mc2qq_template)-1) if roll_number >= 3 else -1
                message = mc2qq_template[template_index].format(info.player, info.content)
                self.send_msg_to_all_qq(message)
                if self.config['command']['ingame_key_word'] and info.content in self.key_word_ingame:
                    # 游戏内回复
                    response = self.key_word_ingame.check_response(info.content)
                    self.server.say(f'§a[机器人] §f{response}')
                
    # 游戏内指令发送qq
    def ingame_command_qq(self,src,ctx):
        if self.config['command']['qq']:
            player = src.player if src.is_player else 'Console'
            if self.config['command']['ban_word']:
                reason = self.ban_word.check_ban(ctx["message"])
                if reason:
                    temp = '{"text":"' +\
                        '消息包含违禁词无法转发到群聊请修改后重发，维护和谐游戏人人有责。\n违禁理由：'+\
                        reason[1] + '","color":"gray","italic":true}'
                    self.server.execute(f'tellraw {player} {temp}')
                    return
            # 正常转发
            self.send_msg_to_all_qq(f'[{player}] {ctx["message"]}')
            # 检测关键词
            if ctx['message'] in self.key_word:
                self.send_msg_to_all_qq(f'{self.key_word[ctx["message"]]}')
                self.server.say(f'§a[机器人] §f{self.key_word[ctx["message"]]}')

    # 游戏内@
    def ingame_at(self,src,ctx):
        if  self.config['command']['qq']:
            # get player name or system 
            player = src.player if src.is_player else 'Console'
            qq_user_id = ctx['QQ(name/id)'] if ctx['QQ(name/id)'].isdigit() else self.member_dict[ctx['QQ(name/id)']]
            # check ban
            if self.config["command"]["ban_word"]:
                response = self.ban_word.check_ban(ctx['message'])
                if response:
                    temp = '{"text":"' + '消息包含违禁词无法转发到群聊请修改后重发，维护和谐游戏人人有责。违禁理由：'+ response[1] + '","color":"gray","italic":true}'
                    self.server.execute(f'tellraw {player} {temp}')
                    return 
            # send
            self.send_msg_to_all_qq(f'[{player}] [CQ:at,qq={qq_user_id}] {ctx["message"]}')

    # 游戏内@ 推荐
    def ingame_at_suggestion(self):
        # 添加绑定名单
        self.member_dict = {v:k for k,v in self.data.items()}
        suggest_content = [v for v in self.data.values()]
        # 添加群内信息
        try: 
            group_raw_info = []
            for group_id in self.config['group_id']:
                group_raw_info.append(requests.post(f'http://{self.host}:{self.port}/get_group_member_list', json={
                    'group_id': group_id
                }))
            unpack = [i.json()['data'] for i in group_raw_info if i.json()['status'] == 'ok']
        except:
            unpack = []
        for group in unpack:
            for member in group:
                self.member_dict[member['nickname']] = member['user_id']
                self.member_dict[member['card']] = member['user_id']
                suggest_content.append(member['card'])
                suggest_content.append(member['nickname'])
                suggest_content.append(str(member['user_id']))
        return suggest_content

    ################################################################################
    # 辅助functions
    ################################################################################
    
    
    # 通过QQ号找到绑定的游戏ID
    def find_game_name(self, qq_id:str, bot, group_id:str=None) -> str:
        group_id = self.config['group_id'][0]
        qq_uuid = {v:k for k,v in self.uuid_qqid.items()}
        # 未启用白名单
        if not self.config['command']['whitelist']:
            return self.data[qq_id]
        # 如果绑定 且 启动白名单
        if qq_id in qq_uuid:
            uuid = qq_uuid[qq_id]
            if uuid in self.whitelist:
                return self.whitelist[uuid]
        target_data = bot.get_group_member_info(group_id, qq_id).json()['data']
        target_name = target_data['card'] if target_data['card'] != '' else target_data['nickname']
        return f'{target_name}(名字不匹配)'
    
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

    # 转发消息到指定群
    def send_group_msg(self, msg, group):
        requests.post(f'http://{self.host}:{self.port}/send_group_msg', json={
            'group_id': group,
            'message': msg
        })

    # 转发消息到所有群
    def send_msg_to_all_qq(self, msg:str):
        for group in self.config['group_id']:
            self.send_group_msg(msg, group)

    # 机器人名称显示游戏内人数
    def set_number_as_name(self, server:PluginServerInterface, info: Info, bot):
        if self.rcon:
            number = len([i for i in self.rcon.send_command("list").split(": ")[-1].split(", ") if "假的" not in i])
        else:
            content = requests.get(f'https://api.miri.site/mcPlayer/get.php?ip={self.config["game_ip"]}&port={self.config["game_port"]}').json()
            number = len([i["name"] for i in content['sample'] if i["name"] in self.whitelist.values()])
        name = " "
        if number != 0:
            name = "在线人数: {}".format(number)
            
        for gid in self.config['group_id']:
            data = {
            'group_id': gid,
            'user_id': info.self_id,
            'card': name
            }
            requests.post(
            f'http://{self.host}:{self.port}/set_group_card',
            json=data)
