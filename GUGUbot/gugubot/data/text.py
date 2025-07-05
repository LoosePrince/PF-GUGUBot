group_help_msg = """命令帮助如下:
#玩家 -> 获取在线玩家列表
#假人 -> 获取在线假人列表
#服务器 -> 同时获取在线玩家和假人列表
#绑定 <游戏ID> -> 绑定你的游戏ID
#绑定 @xxx <游戏ID> -> 【管理】 给指定用户绑定游戏ID
#mc <消息> -> 向游戏内发送消息（可以触发游戏内关键词）
#风格 -> 机器人风格帮助
#游戏关键词 列表 -> 显示现有游戏内关键词列表
#删除假人 <假人名字> -> 删除游戏内指定假人

关键词相关：
#添加 <关键词> <回复> -> 添加游戏内关键词回复
#添加图片 <关键词/取消> -> 添加/取消添加 关键词图片
#删除 <关键词> -> 删除关键词
#列表 -> 获取关键词回复列表
#帮助 -> 查看关键词相关帮助
"""

admin_help_msg = """管理员命令帮助如下
#绑定   -> 查看绑定相关帮助
#白名单 -> 查看白名单相关帮助
#启动指令 -> 查看启动指令相关帮助
#违禁词 -> 查看违禁词相关帮助
#关键词 -> 查看关键词相关帮助
#游戏内关键词 -> 查看游戏内关键词相关帮助
#uuid   -> 查看uuid 匹配相关帮助
#名字   -> 查看机器人名字相关帮助
#审核   -> 协助审核功能
#执行 <command> -> 执行指令
#MCDR <command> -> 执行MCDR指令(无结果显示)
#重启 -> 重载机器人
"""

bound_help = """#绑定 列表 -> 查看绑定列表
#绑定 查询 <QQ号> -> 查询绑定ID
#绑定 解绑 <QQ号> -> 解除绑定
#绑定 <QQ号> <游戏ID> -> 绑定新ID
#绑定 白名单 开/关 -> 开启/关闭 绑定时添加白名单
#绑定 白名单同步 -> 同步绑定列表到白名单中
#绑定 清空 -> 清空绑定名单 + 白名单（需二次确认）
#绑定 绑定检查 -> 检查是否存在未绑定群员
#绑定 移除未绑定 -> 移除未绑定群员"""

whitelist_help = """#白名单 添加 <target> -> 添加白名单成员
#白名单 列表 -> 列出白名单成员
#白名单 关   -> 关闭白名单
#白名单 开   -> 开启白名单
#白名单 重载 -> 重载白名单
#白名单 更新 <老ID> <新ID> -> 改白名单的名字
#白名单 删除 <target> -> 删除白名单成员
<target> 可以是玩家名/目标选择器/UUID"""

start_command_help = """启动指令菜单：
#启动指令 添加 <名称> <指令> -> 添加启动指令
#启动指令 列表 -> 查看现有启动指令
#启动指令 删除 <名称> -> 删除指定启动指令
#启动指令 开   -> 开启开服指令
#启动指令 关   -> 关闭开服指令
#启动指令 执行 -> 执行一遍开服指令
#启动指令 重载 -> 重载开服指令""" 

ban_word_help = """违禁词相关指令：
#违禁词 添加 <违禁词> <违禁理由> -> 添加违禁词
#违禁词 列表 -> 显示违禁词列表及理由
#违禁词 删除 <违禁词> -> 删除指定违禁词
#违禁词 开   -> 开启违禁词
#违禁词 关   -> 关闭违禁词
#违禁词 重载 -> 重载违禁词"""

key_word_help = """关键词相关指令：
#关键词 开   -> 开启关键词
#关键词 关   -> 关闭关键词
#关键词 重载 -> 重载关键词
#关键词 列表 -> 显示关键词列表
#添加 <关键词> <回复> -> 添加关键词
#删除 <关键词> -> 删除指定关键词"""

ingame_key_word_help = """游戏内关键词相关指令：
#游戏内关键词 开   -> 开启游戏内关键词
#游戏内关键词 关   -> 关闭游戏内关键词
#游戏内关键词 重载 -> 重载游戏内关键词
#游戏内关键词 列表 -> 显示游戏内关键词列表
#游戏内关键词 添加 <关键词> <回复> -> 添加游戏内关键词
#游戏内关键词 删除 <关键词> -> 删除指定游戏内关键词"""

style_help = """风格指令如下：
#风格        -> 风格帮助
#风格 列表   -> 风格列表
#风格 <风格> -> 切换至指定风格"""

uuid_help ="""uuid匹配指令如下：
#uuid        -> 查看uuid相关帮助
#uuid 列表   -> 查看uuid绑定表
#uuid 重载 -> 重新匹配uuid
"""

name_help = """机器人名字相关指令如下：
#名字 -> 查看名字相关帮助
#名字 开 -> 机器人名字显示为在线人数
#名字 关 -> 机器人名字为特殊空白名字
(会占用少许服务器资源)
"""

shenhe_help = """审核名单帮助：
#审核 开 -> 开启自动审核
#审核 关 -> 关闭自动审核
#审核 添加 <QQ号> <别名> -> 添加审核员的别名(匹配用)
#审核 删除 <QQ号> -> 删除审核员
#审核 列表 -> 审核员列表
"""

mc2qq_template = [
    "({}) {}",
    "[{}] {}",
    "{} 说：{}",
    "{} : {}",
    "冒着爱心眼的{}说：{}"
]

style = {
    "正常" : {
        "add_cancel": "图片保存已取消",
        "add_existed": "已存在该关键词~",
        "add_image_instruction": "请发送要添加的图片~",
        "add_image_fail": "图片保存失败~",
        "add_image_previous_no_done": "上一个关键词还未绑定，添加哒咩！",
        "add_success":"添加成功！",
        "authorization_pass": "已通过{}的申请awa",
        "authorization_reject": "已拒绝{}的申请awa",
        "authorization_request": "{} 申请进群, 请审核",
        "ban_word_find":"回复包含违禁词请修改后重发，维护和谐游戏人人有责。\n违禁理由：{}",
        "bound_add_whitelist": "已将您添加到服务器白名单",
        "bound_exist": "您已绑定ID: {}, 绑定已达上限, 请联系管理员修改",
        "bound_success": "已成功绑定",
        "command_success" : "指令执行成功",
        "delete_success":"删除成功！",
        "del_no_exist": "该关键词不存在",
        "del_whitelist_when_quit": "{}已退群，白名单同步删除",
        "key_word_exist": "已有指定关键词,请删除(#删除 <关键词>)后重试 awa",
        "lack_parameter": "缺少参数，请参考 #帮助 里的说明",
        "list": "列表如下: \n{}",
        "no_player_ingame": "现在没人游玩服务器",
        "no_word": "列表空空的",
        "player_api_fail": "未能捕获服务器日志（推荐开启rcon精准获取玩家信息）",
        "player_list":"在线玩家共{}人，{}列表: {}",
        "player_notice_join": "{} 加入了游戏",
        "player_notice_leave": "{} 离开了游戏",
        "reload_success": "重载成功",
        "server_start":"服务器已启动",
        "server_stop": "服务器已关闭"
    },
    "傲娇": {
        "ban_word_find":"本大小姐不听，才不告诉你是因为 {}",
        "no_player_ingame":"讷讷，为什么没人玩，为什么？大家都不爱我了吗awa",
        "player_list":"哼，这次就帮你数数，下次没那么容易了。\n现在有{}人，{}列表: {}",
        "server_start": "服务器启动啦！笨、笨蛋，人家可不是特地来告诉你们的!",
        "add_success":"哼..既然你都这么说了,那我就勉为其难帮你添加了！",
        "delete_success":"删除完了，才...才不是特别为你做的呢!",
        "key_word_exist": "已有指定关键词,请删除(#删除 <关键词>)后重试 awa",
        "lack_parameter": "笨死了，这都不会1w1，去看 #帮助 啦！",
        "del_no_exist": "累死我了，找了半天没这个词，大坏蛋！",
        "no_word": "快添点东西进来叭，才。。才不是人家寂寞了",
        "list": "列表如下: \n{}",
        "reload_success": "重载啦awa，快夸我！",
        "command_success" : "那么多指令，想累死本小姐嘛，才不做！什么，你说你准备了礼物，那我就勉为其难做点，哼"
    },
    "雌小鬼": {
        "ban_word_find": "呜呜呜，偶才不告诉你是因为 {} 呢！",
        "no_player_ingame": "呜呜，为什么没有人陪我玩呢？难道大家都讨厌我了吗？唔唔唔",
        "player_list": "大叔连这都不会，真是杂鱼！杂鱼杂鱼！\n现在有 {} 个人，{} 列表：{}",
        "server_start": "服务器终于启动了！杂鱼，不会连进都进不去吧！真是有够杂鱼的。",
        "add_success": "哼，既然你这么说了，我勉为其难地帮你添加了！",
        "delete_success": "删除成功啦，才不是为了你特别做的呢！",
        "key_word_exist": "已经有这个关键词了，请删除（#删除 <关键词>）后再试试呀。",
        "lack_parameter": "真是笨蛋，这都不会吗？去看看 #帮助 吧！",
        "del_no_exist": "累死我了，找了半天都没有这个词，大坏蛋！",
        "no_word": "快点加点东西进来嘛，我好无聊啊！才不是因为寂寞呢~",
        "list": "列表如下：\n{}",
        "reload_success": "又重载了，哼！快夸夸我吧！",
        "command_success": "那么多指令，你是想累死我吗？才不会做呢！什么？你准备了礼物？好吧，我勉为其难地做点东西，哼~"
    },
    "御姐": {
        "ban_word_find": "哼，不告诉你是因为 {} 这种事情，你也不配知道。",
        "no_player_ingame": "哼，竟然没有人来陪我玩，看来我的魅力还不够。",
        "player_list": "嘻嘻，我就帮你数数吧，现在总共有 {} 位玩家，{} 列表如下：{}",
        "server_start": "服务器终于启动了！不过，我并不是特地为了通知你们才说的。",
        "add_success": "嗯，既然你这么请求，姐姐就勉为其难地帮你添加了！",
        "delete_success": "删除完毕，姐姐可不是特意为你做的。",
        "key_word_exist": "这个关键词已经存在了，请删除（#删除 <关键词>）后重试。",
        "lack_parameter": "真是个无能之辈，连最基本的都不会，快去看看 #帮助 吧！",
        "del_no_exist": "找了半天都没有找到这个词，真是让人头疼！",
        "no_word": "快点给我一些东西吧，不然姐姐会感到无聊的。",
        "list": "以下是列表内容：\n{}",
        "reload_success": "已经重新加载了，你要不夸奖一下姐姐吗？",
        "command_success": "这么多指令，你是想让姐姐累死吗？姐姐可不会这么做！什么？你准备了礼物？好吧，姐姐就勉为其难地做点东西。"
    },
    "萝莉": {
        "ban_word_find": "呀~诶嘿嘿，不告诉你是因为 {} 啦！",
        "no_player_ingame": "呜呜呜，没有人来陪我玩耍了，难过死了！",
        "player_list": "嘻嘻，我来帮你数数哦，现在一共有 {} 个人，{} 列表是：{}",
        "server_start": "服务器启动啦！嘻嘻，我可不是特意来告诉你们的哦！",
        "add_success": "嘻嘻，既然你这么说了，那我就勉为其难地帮你添加啦！",
        "delete_success": "删除成功啦，可不是特别为你做的呢！",
        "key_word_exist": "这个关键词已经存在了呢，请删除（#删除 <关键词>）后重试哦！",
        "lack_parameter": "嗯？怎么连这个都不会呀，快去看看 #帮助 吧！",
        "del_no_exist": "唔...找了半天都没有这个词，大坏蛋！",
        "no_word": "呜呜，快给我点东西吧，不然我会好寂寞的！",
        "list": "下面是列表内容哦：\n{}",
        "reload_success": "呀呀，已经重新加载啦！夸夸我嘛~",
        "command_success": "好多指令呀，你是要累坏我吗？才不会做呢！嘻嘻~什么？你有礼物？好吧，我勉为其难地帮你做点东西啦~"
    },
    "波奇酱": {
        "ban_word_find": "咳咳，不告诉你 {} 是因为...没什么特别的理由。",
        "no_player_ingame": "唔...好害怕，为什么没有人来玩呢？大家都不喜欢我吗？",
        "player_list": "呃...好紧张，现在一共有 {} 个人，{} 列表如下：{}",
        "server_start": "服务器启动了...只是...不是为了特地告诉你们而已。",
        "add_success": "唔...既然你这么请求，我就勉为其难地帮你添加了。",
        "delete_success": "已经删除了...唔，不是特意为了你才这么做的。",
        "key_word_exist": "这个关键词已经存在了，请删除（#删除 <关键词>）后重试。",
        "lack_parameter": "唔唔唔...你竟然连最基本的都不会，去看看 #帮助 吧。",
        "del_no_exist": "好困扰...找了半天都找不到这个词，真是让人头疼。",
        "no_word": "唔唔...快点给我一些东西，否则我会感到更加害怕。",
        "list": "列表如下：\n{}",
        "reload_success": "重新加载完成...唔唔，有没有什么表扬的话？",
        "command_success": "这么多指令...你是想让我陷入恐惧中吗？唔，我不会做的！什么？你准备了礼物？唔唔...好吧，我勉为其难地做点东西。"
    },
    "病娇": {
        "ban_word_find": "嘻嘻嘻，怎么样？你猜不到 {} 是因为我喜欢看你迷茫的样子！",
        "no_player_ingame": "唔唔唔...都没有人来陪我玩耍了！你们都抛弃我了吗？！我会让你们后悔的！",
        "player_list": "哼，我勉为其难地帮你数数！现在一共有 {} 个人，{} 列表如下：{}",
        "server_start": "服务器启动了！嘻嘻嘻，你以为我是特地来告诉你的吗？不，我只是觉得这样做会让你更加困惑！",
        "add_success": "唔唔唔...既然你这么请求，我勉为其难地帮你添加了！但是别误会，这并不代表我对你有好感！",
        "delete_success": "删除成功了！嘻嘻嘻，我并没有特意为了你才这么做，我只是觉得这样做会让你更加绝望而已！",
        "key_word_exist": "这个关键词已经存在了！请删除（#删除 <关键词>）后重试。嘻嘻嘻，你真是个可笑的小丑！",
        "lack_parameter": "唔唔唔，你连这个都不会？真是个令人讨厌的笨蛋！快去看看 #帮助 吧！",
        "del_no_exist": "唔唔唔，找了半天都找不到这个词！你真是个让人发疯的家伙！我会让你付出代价的！",
        "no_word": "嘻嘻嘻，给我一些东西吧！否则我会让你体验到痛苦的滋味！你不会想看到我发狂的样子吧？",
        "list": "下面是列表内容哦：\n{}",
        "reload_success": "重新加载完成了！嘻嘻嘻，不必夸奖我，我只是觉得这样做会让你更加绝望而已！",
        "command_success": "这么多指令，你是想让我彻底发疯吗？唔唔唔，算了，我勉为其难地帮你做点东西！但是你必须付出代价！"
    },
    "中二病": {
        "ban_word_find": "你可看不出来，这个 {} 是我掌握的秘术，你无法窥探其中的奥秘！",
        "no_player_ingame": "唔，竟然没有人能够与我一同战斗，看来这个世界已经失去了勇者的存在！",
        "player_list": "哼，这么请求的话，我就勉为其难地为你点数一番！现在共有 {} 位勇者，{} 列表如下：{}",
        "server_start": "黑暗之力觉醒了！世界将被我带入深渊，这并非偶然，而是命运的安排！",
        "add_success": "你终于请求到了我的帮助，勇敢的冒险者！我将在有限的时间内为你添加！但请记住，这不代表我对你产生了任何好感！",
        "delete_success": "黑暗力量洗净了这个世界上的某个存在，你应该庆幸自己没有成为那个被消灭的人！",
        "key_word_exist": "这个关键词已经在我的掌控之下！在黑暗的领域中，你休想摆脱我的控制！",
        "lack_parameter": "无知的愚者，你不懂这个世界的秘密，去阅读 #帮助，也许你能窥探一些真相！",
        "del_no_exist": "在黑暗的境界中，你找不到任何痕迹，这个词根本不存在于我的领域中！",
        "no_word": "唔唔唔，这个世界需要更多的暗黑力量，只有这样才能引发真正的战斗！快给我更多的事物，让黑暗的力量永不停歇！",
        "list": "现在，我将揭开真相的面纱！以下是列表的真实内容：\n{}",
        "reload_success": "重新注入黑暗力量完成！勇敢的探险者，不必称赞我，你不懂这其中的牺牲与代价！",
        "command_success": "在无尽的命运中，你希望我屈从于你的命令吗？哈哈哈，不过，我愿意勉为其难地帮你完成一些事情！"
    }

}

qq_face_name = {
    "4" : "得意",
    "5" : "流泪",
    "8" : "睡",
    "9" : "大哭",
    "10" : "尴尬",
    "12" : "调皮",
    "14" : "微笑",
    "16" : "酷",
    "21" : "可爱",
    "23" : "傲慢",
    "24" : "饥饿",
    "25" : "困",
    "26" : "惊恐",
    "27" : "流汗",
    "28" : "憨笑",
    "29" : "悠闲",
    "30" : "奋斗",
    "32" : "疑问",
    "33" : "嘘",
    "34" : "晕",
    "38" : "敲打",
    "39" : "再见",
    "41" : "发抖",
    "42" : "爱情",
    "43" : "跳跳",
    "49" : "拥抱",
    "53" : "蛋糕",
    "60" : "咖啡",
    "63" : "玫瑰",
    "66" : "爱心",
    "74" : "太阳",
    "75" : "月亮",
    "76" : "赞",
    "78" : "握手",
    "79" : "胜利",
    "85" : "飞吻",
    "89" : "西瓜",
    "96" : "冷汗",
    "97" : "擦汗",
    "98" : "抠鼻",
    "99" : "鼓掌",
    "100" : "糗大了",
    "101" : "坏笑",
    "102" : "左哼哼",
    "103" : "右哼哼",
    "104" : "哈欠",
    "106" : "委屈",
    "109" : "左亲亲",
    "111" : "可怜",
    "116" : "示爱",
    "118" : "抱拳",
    "120" : "拳头",
    "122" : "爱你",
    "123" : "NO",
    "124" : "OK",
    "125" : "转圈",
    "129" : "挥手",
    "144" : "喝彩",
    "147" : "棒棒糖",
    "171" : "茶",
    "173" : "泪奔",
    "174" : "无奈",
    "175" : "卖萌",
    "176" : "小纠结",
    "179" : "doge",
    "180" : "惊喜",
    "181" : "骚扰",
    "182" : "笑哭",
    "183" : "我最美",
    "201" : "点赞",
    "203" : "托脸",
    "212" : "托腮",
    "214" : "啵啵",
    "219" : "蹭一蹭",
    "222" : "抱抱",
    "227" : "拍手",
    "232" : "佛系",
    "240" : "喷脸",
    "243" : "甩头",
    "246" : "加油抱抱",
    "262" : "脑阔疼",
    "264" : "捂脸",
    "265" : "辣眼睛",
    "266" : "哦哟",
    "267" : "头秃",
    "268" : "问号脸",
    "269" : "暗中观察",
    "270" : "emm",
    "271" : "吃瓜",
    "272" : "呵呵哒",
    "273" : "我酸了",
    "277" : "汪汪",
    "278" : "汗",
    "281" : "无眼笑",
    "282" : "敬礼",
    "284" : "面无表情",
    "285" : "摸鱼",
    "287" : "哦",
    "289" : "睁眼",
    "290" : "敲开心",
    "293" : "摸锦鲤",
    "294" : "期待",
    "297" : "拜谢",
    "298" : "元宝",
    "299" : "牛啊",
    "305" : "右亲亲",
    "306" : "牛气冲天",
    "307" : "喵喵",
    "314" : "仔细分析",
    "315" : "加油",
    "317" : "菜汪",
    "318" : "崇拜",
    "319" : "比心",
    "320" : "庆祝",
    "322" : "拒绝",
    "324" : "吃糖",
    "326" : "生气",
    "9728" : "☀ 晴天",
    "9749" : "☕ 咖啡",
    "9786" : "☺ 可爱",
    "10024" : "✨ 闪光",
    "10060" : "❌ 错误",
    "10068" : "❔ 问号",
    "127801" : "🌹 玫瑰",
    "127817" : "🍉 西瓜",
    "127822" : "🍎 苹果",
    "127827" : "🍓 草莓",
    "127836" : "🍜 拉面",
    "127838" : "🍞 面包",
    "127847" : "🍧 刨冰",
    "127866" : "🍺 啤酒",
    "127867" : "🍻 干杯",
    "127881" : "🎉 庆祝",
    "128027" : "🐛 虫",
    "128046" : "🐮 牛",
    "128051" : "🐳 鲸鱼",
    "128053" : "🐵 猴",
    "128074" : "👊 拳头",
    "128076" : "👌 好的",
    "128077" : "👍 厉害",
    "128079" : "👏 鼓掌",
    "128089" : "👙 内衣",
    "128102" : "👦 男孩",
    "128104" : "👨 爸爸",
    "128147" : "💓 爱心",
    "128157" : "💝 礼物",
    "128164" : "💤 睡觉",
    "128166" : "💦 水",
    "128168" : "💨 吹气",
    "128170" : "💪 肌肉",
    "128235" : "📫 邮箱",
    "128293" : "🔥 火",
    "128513" : "😁 呲牙",
    "128514" : "😂 激动",
    "128516" : "😄 高兴",
    "128522" : "😊 嘿嘿",
    "128524" : "😌 羞涩",
    "128527" : "😏 哼哼",
    "128530" : "😒 不屑",
    "128531" : "😓 汗",
    "128532" : "😔 失落",
    "128536" : "😘 飞吻",
    "128538" : "😚 亲亲",
    "128540" : "😜 淘气",
    "128541" : "😝 吐舌",
    "128557" : "😭 大哭",
    "128560" : "😰 紧张",
    "128563" : "😳 瞪眼"
}

achievement_tr = {
    "Stone Age": "石器时代",
    "Getting an Upgrade": "获得升级",
    "Acquire Hardware": "来硬的",
    "Isn't It Iron Pick": "这不是铁镐么",
    "Hot Stuff": "热腾腾的",
    "Suit Up": "整装上阵",
    "Diamonds!": "钻石！",
    "Ice Bucket Challenge": "冰桶挑战",
    "Not Today, Thank You": "不吃这套，谢谢",
    "Enchanter": "附魔师",
    "Cover Me with Diamonds": "钻石护体",
    "We Need to Go Deeper": "勇往直下",
    "Zombie Doctor": "僵尸科医生",
    "Eye Spy": "隔墙有眼",
    "The End?": "结束了？",
    "Nether": "下界",
    "Oh Shiny": "金光闪闪",
    "Subspace Bubble": "曲速泡",
    "Those Were the Days": "光辉岁月",
    "A Terrible Fortress": "阴森的要塞",
    "Hidden in the Depths": "深藏不露",
    "Who is Cutting Onions?": "谁在切洋葱？",
    "Return to Sender": "见鬼去吧",
    "This Boat Has Legs": "画船添足",
    "War Pigs": "战猪",
    "Spooky Scary Skeleton": "惊悚恐怖骷髅头",
    "Into Fire": "与火共舞",
    "Cover Me in Debris": "残骸裹身",
    "Country Lode, Take Me Home": "天涯共此石",
    'Not Quite "Nine" Lives': "锚没有九条命",
    "Uneasy Alliance": "脆弱的同盟",
    "Hot Tourist Destinations": "热门景点",
    "Feels Like Home": "温暖如家",
    "Withering Heights": "凋零山庄",
    "Local Brewery": "本地酿造厂",
    "Bring Home the Beacon": "带信标回家",
    "A Furious Cocktail": "狂乱的鸡尾酒",
    "Beaconator": "信标工程师",
    "How Did We Get Here?": "为什么会变成这样呢？",
    "The End": "末地",
    "Free the End": "解放末地",
    "You Need a Mint": "你需要来点薄荷糖",
    "The Next Generation": "下一世代",
    "Remote Getaway": "远程折跃",
    "The End... Again...": "结束了再一次",
    "The City at the End of the Game": "在游戏尽头的城市",
    "Sky's the Limit": "天空即为极限",
    "Great View From Up Here": "这上面的风景不错",
    "Adventure": "冒险",
    "Sneak 100": "潜行100级",
    "Crafters Crafting Crafters": "合成器合成合成器",
    "Caves & Cliffs": "上天入地",
    "Sticky Situation": "胶着状态",
    "Monster Hunter": "怪物猎人",
    "Surge Protector": "电涌保护器",
    "Minecraft: Trial(s) Edition": "Minecraft：试炼版",
    "Ol' Betsy": "扣下悬刀",
    "The Power of Books": "知识就是力量",
    "Isn't It Scute?": "这不是鳞甲么？",
    "Respecting the Remnants": "探古寻源",
    "Sweet Dreams": "甜蜜的梦",
    "Is It a Bird?": "那是鸟吗？",
    "What a Deal!": "成交！",
    "Crafting a New Look": "旧貌锻新颜",
    "Voluntary Exile": "自我放逐",
    "Monsters Hunted": "资深怪物猎人",
    "It Spreads": "它蔓延了",
    "Take Aim": "瞄准目标",
    "A Throwaway Joke": "抖包袱",
    "Postmortal": "超越生死",
    "Blowback": "逆风翻盘",
    "Lighten Up": "铜光焕发",
    "Over-Overkill": "天赐良击",
    "Under Lock and Key": "珍藏密敛",
    "Who Needs Rockets?": "还要啥火箭啊？",
    "Arbalistic": "劲弩手",
    "Two Birds, One Arrow": "一箭双雕",
    "Who's the Pillager Now?": "现在谁才是掠夺者？",
    "Careful Restoration": "精修细补",
    "Adventuring Time": "探索的时光",
    "Sound of Music": "音乐之声",
    "Light as a Rabbit": "轻功雪上飘",
    "Is It a Balloon?": "那是气球吗？",
    "Hired Help": "招募援兵",
    "Star Trader": "星际商人",
    "Smithing with Style": "匠心独具",
    "Hero of the Village": "村庄英雄",
    "Bullseye": "正中靶心",
    "Sniper Duel": "狙击手的对决",
    "Very Very Frightening": "魔女审判",
    "Is It a Plane?": "那是飞机吗？",
    "Revaulting": "宝经磨炼",
    "Husbandry": "农牧业",
    "You've Got a Friend in Me": "找到一个好朋友",
    "The Parrots and the Bats": "我从哪儿来？",
    "Fishy Business": "腥味十足的生意",
    "Glow and Behold!": "眼前一亮！",
    "Smells Interesting": "怪味蛋",
    "A Seedy Place": "开荒垦地",
    "Whatever Floats Your Goat!": "羊帆起航！",
    "Bee Our Guest": "与蜂共舞",
    "Total Beelocation": "举巢搬迁",
    "Bukkit Bukkit": "蚪到桶里来",
    "Best Friends Forever": "永恒的伙伴",
    "Birthday Song": "生日快乐歌",
    "Two by Two": "成双成对",
    "Tactical Fishing": "战术性钓鱼",
    "Little Sniffs": "小小嗅探兽",
    "A Balanced Diet": "均衡饮食",
    "Serious Dedication": "终极奉献",
    "Wax On": "涂蜡",
    "When the Squad Hops into Town": "呱呱队出动",
    "Good as New": "完好如初",
    "Shear Brilliance": "华丽一剪",
    "A Complete Catalogue": "百猫全书",
    "The Whole Pack": "群狼聚首",
    "The Cutest Predator": "最萌捕食者",
    "Planting the Past": "播种往事",
    "Wax Off": "脱蜡",
    "With Our Powers Combined!": "相映生辉！",
    "The Healing Power of Friendship!": "友谊的治愈力！"
 }

achievement_template = {
    "chat.type.advancement.challenge": "%s完成了挑战%s",
    "chat.type.advancement.goal": "%s达成了目标%s",
    "chat.type.advancement.task": "%s取得了进度%s",
}

death_template = {
    "death.attack.anvil": "%1$s被坠落的铁砧压扁了",
    "death.attack.anvil.player": "%1$s在与%2$s战斗时被坠落的铁砧压扁了",
    "death.attack.arrow": "%1$s被%2$s射杀",
    "death.attack.arrow.item": "%1$s被%2$s用%3$s射杀",
    "death.attack.badRespawnPoint.link": "刻意的游戏设计",
    "death.attack.badRespawnPoint.message": "%1$s被%2$s杀死了",
    "death.attack.cactus": "%1$s被戳死了",
    "death.attack.cactus.player": "%1$s在试图逃离%2$s时撞上了仙人掌",
    "death.attack.cramming": "%1$s因被过度挤压而死",
    "death.attack.cramming.player": "%1$s被%2$s挤扁了",
    "death.attack.dragonBreath": "%1$s被龙息烤熟了",
    "death.attack.dragonBreath.player": "%1$s被%2$s的龙息烤熟了",
    "death.attack.drown": "%1$s淹死了",
    "death.attack.drown.player": "%1$s在试图逃离%2$s时淹死了",
    "death.attack.dryout": "%1$s因脱水而死",
    "death.attack.dryout.player": "%1$s在试图逃离%2$s时因脱水而死",
    "death.attack.even_more_magic": "%1$s被不为人知的魔法杀死了",
    "death.attack.explosion": "%1$s爆炸了",
    "death.attack.explosion.player": "%1$s被%2$s炸死了",
    "death.attack.explosion.player.item": "%1$s被%2$s用%3$s炸死了",
    "death.attack.fall": "%1$s落地过猛",
    "death.attack.fall.player": "%1$s在试图逃离%2$s时落地过猛",
    "death.attack.fallingBlock": "%1$s被下落的方块压扁了",
    "death.attack.fallingBlock.player": "%1$s在与%2$s战斗时被下落的方块压扁了",
    "death.attack.fallingStalactite": "%1$s被坠落的钟乳石刺穿了",
    "death.attack.fallingStalactite.player": "%1$s在与%2$s战斗时被坠落的钟乳石刺穿了",
    "death.attack.fireball": "%1$s被%2$s用火球烧死了",
    "death.attack.fireball.item": "%1$s被%2$s用%3$s发射的火球烧死了",
    "death.attack.fireworks": "%1$s随着一声巨响消失了",
    "death.attack.fireworks.item": "%1$s随着%2$s用%3$s发射的烟花发出的巨响消失了",
    "death.attack.fireworks.player": "%1$s在与%2$s战斗时随着一声巨响消失了",
    "death.attack.flyIntoWall": "%1$s感受到了动能",
    "death.attack.flyIntoWall.player": "%1$s在试图逃离%2$s时感受到了动能",
    "death.attack.freeze": "%1$s被冻死了",
    "death.attack.freeze.player": "%1$s被%2$s冻死了",
    "death.attack.generic": "%1$s死了",
    "death.attack.generic.player": "%1$s死于%2$s",
    "death.attack.genericKill": "%1$s被杀死了",
    "death.attack.genericKill.player": "%1$s在与%2$s战斗时被杀死了",
    "death.attack.hotFloor": "%1$s发现了地板是熔岩做的",
    "death.attack.hotFloor.player": "%1$s因%2$s而步入危险之地",
    "death.attack.inFire": "%1$s浴火焚身",
    "death.attack.inFire.player": "%1$s在与%2$s战斗时不慎走入了火中",
    "death.attack.inWall": "%1$s在墙里窒息而亡",
    "death.attack.inWall.player": "%1$s在与%2$s战斗时在墙里窒息而亡",
    "death.attack.indirectMagic": "%1$s被%2$s使用的魔法杀死了",
    "death.attack.indirectMagic.item": "%1$s被%2$s用%3$s杀死了",
    "death.attack.lava": "%1$s试图在熔岩里游泳",
    "death.attack.lava.player": "%1$s在逃离%2$s时试图在熔岩里游泳",
    "death.attack.lightningBolt": "%1$s被闪电击中",
    "death.attack.lightningBolt.player": "%1$s在与%2$s战斗时被闪电击中",
    "death.attack.mace_smash": "%1$s被%2$s一锤毙命",
    "death.attack.mace_smash.item": "%1$s被%2$s用%3$s一锤毙命",
    "death.attack.magic": "%1$s被魔法杀死了",
    "death.attack.magic.player": "%1$s在试图逃离%2$s时被魔法杀死了",
    "death.attack.message_too_long": "抱歉！消息太长，无法完整显示。截断后的消息：%s",
    "death.attack.mob": "%1$s被%2$s杀死了",
    "death.attack.mob.item": "%1$s被%2$s用%3$s杀死了",
    "death.attack.onFire": "%1$s被烧死了",
    "death.attack.onFire.item": "%1$s在与持有%3$s的%2$s战斗时被烤得酥脆",
    "death.attack.onFire.player": "%1$s在与%2$s战斗时被烤得酥脆",
    "death.attack.outOfWorld": "%1$s掉出了这个世界",
    "death.attack.outOfWorld.player": "%1$s与%2$s不共戴天",
    "death.attack.outsideBorder": "%1$s脱离了这个世界",
    "death.attack.outsideBorder.player": "%1$s在与%2$s战斗时脱离了这个世界",
    "death.attack.player": "%1$s被%2$s杀死了",
    "death.attack.player.item": "%1$s被%2$s用%3$s杀死了",
    "death.attack.sonic_boom": "%1$s被一道音波尖啸抹除了",
    "death.attack.sonic_boom.item": "%1$s在试图逃离持有%3$s的%2$s时被一道音波尖啸抹除了",
    "death.attack.sonic_boom.player": "%1$s在试图逃离%2$s时被一道音波尖啸抹除了",
    "death.attack.stalagmite": "%1$s被石笋刺穿了",
    "death.attack.stalagmite.player": "%1$s在与%2$s战斗时被石笋刺穿了",
    "death.attack.starve": "%1$s饿死了",
    "death.attack.starve.player": "%1$s在与%2$s战斗时饿死了",
    "death.attack.sting": "%1$s被蛰死了",
    "death.attack.sting.item": "%1$s被%2$s用%3$s蛰死了",
    "death.attack.sting.player": "%1$s被%2$s蛰死了",
    "death.attack.sweetBerryBush": "%1$s被甜浆果丛刺死了",
    "death.attack.sweetBerryBush.player": "%1$s在试图逃离%2$s时被甜浆果丛刺死了",
    "death.attack.thorns": "%1$s在试图伤害%2$s时被杀",
    "death.attack.thorns.item": "%1$s在试图伤害%2$s时被%3$s杀死",
    "death.attack.thrown": "%1$s被%2$s给砸死了",
    "death.attack.thrown.item": "%1$s被%2$s用%3$s给砸死了",
    "death.attack.trident": "%1$s被%2$s刺穿了",
    "death.attack.trident.item": "%1$s被%2$s用%3$s刺穿了",
    "death.attack.wither": "%1$s凋零了",
    "death.attack.wither.player": "%1$s在与%2$s战斗时凋零了",
    "death.attack.witherSkull": "%1$s被%2$s发射的头颅射杀",
    "death.attack.witherSkull.item": "%1$s被%2$s用%3$s发射的头颅射杀",
    "death.fell.accident.generic": "%1$s从高处摔了下来",
    "death.fell.accident.ladder": "%1$s从梯子上摔了下来",
    "death.fell.accident.other_climbable": "%1$s在攀爬时摔了下来",
    "death.fell.accident.scaffolding": "%1$s从脚手架上摔了下来",
    "death.fell.accident.twisting_vines": "%1$s从缠怨藤上摔了下来",
    "death.fell.accident.vines": "%1$s从藤蔓上摔了下来",
    "death.fell.accident.weeping_vines": "%1$s从垂泪藤上摔了下来",
    "death.fell.assist": "%1$s因为%2$s注定要摔死",
    "death.fell.assist.item": "%1$s因为%2$s使用了%3$s注定要摔死",
    "death.fell.finish": "%1$s摔伤得太重并被%2$s完结了生命",
    "death.fell.finish.item": "%1$s摔伤得太重并被%2$s用%3$s完结了生命",
    "death.fell.killer": "%1$s注定要摔死",
}