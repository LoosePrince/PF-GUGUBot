# PF-QQchat
#### PFingan服务器MCDRQQ机器人插件  
源：[QQChat-用于连接Minecraft和QQ的插件](https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/.archived/qq_chat)<br>
修改：[XueK__ - 前往项目](https://github.com/XueK66/PF-MCDRQQchat)
### 这是基于原插件的修改版本

## 依赖
### Python包
- requests
### 前置插件
- [CoolQAPI](https://github.com/AnzhiZhang/CoolQAPI)
- [OnlinePlayerAPI](https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/.archived/OnlinePlayerAPI)
- [ConfigAPI](https://github.com/MCDReforged/ConfigAPI)
- [JsonDataAPI](https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/.archived/JsonDataAPI)

## 功能列表
QQ部分帮助，向QQ机器人发送，可以私聊也可以群聊发送 `/help`
<br>基本功能：聊天互相转发
#### 部分功能在群聊和私聊都能使用
### 管理员部分，请私聊机器人
```
/bound 查看绑定相关帮助
/whitelist 查看白名单相关帮助
/start_command 查看启动指令相关帮助
/ban_word 查看违禁词相关帮助
/key_word 查看关键词相关帮助
/ingame_key_word 查看游戏内关键词相关帮助
/uuid 查看uuid 匹配相关帮助
/name 查看机器人名字相关帮助
/shenhe 协助审核功能(不在私聊帮助列表显示)
```
* 游戏ID与QQ绑定 `/bound`
```
/bound list  查看绑定列表
/bound check <QQ号> 查询绑定ID
/bound unbound <QQ号> 解除绑定
/bound <QQ号> <游戏ID> 绑定新ID
```
* 白名单管理 `/whitelist`
```
/whitelist add <target> 添加白名单成员
/whitelist list 列出白名单成员
/whitelist off 关闭白名单
/whitelist on 开启白名单
/whitelist reload 重载白名单
/whitelist remove <target> 删除白名单成员
<target> 可以是玩家名/目标选择器/UUID
```
* 服务器启动时执行指令 `/start_command`
```
/start_command add <名称> <指令> 添加启动指令
/start_command list 查看现有启动指令
/start_command del <名称> 删除指定启动指令
/start_command on 开启开服指令
/start_command off 关闭开服指令
/start_command exe 执行一遍开服指令
/start_command reload 重载开服指令
```
* 触发(包含模式)违禁词自动撤回 `/ban_word`
```
/ban_word add <违禁词> <违禁理由> 添加违禁词
/ban_word list 显示违禁词表列及理由
/ban_word del <违禁词> 删除指定违禁词
/ban_word on 开启违禁词
/ban_word off 关闭违禁词
/ban_word reload 重载违禁词
```
* 发送关键词（完全匹配模式）自动回复，支持图片 `/key_word`
```
/key_word on 开启关键词
/key_word off 关闭关键词
/key_word reload 重载关键词
/klist 显示关键词列表
/add <关键词> <回复> 添加关键词
/addp <关键词> 添加关键词图片回复，请在发送过后发送将要作为回复的图片
/del <关键词> 删除指定关键词
```
* 游戏内关键词 `/ingame_key_word`
```
/ingame_key_word on 开启游戏内关键词
/ingame_key_word off 关闭游戏内关键词
/ingame_key_word reload 重载游戏内关键词
```
* uuid 匹配 游戏ID，如果有时游戏内现实ID不匹配，可以尝试重新匹配一下uuid `/uuid`
```
/uuid list 查看uuid绑定表
/uuid reload 重新匹配uuid
/uuid update <老ID> <新ID> 改白名单的名字
/uuid name 查看白名单名字
```
* 让机器人昵称显示为在线人数 `/name`
```
/name on 机器人名字显示为在线人数,需要在配置文件内配置服务器公网或IP域名和端口(一直显示会占用少许服务器资源)
/name off 机器人名字为特殊空白名字，如果不支持请关闭此功能，然后你就可以自己给机器人命名了
```
* 协助审核,会自动识别加群申请，通过申请填写的回答（请将问题设置为"你的邀请人？"或"你的邀请人?"）的 <别名> 并将请求通过私聊和群聊艾特的方式将申请人昵称和回答发送到审核员，若审核员游戏在线还会发送到游戏，此时审核员只需在游戏、群聊或私聊发送通过即可同意申请 `/shenhe`
```
/shenhe on 开启自动审核
/shenhe off 关闭自动审核
/shenhe add <QQ号> <别名> 添加审核员的别名(匹配用)
/shenhe del <QQ号> 删除审核员
/shenhe list 审核员列表
```

### 群聊部分，请在群内使用
```
/help 获取机器人帮助
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
/style 机器人风格帮助
```
* 机器人回复风格切换 `/style`
```
/style        风格帮助
/style list   风格列表
/style <风格> 切换至指定风格
```
内置模式：`普通` `傲娇`

## 配置文件
```
# 填管理员QQ号，有几个就填几个
admin_id: [123456, 7891011]
# true为开启，false为关闭
command: {
  # ban_word:违禁词测回
  ban_word: true, 
  # ingame_key_word:游戏内关键词回复
  ingame_key_word: true, 
  # key_word:群内关键词回复
  key_word: true, 
  # list:在线查询
  list: true, 
  # 获取服务器内聊天内容
  mc: true, 
  # 机器人昵称
  name: true, 
  # 获取QQ聊天内容
  qq: true, 
  # 开服指令
  start_command: true, 
  # 白名单功能
  whitelist: true, 
  # 辅助审核功能
  shenhe: true
  }
# 配置文件读取
dict_address: {
  # 违禁词
  ban_word_dict: .//config//QQChat//ban_word.json, 
  # 关键词
  key_word_dict: .//config//QQChat//key_word.json, 
  # 游戏内关键词
  key_word_ingame_dict: .//config//QQChat//key_word_ingame.json, 
  # 辅助审核日志文件
  shenhe_log: .//config//QQChat//shenhe_log.txt, 
  # 开服指令
  start_command_dict: .//config//QQChat//start_commands.json, 
  # uuid绑定
  uuid_qqid: .//config//QQChat//uuid_qqid.json, 
  # 辅助审核
  shenheman: .//config//QQChat//shenheman.json, 
  # 白名单
  whitelist: .//server//whitelist.json
  }
# 转发设置
forward: {
  # 服务器往QQ群转发
  mc_to_qq: true,
  # QQ群往服务器转发 
  qq_to_mc: true
  }
# 服务器IP，请填公网域名，端口号前面那段，例：mcserver.com:25565
game_ip: mcserver.com
# 服务器端口
game_port: '25565'
# 填写群号,有几个就填几个
group_id: [123456,7891011]
# 绑定ID自动绑定服务器白名单
whitelist_add_with_bound: true
# 退群自动删除绑定和白名单
whitelist_remove_with_leave: true
```

