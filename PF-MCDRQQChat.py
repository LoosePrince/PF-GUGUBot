# -*- coding: utf-8 -*-
# Author: XueK__ 
# Description: Restructure the MC-QQ bot based on QQChat plugin
#              The original github is: https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/QQChat

# required import
from mcdreforged.api.types import PluginServerInterface
from mcdreforged.api.command import *
import requests, os, sys, json, time
from collections import defaultdict

PLUGIN_METADATA = {
    'id': 'qq_chat',
    'version': '1.0',
    'name': 'QQChat',
    'description': 'Bot for QQ and MC',
    'author': 'XueK__',
    'original author': 'zhang_anzhi',
    'original link': 'https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/QQChat',
    'dependencies': {
        'cool_q_api': '*',
        'online_player_api': '*',
        'config_api': '*',
        'json_data_api': '*'
    }
}
DEFAULT_CONFIG = {
    'group_id': [1234561, 1234562],
    'admin_id': [1234563, 1234564],
    'whitelist_add_with_bound': False,
    'whitelist_remove_with_leave': True,
    'game_ip':'',
    'game_port':'',
    'forward': {
        'mc_to_qq': True,
        'qq_to_mc': True
    },
    'command': {
        'list': True,
        'mc': True,
        'qq': True,
        'ban_word': True,
        'key_word': True,
        'ingame_key_word': True,
        'name':True,
        'whitelist':True,
        'shenhe':True
    },
    'dict_address' : {"start_command_dict": './/config//QQChat//start_commands.json',
            "key_word_dict": './/config//QQChat//key_word.json',
            "ban_word_dict": './/config//QQChat//ban_word.json',
            "key_word_ingame_dict": './/config//QQChat//key_word_ingame.json',
            "uuid_qqid": './/config//QQChat//uuid_qqid.json',
            "whitelist": './/server//whitelist.json',
            "shenheman":'.//config//QQChat//shenheman.json',
            'shenhe_log':'.//config//QQChat//shenhe_log.txt'},
    '配置说明': '''group_id: 需要转发的QQ群号码，可以添加多个
            admin_id: 管理员名单，可以添加多个
            whitelist_add_with_bound: 绑定时顺便添加白名单 true 开启 false 关闭
            forward: 是否转发消息 true 开启 false 关闭
            command: 是否开启指定功能 true 开启 false 关闭'''
}

group_help_msg = '''命令帮助如下:
/list 获取在线玩家列表
/flist 获取在线假人列表
/bound <游戏ID> 绑定你的游戏ID
/mc <消息> 向游戏内发送消息（可以触发游戏内关键词）
关键词相关：
/addg <关键词> <回复> 添加游戏内关键词回复
/addp <关键词> 添加关键词图片
/delg <关键词> 删除游戏内关键词
/klistg 显示现有游戏内关键词列表
/key_word 查看关键词相关帮助
/style 机器人风格帮助'''

admin_help_msg = '''管理员命令帮助如下
/bound 查看绑定相关帮助
/whitelist 查看白名单相关帮助
/start_command 查看启动指令相关帮助
/ban_word 查看违禁词相关帮助
/key_word 查看关键词相关帮助
/ingame_key_word 查看游戏内关键词相关帮助
/uuid 查看uuid 匹配相关帮助
/name 查看机器人名字相关帮助
（被关了）/command <command> 执行任意指令'''

bound_help = '''/bound list 查看绑定列表
/bound check <QQ号> 查询绑定ID
/bound unbound <QQ号> 解除绑定
/bound <QQ号> <游戏ID> 绑定新ID'''

whitelist_help = '''/whitelist add <target> 添加白名单成员
/whitelist list 列出白名单成员
/whitelist off 关闭白名单
/whitelist on 开启白名单
/whitelist reload 重载白名单
/whitelist remove <target> 删除白名单成员
<target> 可以是玩家名/目标选择器/UUID'''

start_command_help = '''启动指令菜单：
/start_command add <名称> <指令> 添加启动指令
/start_command list 查看现有启动指令
/start_command del <名称> 删除指定启动指令
/start_command on 开启开服指令
/start_command off 关闭开服指令
/start_command exe 执行一遍开服指令
/start_command reload 重载开服指令'''

ban_word_help = '''违禁词相关指令：
/ban_word add <违禁词> <违禁理由> 添加违禁词
/ban_word list 显示违禁词表列及理由
/ban_word del <违禁词> 删除指定违禁词
/ban_word on 开启违禁词
/ban_word off 关闭违禁词
/ban_word reload 重载违禁词'''

key_word_help = '''关键词相关指令：
/key_word on 开启关键词
/key_word off 关闭关键词
/key_word reload 重载关键词
/klist 显示关键词列表
/add <关键词> <回复> 添加关键词
/del <关键词> 删除指定关键词'''

ingame_key_word_help = '''游戏内关键词相关指令：
/ingame_key_word on 开启游戏内关键词
/ingame_key_word off 关闭游戏内关键词
/ingame_key_word reload 重载游戏内关键词'''

style_help = '''风格指令如下：
/style        风格帮助
/style list   风格列表
/style <风格> 切换至指定风格'''

uuid_help ='''uuid匹配指令如下：
/uuid 查看uuid相关帮助
/uuid list 查看uuid绑定表
/uuid reload 重新匹配uuid
/uuid update <老ID> <新ID> 改白名单的名字
/uuid name 查看白名单名字'''

name_help = '''机器人名字相关指令如下：
/name 查看名字相关帮助
/name on 机器人名字显示为在线人数
/name off 机器人名字为特殊空白名字
(一直显示会占用少许服务器资源)
'''

shenhe_help = '''审核名单帮助：
/shenhe on 开启自动审核
/shenhe off 关闭自动审核
/shenhe add <QQ号> <别名> 添加审核员的别名(匹配用)
/shenhe del <QQ号> 删除审核员
/shenhe list 审核员列表
'''

def on_load(server: PluginServerInterface, old):
    # 设置系统路径
    set_sys_path()
    from ConfigAPI import Config
    from JsonDataAPI import Json
    global host,port,past_bot,past_info

    global qq_bot
    config = Config(PLUGIN_METADATA['name'], DEFAULT_CONFIG)
    data = Json(PLUGIN_METADATA['name'])
    host = server.get_plugin_instance('cool_q_api').get_config()['api_host']
    port = server.get_plugin_instance('cool_q_api').get_config()['api_port']
    if old is not None and hasattr(old, 'past_bot') and \
       old is not None and hasattr(old, 'past_info'):
        past_info = old.past_info
        past_bot = old.past_bot
    else:
        past_bot = False

    qq_bot = qbot(server,config,data,host,port)

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
    server.register_event_listener('cool_q_api.on_qq_info', qq_bot.send_msg_to_mc)
    server.register_event_listener('cool_q_api.on_qq_command', qq_bot.on_qq_command)
    server.register_event_listener('cool_q_api.on_qq_notice', qq_bot.quit_notice)

########################################################################
# 游戏消息 -> QQ
qq_bot=None
def on_user_info(server,info):
    if type(qq_bot) != type(None):
        qq_bot.send_msg_to_qq(server,info)
# 更新机器人名字 <- 显示在线人数功能
def on_player_joined(server: PluginServerInterface, player: str, info):
    if type(qq_bot) != type(None) and qq_bot.config["command"]["name"] and past_bot:
        qq_bot.set_number_as_name(server, past_bot,past_info)
# 更新机器人名字 <- 显示在线人数功能
def on_player_left(server: PluginServerInterface, player: str):
    if type(qq_bot) != type(None) and qq_bot.config["command"]["name"] and past_bot:
        qq_bot.set_number_as_name(server, past_bot,past_info)

########################################################################

# 开服
def on_server_startup(server):
    # 开服提示
    qq_bot.send_msg_to_all_qq(style[qq_bot.style]['server_start'])
    # 开服指令
    for _,command in qq_bot.start_command_dict.items():
        # 执行指令
        server.execute(command)

# The definition of the QQ Chat robot:
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
        self.style = '傲娇'
        self.suggestion = self.ingame_at_suggestion()
        # 读取文件
        self.loading_dicts()

    # 读取文件
    def loading_dicts(self) -> None:
        self.start_command_dict = table(self.config["dict_address"]["start_command_dict"])      # 开服指令
        self.key_word_dict = table(self.config["dict_address"]['key_word_dict'])                # QQ 关键词
        self.ban_word_dict = table(self.config["dict_address"]['ban_word_dict'])                # 违禁词
        self.key_word_ingame_dict = table(self.config["dict_address"]['key_word_ingame_dict'])  # MC 关键词
        self.uuid_qqid = table(self.config["dict_address"]['uuid_qqid'])                        # uuid - qqid 表
        temp = self.loading_file(self.config["dict_address"]['whitelist'])                      # 白名单表 [{uuid:value, name: value}]
        self.whitelist = {list(i.values())[0]:list(i.values())[1] for i in temp}                # 解压白名单表
        self.shenheman = table(self.config["dict_address"]['shenheman'])                        # 群审核人员

    # 通用QQ 指令
    def on_qq_command(self,server, info, bot):
        print(info)
        # 过滤非关注的消息
        if not (info.source_id in self.config['group_id'] or
            info.source_id in self.config['admin_id']) or info.content[0] != '/':
            return 
        command = info.content.split(' ')
        command[0] = command[0].replace('/', '')
        # 玩家列表
        if self.config['command']['list'] and command[0] == 'list':
            content = requests.get(f'https://api.miri.site/mcPlayer/get.php?ip={self.config["game_ip"]}&port={self.config["game_port"]}').json()
            # 过滤假人
            t_player = [i["name"] for i in content['sample'] if i["name"] in self.whitelist.values()]
            if len(t_player) == 0:
                bot.reply(info,style[self.style]['no_player_ingame'])
            else:
                # 名字排序
                t_player.sort()
                bot.reply(info, style[self.style]['player_list'].format(
                    len(t_player),
                    ', '.join(t_player)))
        # 假人列表
        elif self.config['command']['list'] and command[0] == 'flist':
            content = requests.get(f'https://api.miri.site/mcPlayer/get.php?ip={self.config["game_ip"]}&port={self.config["game_port"]}').json()
            # 过滤真人
            t_player = [i["name"] for i in content['sample'] if i["name"] not in self.whitelist.values()]
            if len(t_player) == 0:
                bot.reply(info,'没有假人在线哦！')
            else:
                # 名字排序
                t_player.sort()
                bot.reply(info, style[self.style]['bot_list'].format(
                    len(t_player),
                    ', '.join(t_player)))
        # 添加关键词
        elif self.config['command']['key_word'] and command[0] == 'add':
            if command[1] not in self.key_word_dict:
                # 先检测违禁词
                whether_ban1,_ = self.check_ban_word(command[1])
                whether_ban2,_ = self.check_ban_word(' '.join(command[2:]))
                if whether_ban1 or whether_ban2:
                    bot.reply(info,'添加失败!')
                # 正常添加
                else:
                    self.key_word_dict[command[1]] = ' '.join(command[2:])
                    bot.reply(info, style[self.style]['add_success'])
            else:
                bot.reply(info, '已有指定关键词,请删除(/del <关键词>)后重试 awa')
        # 删除指定关键词
        elif self.config['command']['key_word'] and command[0] == 'del':
            if command[1] in self.key_word_dict:
                del self.key_word_dict[command[1]]
                bot.reply(info, style[self.style]['delete_success'])
        # 回复关键词列表
        elif self.config['command']['key_word'] and command[0] == 'klist':
            temp = '现在有以下关键词:\n' + '\n'.join( self.key_word_dict.keys())
            bot.reply(info, temp)
        # 游戏内关键词
        elif self.config['command']['ingame_key_word'] and command[0] == 'addg':
            if command[1] not in self.key_word_ingame_dict:
                key_word, response = command[1], ' '.join(command[1])
                # 先检测违禁词
                whether_ban1,_ = self.check_ban_word(key_word)
                whether_ban2,_ = self.check_ban_word(response)
                if whether_ban1 or whether_ban2:
                    bot.reply(info,'添加失败!')
                # 正常添加
                else:
                    self.key_word_ingame_dict[key_word] = response
                    bot.reply(info, style[self.style]['add_success'])
            else:
                bot.reply('添加失败，已有该关键词！')
        # 审核通过
        elif self.config['command']['shenhe'] and command[0] == '同意' and len(self.shenhe[info.user_id]) > 0:
            bot.set_group_add_request(self.shenhe[info.user_id][0][1],self.shenhe[info.user_id][0][2],True)
            with open(self.config["dict_address"]['shenhe_log'],'a+',encoding='utf-8') as f:
                f.write(" ".join([time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    self.shenhe[info.user_id][0][0],
                    info.user_id,
                    '通过'])+'\n')
            bot.reply(info,f"已通过{self.shenhe[info.user_id][0][0]}的申请awa")
            self.shenhe.pop(0)
        # 审核不通过
        elif self.config['command']['shenhe'] and command[0] == '拒绝' and len(self.shenhe[info.user_id]) > 0:
            bot.set_group_add_request(self.shenhe[info.user_id][0][1],self.shenhe[info.user_id][0][2],False)
            with open(self.config["dict_address"]['shenhe_log'],'a+',encoding='utf-8') as f:
                f.write(" ".join([time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    self.shenhe[info.user_id][0][0],
                    info.user_id,
                    '拒绝'])+'\n')
            bot.reply(info,f"已拒绝{self.shenhe[info.user_id][0][0]}的申请awa")
            self.shenhe.pop(0)
        # 删除游戏内关键词
        elif self.config['command']['ingame_key_word'] and command[0] == 'delg' and command[1] in self.key_word_ingame_dict:
            if command[1] in self.key_word_ingame_dict:
                del self.key_word_ingame_dict[command[1]]
                bot.reply(info, style[self.style]['delete_success'])
            else:
                bot.reply(info, '未找到对应关键词')
        # qq查看游戏内关键词列表
        elif self.config['command']['ingame_key_word'] and command[0] == 'klistg':
            temp = '现在有以下关键词:\n' + '\n'.join(self.key_word_ingame_dict.keys())
            bot.reply(info, temp)
        # 添加关键词图片
        elif self.config['command']['key_word'] and command[0] == 'addp' and len(command)>1:
            if command[1] not in self.key_word_dict and info.user_id not in self.picture_record_dict:
                whether_ban1,_ = self.check_ban_word(command[1])
                if whether_ban1:
                    bot.reply(info,'添加失败!')
                # 正常添加
                else:
                    self.picture_record_dict[info.user_id] = command[1]
                    bot.reply(info, '请发送要添加的图片~')
            elif command[1] in self.key_word_dict:
                bot.reply(info, '已存在该关键词~')
            else:
                bot.reply(info,'上一个关键词还未绑定，添加哒咩！') 
        
        if info.source_type == 'private':
            self.private_command(server, info, bot, command)
        elif info.source_type == 'group':
            self.group_command(server, info, bot, command)

    # 管理员指令
    def private_command(self, server, info, bot, command):
        # 全部帮助菜单
        if info.content == '/help':
            bot.reply(info, admin_help_msg)
        # bound 帮助菜单
        elif info.content.startswith('/bound'):
            if info.content == '/bound':
                bot.reply(info, bound_help)
            # 已绑定的名单    
            elif len(command) == 2 and command[1] == 'list':
                bound_list = [f'{a} - {b}' for a, b in self.data.items()]
                reply_msg = ''
                for i in range(0, len(bound_list)):
                    reply_msg += f'{i + 1}. {bound_list[i]}\n'
                reply_msg = '还没有人绑定' if reply_msg == '' else reply_msg
                bot.reply(info, reply_msg)
            # 查寻绑定的ID
            elif len(command) == 3 and command[1] == 'check':
                if command[2] in self.data:
                    bot.reply(info,
                            f'{command[2]} 绑定的ID是{self.data[command[2]]}')
                else:
                    bot.reply(info, f'{command[2]} 未绑定')
            # 解除绑定
            elif len(command) == 3 and command[1] == 'unbound':
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
        elif info.content.startswith('/whitelist'):
            if info.content == '/whitelist':
                bot.reply(info, whitelist_help)
            # 执行指令
            elif command[1] in ['add', 'remove', 'list', 'on', 'off', 'reload']:
                if server.is_rcon_running():
                    bot.reply(info, server.rcon_query(info.content))
                # 添加提示
                else:
                    server.execute(info.content)
                if command[1] == 'add':
                    bot.reply(info, style[self.style]['add_success'])
                    while command[2] not in self.whitelist:
                        temp = self.loading_file(self.config["dict_address"]['whitelist'])
                        # 解压白名单表
                        self.whitelist = {list(i.values())[0]:list(i.values())[1] for i in temp}
                        time.sleep(2)
                    self.match_id()
                elif command[1] == 'remove':
                    bot.reply(info ,style[self.style]['delete_success'])
                    temp = self.loading_file(self.config["dict_address"]['whitelist'])
                    # 解压白名单表
                    self.whitelist = {list(i.values())[0]:list(i.values())[1] for i in temp}
                elif command[1] == 'on':
                    bot.reply(info, '白名单已开启！')
                elif command[1] == 'off':
                    bot.reply(info, '白名单已关闭！')
                elif command[1] == 'reload':
                    temp = self.loading_file(self.config["dict_address"]['whitelist'])
                    # 解压白名单表
                    self.whitelist = {list(i.values())[0]:list(i.values())[1] for i in temp}
                    bot.reply(info, '白名单已重载~')
                else:
                    bot.reply(info,'白名单如下：\n'+'\n'.join(sorted(self.whitelist.values())))
                    
        # 启动指令相关
        elif info.content.startswith('/start_command'):
            # 帮助菜单
            if info.content == '/start_command':
                bot.reply(info, start_command_help)
            # 添加指令
            elif command[1] == 'add':
                if command[2] not in self.start_command_dict:
                    self.start_command_dict[info.content[19:].split(' ',1)[0]] = info.content[19:].split(' ',1)[1]
                    bot.reply(info, style[self.style]['add_success'])
                else:
                    bot.reply(info, f'已存在指令：{command[2]}')
            # 显示指令
            elif command[1] == 'list':
                temp = '现有的指令如下：\n' + '\n'.join(self.start_command_dict.keys())
                bot.reply(info, temp)
            # 删除指令
            elif command[1] == 'del':
                # 存在的指令：删除
                if command[2] in self.start_command_dict:
                    del self.start_command_dict[command[2]]
                    bot.reply(info,style[self.style]['delete_success'])
                # 不存在的指令
                else:
                    bot.reply(info, '指令不存在哦！')
            # 开启开服指令
            elif command[1] == 'on':
                self.config['command']['start_command'] = True
                bot.reply(info, '已开启开服指令！')
            # 关闭开服指令
            elif command[1] == 'off':
                self.config['command']['start_command'] = False
                bot.reply(info, '已关闭开服指令！')
            # 立即执行一遍开服指令
            elif command[1] == 'exe':
                for _,command in self.start_command_dict.items():
                # 执行指令
                    server.execute(command)
                bot.reply(info, '已执行开服指令')
            # 重载开服指令
            elif command[1] == 'reload':
                self.start_command_dict.load()
                bot.reply(info, '已重载开服指令')      
                
        # 违禁词相关
        elif info.content.startswith('/ban_word'):
            # 帮助菜单
            if info.content == '/ban_word':
                bot.reply(info, ban_word_help)
            # 违禁词列表
            elif command[1] == 'list':
                if len(self.ban_word_dict) != 0:
                    temp = '现有违禁词及理由如下：\n' + ''.join([k+'->'+v+'\n' for k,v in self.ban_word_dict.items()])
                    bot.reply(info, temp)
                else:
                    bot.reply(info, '现在还没有违禁词哦~')
            # 添加违禁词
            elif command[1] == 'add':
                bw,reason = info.content.strip().split(' ',3)[2:]
                if bw not in self.ban_word_dict:
                    self.ban_word_dict[bw] = reason
                    bot.reply(info,style[self.style]['add_success'])
                else:
                    bot.reply(info, '添加失败，违禁词已存在')
            # 删除违禁词
            elif command[1] == 'del':
                bw = info.content.strip().split(' ',2)[-1]
                if bw in self.ban_word_dict:
                    del self.ban_word_dict[bw]
                    bot.reply(info, style[self.style]['delete_success'])
                else:
                    bot.reply(info, '未找到相应违禁词')
            # 开启违禁词
            elif command[1] == 'on':
                self.config['command']['ban_word'] = True
                bot.reply(info, '已开启违禁词！')
            # 关闭违禁词
            elif command[1] == 'off':
                self.config['command']['ban_word'] = False
                bot.reply(info, '已关闭违禁词！')
            # 重载违禁词
            elif command[1] == 'reload':
                self.ban_word_dict.load()
                bot.reply(info, '已重载违禁词！')
        
        # 关键词相关
        elif info.content.startswith('/key_word'):
            # 关键词帮助
            if info.content == '/key_word':
                bot.reply(info, key_word_help)
            # 开启关键词
            elif command[1] == 'on':
                self.config['command']['key_word'] = True
                bot.reply(info, '已开启关键词！')
            # 关闭关键词
            elif command[1] == 'off':
                self.config['command']['key_word'] = False
                bot.reply(info, '已关闭关键词！')
            # 重载关键词
            elif command[1] == 'reload':
                self.key_word_dict.load()
                bot.reply(info, '已重载关键词！')
            
        # 游戏内关键词相关
        elif info.content.startswith('/ingame_key_word'):
            # 游戏关键词帮助
            if info.content == '/ingame_key_word':
                bot.reply(info, ingame_key_word_help)
            # 开启游戏关键词
            elif command[1] == 'on':
                self.config['command']['ingame_key_word'] = True
                bot.reply(info, '已开启游戏关键词！')
            # 关闭游戏关键词
            elif command[1] == 'off':
                self.config['command']['ingame_key_word'] = False
                bot.reply(info, '已关闭游戏关键词！')
            # 重载游戏关键词
            elif command[1] == 'reload':
                self.key_word_ingame_dict.load()
                bot.reply(info, '已重载游戏内关键词！')
        # uuid匹配相关
        elif info.content.startswith('/uuid'):
            # uuid 帮助
            if info.content == '/uuid':
                bot.reply(info, uuid_help)
            # 查看uuid 匹配表
            elif command[1] == 'list':
                bot.reply(info, "uuid匹配如下：\n"+'\n'.join([str(k)+'-'+str(v)+'-'+self.data[v] for k,v in self.uuid_qqid.items()]))
            # 更新匹配表
            elif command[1] == 'reload':
                # 白名单表 [{uuid:value, name: value}]
                temp = self.loading_file(self.config["dict_address"]['whitelist'])
                # 解压白名单表
                self.whitelist = {list(i.values())[0]:list(i.values())[1] for i in temp}
                self.match_id()
                bot.reply(info, '已重新匹配~')
            # 更改白名单名字
            elif command[1] == 'update':
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
            # 查看白名单表
            elif command[1] == 'name':
                bot.reply(info, '白名单如下：'+'\n'.join(sorted(self.whitelist.values())))  
        # 机器人名字 <- 服务器人数
        elif info.content.startswith('/name'):
            if info.content == '/name':
                bot.reply(info, name_help)
            elif command[1] == 'on':
                self.config['command']['name'] = True
    
                # 创造全局变量
                global past_info,past_bot
                past_info = info
                past_bot = bot

                self.set_number_as_name(server, bot, info)

                bot.reply(info, "显示游戏内人数已开启")
            elif command[1] == 'off':
                self.config['command']['name'] = False
                for gid in self.config['group_id']:
                    bot.set_group_card(gid, int(bot.get_login_info().json()['data']['user_id']), " ")
                bot.reply(info, "显示游戏内人数已关闭")              
        elif info.content.startswith('/shenhe'):
            if info.content == '/shenhe':
                bot.reply(info, shenhe_help)
            elif command[1] == 'on':
                self.config['command']['shenhe'] = True
                bot.reply(info, '自动审核开启')
            elif command[1] == 'off':
                self.config['command']['shenhe'] = False
                bot.reply(info, '自动审核关闭')
            elif command[1] == 'add':
                if len(command) == 4 and command[3] not in self.shenheman:
                    self.shenheman[command[3]] = command[2] # 别名：QQ号
                    bot.reply(info,style[self.style]['add_success'])
                elif command[3] in self.shenheman:
                    bot.reply(info,'已存在该别名')
            elif command[1] == 'del' and len(command) > 2:
                
                if command[2] in self.shenheman.values():
                    for k,v in self.shenheman.items():
                        if v == command[2]:
                            del self.shenheman[k]
                    bot.reply(info,style[self.style]['delete_success'])
                else:
                    bot.reply(info,'审核员不存在哦！')
            elif command[1] == 'list':
                temp = defaultdict(list)
                for name,qq_hao in self.shenheman.items():
                    temp[qq_hao].append(name)
                bot.reply(info, "有如下审核员：\n"+"\n".join([k+'-'+",".join(v) for k,v in temp.items()]))

    # 群指令
    def group_command(self, server, info, bot, command):
        # 群帮助
        if info.content == '/help':
            bot.reply(info, group_help_msg)
        # qq发送到游戏内消息
        elif self.config['command']['mc'] and command[0] == 'mc':
            user_id = str(info.user_id)
            if user_id in self.data.keys() and not self.check_ban_word(info.content[4:])[0]:
                # 正常转发
                server.say(f'§6[QQ] §a[{self.find_game_name(user_id)}] §f{info.content[4:]}')
                # 回复关键词
                if info.content[4:] in self.key_word_ingame_dict:
                    server.say(f'§a[机器人] §f{self.key_word_ingame_dict[info.content[4:]]}')
                    bot.reply(info,f'{self.key_word_ingame_dict[info.content[4:]]}')
            # 有违禁词
            elif self.config['command']['ban_word'] and self.check_ban_word(info.content[4:])[0]:
                bot.reply(info, style[self.style]['ban_word_find'].format(self.check_ban_word(info.content[4:])[1]))
            else:
                bot.reply(info, f'[CQ:at,qq={user_id}] 请使用/bound <ID>绑定游戏ID')
        # 绑定功能
        elif len(command) == 2 and command[0] == 'bound':
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
                bot.set_group_card(info.source_id,user_id, self.data[user_id])
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
                        time.sleep(2)
                    # 重新匹配
                    self.match_id()
        # 机器人风格相关
        elif info.content.startswith('/style'):
            # 风格帮助
            if info.content == '/style':
                bot.reply(info, style_help)
            # 风格列表
            elif command[1] == 'list':
                bot.reply(info, "现有如下风格：\n"+'\n'.join(style.keys()))
            # 切换风格
            elif command[1] in style.keys():
                self.style = command[1]
                bot.reply(info, f'已切换为 {self.style}')
    # 退群处理
    def quit_notice(self, server, info, bot):
        # 指定群里 + 是退群消息
        if info.source_id in self.config['group_id'] \
            and info.notice_type == 'group_decrease':
            user_id = str(info.user_id)
            if user_id in self.data.keys():
                server.execute(f"whitelist remove {self.data[user_id]}")
                bot.reply(info, f"{self.data[user_id]}已退群，白名单同步删除")
                del self.data[user_id]
                self.data.save()

    # 进群处理
    def apply_notice(self,server, info, bot):
        if info.source_id in self.config["group_id"] \
            and info.request_type == "group" and self.config["command"]["shenhe"]:
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
            self.shenhe[at_id].append((stranger_name,info.flag,info.sub_type))
                        
    # 匹配uuid qqid
    def match_id(self) -> None:
        # QQ绑定名单
        with open(".//config//QQChat//QQChat.json",'r')  as f:
            # {qq_id: qq_name}
            QQ_bound = json.load(f)
        # 解压whitelist
        whitelist_dict = {}
        for uuid, game_name in self.whitelist.items():
            whitelist_dict[game_name] = uuid   
        # 匹配    
        for qq_id, qq_name in QQ_bound.items():
            if '(' in qq_name or '（' in qq_name:
                qq_name = qq_name.split('(')[0].split('（')[0]
            if qq_name in whitelist_dict:
                self.uuid_qqid[whitelist_dict[qq_name]] = qq_id

    # 转发消息
    def send_msg_to_mc(self, server, info, bot):
        self.server = server
        # 判断是否转发
        if info.content[0] != '/' and info.source_id in self.config['group_id']\
            and self.config['forward']['qq_to_mc']:
            # 判断是否绑定
            if  str(info.user_id) in self.data.keys():
                # 如果开启违禁词
                if self.config['command']['ban_word']:
                    ban, reason = self.check_ban_word(info.content)
                    # 包含违禁词 -> 撤回 + 提示 + 不转发
                    if ban:
                        bot.delete_msg(info.message_id)
                        bot.reply(info, style[self.style]['ban_word_find'].format(reason))
                user_id = str(info.user_id)
                # 检测关键词
                if (self.config['command']['ban_word'] == False or ban == False)\
                    and self.config['command']['key_word']:
                    # 检测到关键词 -> 转发原文 + 转发回复
                    if info.content in self.key_word_dict:
                        self.server.say(f'§6[QQ] §a[{self.find_game_name(user_id)}] §f{info.content}')
                        bot.reply(info,self.key_word_dict[info.content])
                        # 过滤图片
                        if self.key_word_dict[info.content][:9] != '[CQ:image':
                            self.server.say(f'§6[QQ] §a[机器人] §f{self.key_word_dict[info.content]}')
                    # 添加图片
                    elif info.user_id in self.picture_record_dict and info.raw_content[:9]=='[CQ:image':
                        self.key_word_dict[self.picture_record_dict[info.user_id]]=info.raw_content
                        del self.picture_record_dict[info.user_id]
                        bot.reply(info,style[self.style]['add_success'])
                    # @ 模块 （现在只支持@ + 内容，非置顶@会出问题）
                    elif '[@' in info.content:
                        temp = info.raw_content.split(']')
                        # 普通 @ 人
                        if len(temp) == 2:
                            target_id,info.content = (temp[0][10:],temp[1])
                            # 未绑定且不是机器人
                            if str(target_id) not in self.data.keys() \
                                and str(target_id) != str(bot.get_login_info().json()['data']['user_id']):
                                target_data = bot.get_group_member_info(info.source_id, target_id).json()['data']
                                target_name = target_data['card'] if target_data['card'] != '' else target_data['nickname']
                                target_name += '(未绑定)'
                            # 正常人
                            elif str(target_id) != str(bot.get_login_info().json()['data']['user_id']):
                                target_name = self.find_game_name(target_id)
                            self.server.say(f'§6[QQ] §a[{self.data[user_id]}] §b[@{target_name}] §f{info.content}')
                        # 回复
                        else:
                            target_id = temp[1][10:]
                            # 是机器人
                            if target_id == str(bot.get_login_info().json()['data']['user_id']):
                                q = {'message_id': temp[0][13:]}
                                pre_message = requests.post(f'http://{self.host}:{self.port}/get_msg',json=q).json()['data']['message']
                                target_name = pre_message.split(']')[0].split('&')[1][4:]
                            # QQ 内回复其他人
                            else:
                                # 未绑定
                                if target_id not in self.data.keys():
                                    target_data = bot.get_group_member_info(info.source_id, target_id).json()['data']
                                    target_name = target_data['card'] if target_data['card'] != '' else target_data['nickname'] 
                                    target_name += '(未绑定)'
                                # 已绑定 -> 找游戏ID
                                else:
                                    target_name = self.find_game_name(target_id)
                            self.server.say(f'§6[QQ] §a[{self.data[user_id]}] §b[@{target_name}] §f{temp[-1]}')
                    # 普通消息
                    else: 
                        # 提取链接中标题
                        if info.content[:8] == '[CQ:json':
                            info.content = '[链接]'+info.content.split('"desc":"')[2].split('&#44')[0][1:]
                        self.server.say(f'§6[QQ] §a[{self.find_game_name(str(user_id))}] §f{info.content}')
            # 提示绑定
            else:
                bot.reply(info, f'[CQ:at,qq={info.user_id}] 请使用/bound <ID>绑定游戏ID')

    # 转发消息
    def send_msg_to_qq(self,server ,info):
        if info.is_player and self.config['forward']['mc_to_qq']:
            # 检测关键词
            if self.config['command']['ban_word']:
                whether_ban_word, response = self.check_ban_word(info.content)
            if self.config['command']['ban_word'] and whether_ban_word:
                temp = '{"text":"' + '消息包含违禁词无法转发到群聊请修改后重发，维护和谐游戏人人有责。\
违禁理由：'+ response + '","color":"gray","italic":true}'
                self.server.execute(f'tellraw {info.player} {temp}')
            else:
                # 检测关键词
                if self.config['command']['ingame_key_word'] and info.content in self.key_word_ingame_dict:
                    # 转发原句
                    self.send_msg_to_all_qq(f'[{info.player}] {info.content}')
                    # 游戏内回复
                    response = self.key_word_ingame_dict[info.content]
                    self.server.say(f'§a[机器人] §f{response}')
                # 游戏内关键词添加
                elif self.config['command']['ingame_key_word'] and info.content[:6] == '!!add ':
                    temp = info.content[6:].split(' ',1)
                    if len(temp) == 2 and temp[0] not in self.key_word_ingame_dict:
                        self.key_word_ingame_dict[temp[0]] = temp[1]
                        self.server.say(style[self.style]['add_success'])
                    else:
                        self.server.say('关键词重复或者指令无效~')
                # 游戏内关键词删除
                elif self.config['command']['ingame_key_word'] and info.content[:6] == '!!del ':
                    if info.content[6:] in self.key_word_ingame_dict:
                        del self.key_word_ingame_dict[info.content[6:]]
                        self.server.say(style[self.style]['delete_success'])
                    else:
                        self.server.say('未找到对应关键词~')
                elif info.content[:2] not in [ '@ ','!!']:
                    # 发送
                    self.send_msg_to_all_qq(f'[{info.player}] {info.content}')

    # 游戏内指令发送qq
    def ingame_command_qq(self,src,ctx):
        if self.config['command']['qq']:
            player = src.player if src.is_player else 'Console'
            if self.config['command']['ban_word']:
                ban,reason = self.check_ban_word(ctx["message"])
            if self.config['command']['ban_word'] and ban:
                temp = '{"text":"' + '消息包含违禁词无法转发到群聊请修改后重发，维护和谐游戏人人有责。\
违禁理由：'+ reason + '","color":"gray","italic":true}'
                self.server.execute(f'tellraw {player} {temp}')
            else:
                # 正常转发
                self.send_msg_to_all_qq(f'[{player}] {ctx["message"]}')
                # 检测关键词
                if ctx['message'] in self.key_word_dict:
                    self.send_msg_to_all_qq(f'{self.key_word_dict[ctx["message"]]}')
                    self.server.say(f'§a[机器人] §f{self.key_word_dict[ctx["message"]]}')

    # 游戏内@
    def ingame_at(self,src,ctx):
        if  self.config['command']['qq']:
            if ctx['QQ(name/id)'].isdigit():
                qq_user_id = ctx['QQ(name/id)']
            else:
                qq_user_id = self.member_dict[ctx['QQ(name/id)']]
            if self.config["command"]["ban_word"]:
                whether_ban, response = self.check_ban_word(ctx['message'])
            player = src.player if src.is_player else 'Console'
            if self.config["command"]["ban_word"] and whether_ban:
                temp = '{"text":"' + '消息包含违禁词无法转发到群聊请修改后重发，维护和谐游戏人人有责。违禁理由：'+ response + '","color":"gray","italic":true}'
                self.server.execute(f'tellraw {player} {temp}')
            else:
                self.send_msg_to_all_qq(f'[{player}] [CQ:at,qq={qq_user_id}] {ctx["message"]}')

    # 游戏内@ 推荐
    def ingame_at_suggestion(self):
        self.member_dict = {}
        suggest_content = []
        # 添加绑定名单
        with open('.//config//QQChat//QQChat.json','r') as f:
            game_name_dict = json.load(f)
        for k,v in game_name_dict.items():
            suggest_content.append(v)
            self.member_dict[v] = k
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
    # 检测违禁词
    def check_ban_word(self, text:str) -> tuple:
        for ban_word in self.ban_word_dict:
            if ban_word in text:
                return True, self.ban_word_dict[ban_word]
        return False, ''

    # 通过QQ号找到绑定的游戏ID
    def find_game_name(self, qq_id:str) -> str:
        qq_uuid = {v:k for k,v in self.uuid_qqid.items()}
        # 未启用白名单
        if self.config['command']['whitelist'] == False:
            return self.data[qq_id]
        # 如果绑定 且 启动白名单
        elif qq_id in qq_uuid:
            uuid = qq_uuid[qq_id]
            if uuid in self.whitelist:
                name = self.whitelist[uuid]
                return name
            else:
                name = requests.post(f'http://{self.host}:{self.port}/get_stranger_info',json={
                    "user_id":qq_id
                }).json()['data']['nickname']
                return str(name)+"(名字不匹配)"
            return str(qq_id)+"(名字不匹配)"
        return '(名字不匹配)'
    
    # 游戏内关键词列表显示
    def ingame_key_list(self):
        temp = '现在有以下关键词:\n' + '\n'.join(self.key_word_ingame_dict.keys())
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
    def send_msg_to_all_qq(self, msg):
        for group in self.config['group_id']:
            requests.post(f'http://{self.host}:{self.port}/send_group_msg', json={
                'group_id': group,
                'message': msg
            })

    # 机器人名称显示游戏内人数
    def set_number_as_name(self,server, bot, info):
        content = requests.get(f'https://api.miri.site/mcPlayer/get.php?ip={self.config["game_ip"]}&port={self.config["game_port"]}').json()
        number = len([i["name"] for i in content['sample'] if i["name"] in self.whitelist.values()])
        name = " "
        if number != 0:
            name = "在线人数: {}".format(number)
            
        for gid in self.config['group_id']:
            data = {
            'group_id': gid,
            'user_id': int(bot.get_login_info().json()['data']['user_id']),
            'card': name
            }
            requests.post(
            f'http://{self.host}:{self.port}/set_group_card',
            json=data)

# 设置系统路径
def set_sys_path():
    file_dir = os.path.dirname(__file__)
    if file_dir not in sys.path:
        sys.path.append(file_dir)
#############################################################################
# 辅助类
import json, os
class table(object):    
    def __init__(self,path="./default.json") -> None: # 初始化，记录系统路径
        self.path = path
        self.load()    
    def load(self) -> None: # 读取
        if os.path.isfile(self.path) and os.path.getsize(self.path) != 0:
            with open(self.path,'r') as f:
                self.data = json.load(f)
        else:
            self.data = {}    
    def save(self) -> None: # 储存
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f)        
    def __getitem__(self,key): # 获取储存内容
        return self.data[key]    
    def __setitem__(self,key,value): # 增加，修改
        self.data[key] = value
        self.save()   
    def __delitem__(self,key): # 删除
        if key in self.data:
            del self.data[key]
            self.save()
    def __repr__(self) -> str: # 打印
        if self.data is None:
            return ""
        return str(self.data)
    def __contains__(self,key): # in 
        return key in self.data
    def keys(self):
        return self.data.keys()
    def values(self):
        return self.data.values()
    def items(self):
        return self.data.items()
    def __iter__(self):
        return self.data.__iter__()
#############################################################################
style = {
    '正常' : {
        'ban_word_find':'回复包含违禁词请修改后重发，维护和谐游戏人人有责。\n违禁理由：{}',
        'no_player_ingame': f"现在没人游玩服务器",
        'player_list':'在线玩家共{}人，玩家列表: {}',
        'bot_list':'在线玩家共{}人，假人列表: {}',
        'server_start':'服务器已启动',
        'add_success':'添加成功！',
        'delete_success':'删除成功！',
    },
    '傲娇': {
        'ban_word_find':"本大小姐不听，才不告诉你是因为 {}",
        'no_player_ingame':'讷讷，为什么没人玩，为什么？大家都不爱我了吗awa',
        'player_list':'哼，这次就帮你数数，下次没那么容易了。\n现在有{}人，玩家列表: {}',
        'bot_list':'哼，这次就帮你数数，下次没那么容易了。\n现在有{}人，假人列表: {}',
        'server_start': '服务器启动啦！笨、笨蛋，人家可不是特地来告诉你们的!',
        'add_success':'哼..既然你都这么说了,那我就勉为其难帮你添加了！',
        'delete_success':'删除完了，才...才不是特别为你做的呢!',
    }
}
