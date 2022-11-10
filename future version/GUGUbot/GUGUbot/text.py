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

style = {
    '正常' : {
        'ban_word_find':'回复包含违禁词请修改后重发，维护和谐游戏人人有责。\n违禁理由：{}',
        'no_player_ingame': f"现在没人游玩服务器",
        'player_list':'在线玩家共{}人，玩家列表: {}',
        'bot_list':'在线玩家共{}人，假人列表: {}',
        'server_start':'服务器已启动',
        'add_success':'添加成功！',
        'delete_success':'删除成功！',
        'key_word_exist': '已有指定关键词,请删除(/del <关键词>)后重试 awa'
    },
    '傲娇': {
        'ban_word_find':"本大小姐不听，才不告诉你是因为 {}",
        'no_player_ingame':'讷讷，为什么没人玩，为什么？大家都不爱我了吗awa',
        'player_list':'哼，这次就帮你数数，下次没那么容易了。\n现在有{}人，玩家列表: {}',
        'bot_list':'哼，这次就帮你数数，下次没那么容易了。\n现在有{}人，假人列表: {}',
        'server_start': '服务器启动啦！笨、笨蛋，人家可不是特地来告诉你们的!',
        'add_success':'哼..既然你都这么说了,那我就勉为其难帮你添加了！',
        'delete_success':'删除完了，才...才不是特别为你做的呢!',
        'key_word_exist': '已有指定关键词,请删除(/del <关键词>)后重试 awa'
    }
}