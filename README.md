# PF-QQchat
#### PFingan服务器MCDRQQ机器人插件  
源：[QQChat-用于连接Minecraft和QQ的插件](https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/qq_chat)<br>
修改：XueK__ [前往主页](https://github.com/XueK66)
### 这是基于原插件的修改版本

## 依赖
### Python包
- [Python™](https://www.python.org/)
### Python模块
- 已存储在插件对应的文件夹内的 [requirements.txt](requirements.txt) 中, 可以使用 `pip install -r requirements.txt` 安装
### 前置插件
- [qq_api](https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/qq_api)

## 功能列表
QQ部分帮助，向QQ机器人发送，可以私聊也可以群聊发送 `#帮助`
<br>基本功能：聊天互相转发
#### 部分功能在群聊和私聊都能使用
### 管理员部分，请私聊机器人
```
#绑定   -> 查看绑定相关帮助
#白名单 -> 查看白名单相关帮助
#启动指令 -> 查看启动指令相关帮助
#违禁词 -> 查看违禁词相关帮助
#关键词 -> 查看关键词相关帮助
#游戏内关键词 -> 查看游戏内关键词相关帮助
#uuid   -> 查看uuid 匹配相关帮助
#名字   -> 查看机器人名字相关帮助
#审核   -> 协助审核功能
```
* 游戏ID与QQ绑定 `#绑定`
```
#绑定 列表 -> 查看绑定列表
#绑定 查询 <QQ号> -> 查询绑定ID
#绑定 解绑 <QQ号> -> 解除绑定
#绑定 <QQ号> <游戏ID> -> 绑定新ID
```
* 白名单管理 `#白名单`
```
#白名单 添加 <target> -> 添加白名单成员
#白名单 列表 -> 列出白名单成员
#白名单 关   -> 关闭白名单
#白名单 开   -> 开启白名单
#白名单 重载 -> 重载白名单
#白名单 删除 <target> -> 删除白名单成员
<target> 可以是玩家名/目标选择器/UUID
```
* 服务器启动时执行指令 `#启动指令`
```
#启动指令 添加 <名称> <指令> -> 添加启动指令
#启动指令 列表 -> 查看现有启动指令
#启动指令 删除 <名称> -> 删除指定启动指令
#启动指令 开   -> 开启开服指令
#启动指令 关   -> 关闭开服指令
#启动指令 执行 -> 执行一遍开服指令
#启动指令 重载 -> 重载开服指令
```
* 触发(包含模式)违禁词自动撤回 `#违禁词`
```
#违禁词 添加 <违禁词> <违禁理由> -> 添加违禁词
#违禁词 列表 -> 显示违禁词列表及理由
#违禁词 删除 <违禁词> -> 删除指定违禁词
#违禁词 开   -> 开启违禁词
#违禁词 关   -> 关闭违禁词
#违禁词 重载 -> 重载违禁词
```
* 发送关键词（完全匹配模式）自动回复，支持图片 `#关键词`
```
#关键词 开   -> 开启关键词
#关键词 关   -> 关闭关键词
#关键词 重载 -> 重载关键词
#关键词 列表 -> 显示关键词列表
#添加 <关键词> <回复> -> 添加关键词
#删除 <关键词> -> 删除指定关键词
```
* 游戏内关键词 `#游戏内关键词`
```
#不再提供开关
```
* uuid 匹配 游戏ID，如果有时游戏内现实ID不匹配，可以尝试重新匹配一下uuid `#uuid`
```
#uuid 列表   -> 查看uuid绑定表
#uuid 重载 -> 重新匹配uuid
#uuid 更新 <老ID> <新ID> -> 改白名单的名字
/uuid name 查看白名单名字 #此功能已失去
```
* 让机器人昵称显示为在线人数 `#名字`
```
#名字 开 -> 机器人名字显示为在线人数,需要在配置文件内配置服务器公网或IP域名和端口(一直显示会占用少许服务器资源)
#名字 关 -> 机器人名字为特殊空白名字，如果不支持请关闭此功能，然后你就可以自己给机器人命名了
```
* 协助审核,会自动识别加群申请，通过申请填写的回答（请将问题设置为"你的邀请人？"或"你的邀请人?"）的 <别名> 并将请求通过私聊和群聊艾特的方式将申请人昵称和回答发送到审核员，若审核员游戏在线还会发送到游戏，此时审核员只需在游戏、群聊或私聊发送通过即可同意申请 `#审核`
```
#审核 开 -> 开启自动审核
#审核 关 -> 关闭自动审核
#审核 添加 <QQ号> <别名> -> 添加审核员的别名(匹配用)
#审核 删除 <QQ号> -> 删除审核员
#审核 列表 -> 审核员列表
```

### 群聊部分，请在群内使用
```
#玩家 -> 获取在线玩家列表
#假人 -> 获取在线假人列表
#绑定 <游戏ID> -> 绑定你的游戏ID
#mc <消息> -> 向游戏内发送消息（可以触发游戏内关键词）
#风格 -> 机器人风格帮助
#游戏关键词 列表 -> 显示现有游戏内关键词列表
#删除假人 <假人名字> -> 删除游戏内指定假人

关键词相关：
#添加 <关键词> <回复> -> 添加游戏内关键词回复
#添加图片 <关键词> -> 添加关键词图片
#删除 <关键词> -> 删除关键词
#列表 -> 获取关键词回复列表
```
* 机器人回复风格切换 `#风格`
```
#风格 列表   -> 风格列表
#风格 <风格> -> 切换至指定风格
```
- 内置模式：`普通` `傲娇`
- AI生成后内置的模式：`雌小鬼` `御姐` `萝莉` `波奇酱` `病娇` `中二病`

# QQAPI

> QQ bot API.

## 说明

### QQ Bot 配置（配置方法源自原始插件说明）

推荐使用 [go-cqhttp](https://github.com/Mrs4s/go-cqhttp).

在`account`字段中设置QQ帐号和密码：

```yaml
account:
  uin: 1233456
  password: ''
```

推荐使用WebSocket，请将配置中的 `http` 设置为 `false` ，将 `websocket` 设置为 `true` 。 然后在 go-cqhttp 配置的 `servers` 字段中设置 `ws-reverse` （此示例配置应与 QQAPI 的默认配置匹配）：

```yaml
servers:
  - ws-reverse:
      universal: ws://127.0.0.1:5700/ws/
      reconnect-interval: 3000
```

---

如果您想使用 HTTP，请将配置中的 `http` 设置为 `true` ，将 `websocket` 设置为 `false` 。 然后在 go-cqhttp 配置的 `servers` 字段中设置 `http` （此示例配置应与 QQAPI 的默认配置匹配）：

```yaml
servers:
  - http:
      address: 0.0.0.0:5700
      post:
      - url: http://127.0.0.1:5701/
```

## 配置文件

| 配置项 | 默认值 | 说明 |
| - | - | - |
| http.enable | `false` | 是否使用 HTTP |
| http.post_host | `127.0.0.1` | 接收数据上报的地址 |
| http.post_port | `5701` | 对应 go-cqhttp 的 HTTP 监听端口 |
| http.api_host | `127.0.0.1` | 对应 go-cqhttp 的地址 |
| http.api_port | `5700` | 对应 go-cqhttp `url` 配置的端口 |
| websocket.enable | `true` | 是否使用 WebSocket |
| websocket.host | `127.0.0.1` | 对应 go-cqhttp 的地址 |
| websocket.port | `5700` | 对应 go-cqhttp 的 WebSocket 监听端口 |

### 关于多服使用

本插件不提供多服功能，但仍然保留原本拥有的功能，不保证能够正常使用，如需使用请查看原始插件

#### 指令

| 指令 | 功能 |
| - | - |
| stop | 关闭QQBot |
| help | 获取帮助 |
| reload config | 重载配置文件 |
| debug thread | 查看线程列表 |

#### 配置

| 配置项 | 默认值 | 说明 |
| - | - | - |
| webscocket | `false` | 是否使用 WebSocket（为 true 则使用 HTTP） |
| host | `127.0.0.1` | 接收数据上报的地址 |
| port | `5700` | 对应 go-cqhttp 的 HTTP 监听端口 |
| server_list | 详见下文 | 需要转发的服务器列表 |
| debug_mode | `false` | 调试模式 |

`server_list`

需要转发的服务器列表, 参照以下格式填写

```yaml
example:
  host: 127.0.0.1
  port: 5701
```

> 你还需要修改 QQAPI 配置文件的 `post_host`, `post_port` 使其与 `server_list` 的内容对应
>
> 建议从 `5701` 向上增加，如第一个服为 `5701` 第二个服为 `5702`

## 开发

请查看原始插件说明，如有需求请提交问题

### 事件

当从QQ接收到消息, 会触发以下各类事件

每个事件监听器需要使用 `register_event_listener` API 注册, 事件ID为 `qq_api.事件名`

- `server`：[PluginServerInterface](https://mcdreforged.readthedocs.io/zh_CN/latest/code_references/PluginServerInterface.html)
- `bot`：[CQHttp](https://aiocqhttp.nonebot.dev/module/aiocqhttp/index.html#aiocqhttp.CQHttp)
- `event`：[Event](https://aiocqhttp.nonebot.dev/module/aiocqhttp/index.html#aiocqhttp.Event)，其中 `on_message` 的参数为 `MessageEvent`，增加了 `content` 属性，为处理后的消息。

| 事件 | 参考 |
| - | - |
| on_message(server, bot, event) | [on_message](https://aiocqhttp.nonebot.dev/module/aiocqhttp/index.html#aiocqhttp.CQHttp.on_message) |
| on_notice(server, bot, event) | [on_notice](https://aiocqhttp.nonebot.dev/module/aiocqhttp/index.html#aiocqhttp.CQHttp.on_notice) |
| on_request(server, bot, event) | [on_request](https://aiocqhttp.nonebot.dev/module/aiocqhttp/index.html#aiocqhttp.CQHttp.on_request) |
| on_meta_event(server, bot, event) | [on_meta_event](https://aiocqhttp.nonebot.dev/module/aiocqhttp/index.html#aiocqhttp.CQHttp.on_meta_event) |

### API

#### get_event_loop()

用于获取 `asyncio` 的 `event_loop`。

#### get_bot()

用于获取 `CQHttp` 的实例。


## 配置文件
[点击查看配置文件说明](https://github.com/LoosePrince/PF-GUGUBot/blob/main/Config-QQChat.yml)

# 有bug或是新的idea
提个Issue!有空的话会回复滴！

# TODO
- [ ] 字体的路径问题

# 使用条款
- 禁止声明为你原创
- 在关键词回复处添加以下关键词 `插件来源` -> `https://github.com/LoosePrince/PF-MCDRQQchat`
- 禁止商业服使用、盈利等
- 禁止售卖
- 允许二次创作，但请标明来源
