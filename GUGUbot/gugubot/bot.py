#encoding=utf-8
# The definition of the QQ Chat robot:
from .ban_word_system import ban_word_system
from .key_word_system import key_word_system
from .start_command_system import start_command_system
from .table import table
from ..data.text import *
from aiocqhttp import CQHttp, Event
from collections import defaultdict
from mcdreforged.api.types import PluginServerInterface, Info
import json
import os
import re
import requests
import time

event_loop = None

class qbot(object):
    def __init__(self, server, config, data, host, port, bot):
        # 添加初始参数
        self.server = server
        self.config = config
        self.data = data
        self.host = host
        self.port = port
        self.bot = bot
        self.picture_record_dict = {}
        self.shenhe = defaultdict(list)
        self.style = '正常'
        self.suggestion = self.ingame_at_suggestion()
        # 读取文件
        self.loading_dicts()

    # 读取文件
    def loading_dicts(self) -> None:
        self.start_command   = start_command_system(self.config["dict_address"]["start_command_dict"])                     # 开服指令
        self.key_word        = key_word_system(self.config["dict_address"]['key_word_dict'])                               # QQ 关键词
        self.key_word_ingame = key_word_system(self.config["dict_address"]['key_word_ingame_dict'], ingame_key_word_help)  # MC 关键词
        self.ban_word        = ban_word_system(self.config["dict_address"]['ban_word_dict'])                               # 违禁词
        self.uuid_qqid       = table(self.config["dict_address"]['uuid_qqid'])                                             # uuid - qqid 表
        temp = self.loading_file(self.config["dict_address"]['whitelist'])                      # 白名单表 [{uuid:value, name: value}]
        self.whitelist = {list(i.values())[0]:list(i.values())[1] for i in temp}                # 解压白名单表
        self.shenheman = table(self.config["dict_address"]['shenheman'])                        # 群审核人员

    # 通用QQ 指令
    def on_qq_command(self,server, bot:CQHttp, event:Event):
        # 过滤非关注的消息
        if not (event.user_id in self.config['group_id'] or
            event.user_id in self.config['admin_id']) or event.raw_message[0] != '#':
            return 
        command = event.content.split(' ')
        command[0] = command[0].replace('#', '')
        # 检测违禁词
        if self.config['command']['ban_word'] and event.detail_type == 'group':
            ban_result = self.ban_word.check_ban(' '.join(command))
            if ban_result:
                self.bot.delete_msg(event.message_id)
                self.reply(event, style[self.style]['ban_word_find'].format(ban_result[1]))
                return 

        # 玩家列表
        if self.config['command']['list'] and (command[0] in ['玩家列表','玩家'] or command[0] in ['假人列表','假人']):
            content = requests.get(f'https://api.miri.site/mcPlayer/get.php?ip={self.config["game_ip"]}&port={self.config["game_port"]}').json()
            player = command[0] in ['玩家','玩家列表']
            if player: # 过滤假人
                t_player = [i["name"] for i in content['sample'] if i["name"] in self.whitelist.values()]
            else: # 过滤真人
                t_player = [i["name"] for i in content['sample'] if i["name"] not in self.whitelist.values()] 

            if len(t_player) == 0 :
                respond = style[self.style]['no_player_ingame'] if player else '没有假人在线哦！'
            else:
                t_player.sort() # 名字排序
                respond = style[self.style]['player_list'].format(
                    len(t_player),
                    '玩家' if player else '假人',
                    ', '.join(t_player))
            self.reply(event, respond)

        # 添加关键词
        elif self.config['command']['key_word'] and command[0] in ["列表",'添加','删除']:
            self.key_word.handle_command(event.content, bot, event, style=self.style)

        # 游戏内关键词
        elif self.config['command']['ingame_key_word'] and command[0] == '游戏关键词':
            if self.config['command']['ban_word']:
                ban_result = self.ban_word.check_ban(''.join(command[1:]))
                if ban_result:
                    self.bot.delete_msg(event.message_id)
                    self.reply(event, style[self.style]['ban_word_find'].format(ban_result[1]))
                    return 
            self.key_word_ingame.handle_command(event.content, bot, event, style=self.style)

        # 添加关键词图片
        elif self.config['command']['key_word'] and command[0] == '添加图片' and len(command)>1:
            if command[1] not in self.key_word.data and event.user_id not in self.picture_record_dict:
                ban_result = self.ban_word.check_ban(command[1])
                if ban_result:
                    self.bot.delete_msg(event.message_id)
                    self.reply(event, style[self.style]['ban_word_find'].format(ban_result[1]))
                    return 
                else: # 正常添加
                    self.picture_record_dict[event.user_id] = command[1]
                    self.reply(event, '请发送要添加的图片~')
            elif command[1] in self.key_word.data:
                self.reply(event, '已存在该关键词~')
            else:
                self.reply(event,'上一个关键词还未绑定，添加哒咩！') 

        # 审核通过
        elif self.config['command']['shenhe'] and command[0] == '同意' and len(self.shenhe[event.user_id]) > 0:
            self.bot.set_group_add_request(self.shenhe[event.user_id][0][1],self.shenhe[event.user_id][0][2],True)
            with open(self.config["dict_address"]['shenhe_log'],'a+',encoding='utf-8') as f:
                f.write(" ".join([time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    self.shenhe[event.user_id][0][0],
                    event.user_id,
                    '通过'])+'\n')
            self.reply(event,f"已通过{self.shenhe[event.user_id][0][0]}的申请awa")
            self.shenhe[event.user_id].pop(0)
        # 审核不通过
        elif self.config['command']['shenhe'] and command[0] == '拒绝' and len(self.shenhe[event.user_id]) > 0:
            self.bot.set_group_add_request(self.shenhe[event.user_id][0][1],self.shenhe[event.user_id][0][2],False)
            with open(self.config["dict_address"]['shenhe_log'],'a+',encoding='utf-8') as f:
                f.write(" ".join([time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    self.shenhe[event.user_id][0][0],
                    event.user_id,
                    '拒绝'])+'\n')
            self.reply(event,f"已拒绝{self.shenhe[event.user_id][0][0]}的申请awa")
            self.shenhe[event.user_id].pop(0)
        
        if event.detail_type == 'private':
            self.private_command(server, bot, event, command)
        elif event.detail_type == 'group':
            self.group_command(server, bot, event, command)

    # 管理员指令
    def private_command(self, server, bot:CQHttp, event:Event, command):
        # 全部帮助菜单
        if event.content == '#帮助':
            self.reply(event, admin_help_msg)
        # bound 帮助菜单
        elif event.content.startswith('#绑定'):
            if event.content == '#绑定':
                self.reply(event, bound_help)
            # 已绑定的名单    
            elif len(command) == 2 and command[1] == '列表':
                bound_list = [f'{a} - {b}' for a, b in self.data.items()]
                reply_msg = ''
                for i in range(0, len(bound_list)):
                    reply_msg += f'{i + 1}. {bound_list[i]}\n'
                reply_msg = '还没有人绑定' if reply_msg == '' else reply_msg
                self.reply(event, reply_msg)
            # 查寻绑定的ID
            elif len(command) == 3 and command[1] == '查询':
                if command[2] in self.data:
                    self.reply(event,
                            f'{command[2]} 绑定的ID是{self.data[command[2]]}')
                else:
                    self.reply(event, f'{command[2]} 未绑定')
            # 解除绑定
            elif len(command) == 3 and command[1] == '解绑':
                if command[2] in self.data:
                    del self.data[command[2]]
                    self.data.save()
                    self.reply(event, f'已解除 {command[2]} 绑定的ID')
                else:
                    self.reply(event, f'{command[2]} 未绑定')
            # 绑定ID
            elif len(command) == 3 and command[1].isdigit():
                self.data[command[1]] = command[2]
                self.data.save()
                self.reply(event, '已成功绑定')

        # 白名单
        elif event.content.startswith('#白名单'):
            if event.content == '#白名单':
                self.reply(event, whitelist_help)
            # 执行指令
            elif len(command)>1 and command[1] in ['添加', '删除','移除', '列表', '开', '关', '重载']:
                if command[1] == '添加':
                    server.execute(f'/whitelist add {command[2]}')
                    self.reply(event, style[self.style]['add_success'])
                    while command[2] not in self.whitelist:
                        temp = self.loading_file(self.config["dict_address"]['whitelist'])
                        # 解压白名单表
                        self.whitelist = {list(i.values())[0]:list(i.values())[1] for i in temp}
                        time.sleep(2)
                    self.match_id()
                elif command[1] in ['删除','移除']:
                    server.execute(f'/whitelist remove {command[2]}')
                    self.reply(event ,style[self.style]['delete_success'])
                    temp = self.loading_file(self.config["dict_address"]['whitelist'])
                    # 解压白名单表
                    self.whitelist = {list(i.values())[0]:list(i.values())[1] for i in temp}
                elif command[1] == '开':
                    server.execute(f'/whitelist on')
                    self.reply(event, '白名单已开启！')
                elif command[1] == '关':
                    server.execute(f'/whitelist off')
                    self.reply(event, '白名单已关闭！')
                elif command[1] == '重载':
                    server.execute(f'/whitelist reload')
                    temp = self.loading_file(self.config["dict_address"]['whitelist'])
                    # 解压白名单表
                    self.whitelist = {list(i.values())[0]:list(i.values())[1] for i in temp}
                    self.reply(event, '白名单已重载~')
                else:
                    self.reply(event,'白名单如下：\n'+'\n'.join(sorted(self.whitelist.values())))
                    
        # 启动指令相关
        elif event.content.startswith('#启动指令'):
            # 开启开服指令
            if len(command)>1 and command[1] == '开':
                self.config['command']['start_command'] = True
                self.reply(event, '已开启开服指令！')
            # 关闭开服指令
            elif len(command)>1 and command[1] == '关':
                self.config['command']['start_command'] = False
                self.reply(event, '已关闭开服指令！')
            else:
                self.start_command.handle_command(event.content, bot, event, style=self.style)
              
        # 违禁词相关
        elif event.content.startswith('#违禁词'):
            if len(command)>1 and command[1] == '开':
                self.config['command']['ban_word'] = True
                self.reply(event, '已开启违禁词！')
            # 关闭违禁词
            elif len(command)>1 and command[1] == '关':
                self.config['command']['ban_word'] = False
                self.reply(event, '已关闭违禁词！')
            else:
                self.ban_word.handle_command(event.content, bot, event, style=self.style)
        
        # 关键词相关
        elif event.content.startswith('#关键词'):
            # 开启关键词
            if len(command)>1 and command[1] in ['开','on']:
                self.config['command']['key_word'] = True
                self.reply(event, '已开启关键词！')
            # 关闭关键词
            elif len(command)>1 and command[1] in ['关', 'off']:
                self.config['command']['key_word'] = False
                self.reply(event, '已关闭关键词！')
            else:
                self.key_word.handle_command(event.content, bot, event, style=self.style)
            
        # 游戏内关键词相关
        elif event.content.startswith('#游戏关键词'):
            # 开启游戏关键词
            if len(command)>1 and command[1] == '开':
                self.config['command']['ingame_key_word'] = True
                self.reply(event, '已开启游戏关键词！')
            # 关闭游戏关键词
            elif len(command)>1 and command[1] == '关':
                self.config['command']['ingame_key_word'] = False
                self.reply(event, '已关闭游戏关键词！')
            else:
                self.key_word_ingame.handle_command(event.content, bot, event, style=self.style)

        # uuid匹配相关
        elif event.content.startswith('#uuid'):
            # uuid 帮助
            if event.content == '#uuid':
                self.reply(event, uuid_help)
            # 查看uuid 匹配表
            elif len(command)>1 and command[1] == '列表':
                self.reply(event, "uuid匹配如下：\n"+'\n'.join([str(k)+'-'+str(v)+'-'+self.data[v] for k,v in self.uuid_qqid.items() if v in self.data]))
            # 更新匹配表
            elif len(command)>1 and command[1] == '重载':
                # 白名单表 [{uuid:value, name: value}]
                temp = self.loading_file(self.config["dict_address"]['whitelist'])
                # 解压白名单表
                self.whitelist = {list(i.values())[0]:list(i.values())[1] for i in temp}
                self.match_id()
                self.reply(event, '已重新匹配~')
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
                        self.reply(event,'已将 {} 改名为 {}'.format(pre_name,cur_name))
                        with open(self.config["dict_address"]['whitelist'],'w') as f:
                            whitelist = json.dump(whitelist,f) # [{uuid:value,name:value}]
                        self.match_id()
                        self.reply(event, '已重新匹配~')
                        break
                if not changed:
                    self.reply(event, '未找到对应名字awa！')                

        # 机器人名字 <- 服务器人数
        elif event.content.startswith('#名字'):
            if event.content == '#名字':
                self.reply(event, name_help)
            elif len(command)>1 and command[1] == '开':
                self.config['command']['name'] = True
    
                # 创造全局变量
                global past_event,past_bot
                past_event = event
                past_bot = bot

                self.set_number_as_name(server, bot, event)

                self.reply(event, "显示游戏内人数已开启")
            elif len(command)>1 and command[1] == '关':
                self.config['command']['name'] = False
                for gid in self.config['group_id']:
                    self.bot.set_group_card(gid, int(event.self_id), " ")
                self.reply(event, "显示游戏内人数已关闭")     

        elif event.content.startswith('#审核'):
            if event.content == '#审核':
                self.reply(event, shenhe_help)
            elif len(command)>1 and command[1] == '开':
                self.config['command']['shenhe'] = True
                self.reply(event, '自动审核开启')
            elif len(command)>1 and command[1] == '关':
                self.config['command']['shenhe'] = False
                self.reply(event, '自动审核关闭')
            elif len(command)>1 and command[1] == '添加':
                if len(command) == 4 and command[3] not in self.shenheman:
                    self.shenheman[command[3]] = command[2] # 别名：QQ号
                    self.reply(event,style[self.style]['add_success'])
                elif command[3] in self.shenheman:
                    self.reply(event,'已存在该别名')
            elif command[1] == '删除' and len(command) > 2:
                
                if command[2] in self.shenheman.values():
                    for k,v in self.shenheman.items():
                        if v == command[2]:
                            del self.shenheman[k]
                    self.reply(event,style[self.style]['delete_success'])
                else:
                    self.reply(event,'审核员不存在哦！')
            elif len(command)>1 and command[1] == '列表':
                temp = defaultdict(list)
                for name,qq_hao in self.shenheman.items():
                    temp[qq_hao].append(name)
                self.reply(event, "有如下审核员：\n"+"\n".join([k+'-'+",".join(v) for k,v in temp.items()]))

    # 群指令
    def group_command(self, server, bot:CQHttp, event:Event, command):
        if event.content == '#帮助':  # 群帮助
            self.reply(event, group_help_msg)
        elif self.config['command']['mc'] and command[0] == 'mc': # qq发送到游戏内消息
            user_id = str(event.user_id)
            message = event.content[4:]
            # 检测绑定
            if user_id in self.data.keys():
                # 正常转发
                server.say(f'§6[QQ] §a[{self.find_game_name(user_id, event.group_id)}] §f{message}')
                # 回复关键词
                response = self.key_word_ingame.check_response(message)
                if response: 
                    self.reply(event, response)
                    server.say(f'§a[机器人] §f{response}')
            else:
                self.reply(event, f'[CQ:at,qq={user_id}][CQ:image,file=file:///{os.getcwd()+"/plugins/GUGUbot/bound.jpg"}]')
        # 绑定功能
        elif len(command) == 2 and command[0] == '绑定':
            user_id = str(event.user_id)
            # 已绑定
            if user_id in self.data.keys():
                _id = self.data[user_id]
                self.reply(event, f'[CQ:at,qq={user_id}] 您已绑定ID: {_id}, 请联系管理员修改')
            # 未绑定
            else:
                self.data[user_id] = command[1]
                self.data.save()
                self.reply(event, f'[CQ:at,qq={user_id}] 已成功绑定')
                # 更换群名片
                self.bot.set_group_card(event.user_id,user_id, self.data[user_id])
                # 自动加白名单
                if self.config['whitelist_add_with_bound']:
                    server.execute(f'whitelist add {command[1]}')
                    self.reply(event, f'[CQ:at,qq={user_id}] 已将您添加到服务器白名单')
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
            if event.content == '#风格':
                self.reply(event, style_help)
            # 风格列表
            elif command[1] == '列表':
                self.reply(event, "现有如下风格：\n"+'\n'.join(style.keys()))
            # 切换风格
            elif command[1] in style.keys():
                self.style = command[1]
                self.reply(event, f'已切换为 {self.style}')

    # 退群处理
    def notification(self, server, bot:CQHttp, event:Event):
        # 指定群里 + 是退群消息
        if event.user_id in self.config['group_id'] \
            and event.sub_type == 'group_decrease':
            user_id = str(event.user_id)
            if user_id in self.data.keys():
                server.execute(f"whitelist remove {self.data[user_id]}")
                self.reply(event, f"{self.data[user_id]}已退群，白名单同步删除")
                del self.data[user_id]
                self.data.save()

    # 进群处理
    def on_qq_request(self,server, bot:CQHttp, event:Event):
        if event.group_id in self.config["group_id"] \
            and event.detail_type == "group" and self.config["command"]["shenhe"]:
            # 获取名称
            stranger_name = requests.post(f"http://{self.host}:{self.port}/get_stranger_info",
                json = {
                    "user_id":event.user_id
            }).json()["data"]["nickname"]
            # 审核人
            at_id = self.shenheman[event.comment] if event.comment in self.shenheman else self.config['admin_id'][0]
            # 通知
            self.reply(event, f"喵！[CQ:at,qq={at_id}] {stranger_name} 申请进群, 请审核")
            server.say(f'§6[QQ] §b[@{at_id}] §f{stranger_name} 申请进群, 请审核')
            self.shenhe[at_id].append((stranger_name, event.flag, event.sub_type))
                        
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
    def send_msg_to_mc(self, server:PluginServerInterface, bot:CQHttp, event:Event):
        self.server = server
        # 判断是否转发
        if event.content[0] != '#' and self.config['forward']['qq_to_mc'] \
            and event.group_id in self.config['group_id']:
            # 判断是否绑定
            if  str(event.user_id) not in self.data.keys():
                # 提示绑定
                self.reply(event, f'[CQ:at,qq={event.user_id}][CQ:image,file=file:///{os.getcwd()+"/plugins/GUGUbot/bound.jpg"}]')
                return 
            # 如果开启违禁词
            if self.config['command']['ban_word']:
                reason = self.ban_word.check_ban(event.content)
                # 包含违禁词 -> 撤回 + 提示 + 不转发
                if reason:
                    self.bot.delete_msg(event.message_id)
                    self.reply(event, style[self.style]['ban_word_find'].format(reason[1]))
                    return 
            user_id = str(event.user_id)
            # 检测关键词
            if self.config['command']['key_word']:
                # 检测到关键词 -> 转发原文 + 转发回复
                if event.content in self.key_word.data:
                    server.say(f'§6[QQ] §a[{self.find_game_name(user_id, event.group_id)}] §f{event.content}')
                    self.reply(event,self.key_word.data[event.content])
                    # 过滤图片
                    is_picture = self.key_word.data[event.content][:9] != '[CQ:image'
                    server.say(f'§6[QQ] §a[机器人] §f{self.key_word.data[event.content] if not is_picture else "图片"}')
                # 添加图片
                elif event.user_id in self.picture_record_dict and event.raw_message[:9]=='[CQ:image':
                    # save pic
                    pattern = "^\[CQ:image.+url=(.+)\]"
                    url = re.match(pattern, url).groups()[-1]
                    response = requests.get(url)
                    if not os.path.exists("./config/GUGUbot/image/"):
                        os.makedirs("./config/GUGUbot/image/")
                    with open(f"./config/GUGUbot/image/{self.picture_record_dict[event.user_id]}.jpg", "wb") as f:
                        f.write(response.content)
                    # save dict
                    self.key_word.data[self.picture_record_dict[event.user_id]]=re.sub(pattern, "[CQ:image\\1file=file:///{}]".format(f"./config/GUGUbot/image/{self.picture_record_dict[event.user_id]}.jpg"), event.raw_message)
                    del self.picture_record_dict[event.user_id]
                    self.reply(event, style[self.style]['add_success'])
                # @ 模块
                elif '@' in event.content:
                    def _get_name(qq_id:str):
                        if str(qq_id) in self.data:
                            return self.find_game_name(qq_id, event.group_id)
                        target_data = self.bot.get_group_member_info(event.group_id, qq_id).json()['data']
                        target_name = target_data['card'] if target_data['card'] != '' else target_data['nickname']
                        return f"{target_name}(未绑定)"
                    sender = _get_name(event.user_id)
                    # reply
                    if "[CQ:reply,id=" in event.content:
                        pattern = r"(?:\[CQ:reply,id=(\d+)\])(?:\[@(\d+)\])(.*)"
                        match_result = re.match(pattern, event.content, re.DOTALL).groups()
                        # get receiver name
                        query = {'message_id': match_result[0]}
                        pre_message = requests.post(f'http://{self.host}:{self.port}/get_msg',json=query).json()['data']['message']
                        receiver = pre_message.split(']')[0].split('&')[1][4:]
                        server.say(f'§6[QQ] §a[{sender}] §b[@{receiver}] §f{match_result[-1]}')
                        return 
                    # only @
                    at_pattern = r"\[@(\d+)\]"
                    sub_string = re.sub(at_pattern, lambda id: f"§b[@{_get_name(id)}]", event.raw_message)
                    server.say(f'§6[QQ] §a[{sender}]§f {sub_string}')
                # 普通消息
                else: 
                    # 提取链接中标题
                    if event.content[:8] == '[CQ:json':
                        event.content = '[链接]'+event.content.split('"desc":"')[2].split('&#44')[0][1:]
                    server.say(f'§6[QQ] §a[{self.find_game_name(str(user_id), event.group_id)}] §f{event.content}')
            
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
                self.send_msg_to_all_qq(f'[{info.player}] {info.content}')
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
        group_raw_info = []
        for group_id in self.config['group_id']:
            group_raw_info.append(requests.post(f'http://{self.host}:{self.port}/get_group_member_list', json={
                'group_id': group_id
            }))
        unpack = [i.json()['data'] for i in group_raw_info if i.json()['status'] == 'ok']
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
    def find_game_name(self, qq_id:str, group_id:str=None) -> str:
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
        target_data = self.bot.get_group_member_info(group_id, qq_id).json()['data']
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
            
    def reply(self, event:Event, message:str):
        event_loop.create_task(self.bot.send(event, message))

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
    def set_number_as_name(self, server:PluginServerInterface, bot:CQHttp, event:Event):
        content = requests.get(f'https://api.miri.site/mcPlayer/get.php?ip={self.config["game_ip"]}&port={self.config["game_port"]}').json()
        number = len([i["name"] for i in content['sample'] if i["name"] in self.whitelist.values()])
        name = " "
        if number != 0:
            name = "在线人数: {}".format(number)
            
        for gid in self.config['group_id']:
            data = {
            'group_id': gid,
            'user_id': event.self_id,
            'card': name
            }
            requests.post(
            f'http://{self.host}:{self.port}/set_group_card',
            json=data)
