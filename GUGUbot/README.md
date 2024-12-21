# PF-QQchat（支持离线服务器）

> PFingan服务器 MCDR的QQ机器人插件，集QQ群管理和白名单管理一体，添加许多功能。

[![页面浏览量计数](https://badges.toozhao.com/badges/01H98QXADB4DYZBRC2EHSEJ4HW/green.svg)](/) 
[![查看次数起始时间](https://img.shields.io/badge/查看次数统计起始于-2023%2F9%2F2-1?style=flat-square)](/)
[![仓库大小](https://img.shields.io/github/repo-size/LoosePrince/PF-GUGUBot?style=flat-square&label=仓库占用)](/) 
[![最新版](https://img.shields.io/github/v/release/LoosePrince/PF-GUGUBot?style=flat-square&label=最新版)](https://github.com/LoosePrince/PF-GUGUBot/releases/latest/download/GUGUbot.mcdr)
[![议题](https://img.shields.io/github/issues/LoosePrince/PF-GUGUBot?style=flat-square&label=Issues)](https://github.com/LoosePrince/PF-GUGUBot/issues) 
[![已关闭issues](https://img.shields.io/github/issues-closed/LoosePrince/PF-GUGUBot?style=flat-square&label=已关闭%20Issues)](https://github.com/LoosePrince/PF-GUGUBot/issues?q=is%3Aissue+is%3Aclosed)
[![下载量](https://img.shields.io/github/downloads/LoosePrince/PF-GUGUBot/total?style=flat-square&label=下载量)](https://github.com/LoosePrince/PF-GUGUBot/releases)
[![最新发布下载量](https://img.shields.io/github/downloads/LoosePrince/PF-GUGUBot/latest/total?style=flat-square&label=最新版本下载量)](https://github.com/LoosePrince/PF-GUGUBot/releases/latest)

> [!NOTE]
> 由于 **GUGUbot** 和 **WebUI** 项目庞大，但迄今为止仅有开发者一名，所以我们从现在开始招募有志者加入我们！<br>
> 有意者请加 QQ[1377820366](http://wpa.qq.com/msgrd?v=3&uin=1377820366&site=qq&menu=yes) 或 QQ群[726741344](https://qm.qq.com/q/TqmRHmTmcU)

> [!TIP]
> [腾讯文档] GUGUbot文档<br>
> 此文档不再维护详细内容，仅保留必要说明<br>
> 访问文档查看更详细的说明: https://docs.qq.com/aio/DTFlheGZKY0RvYnRi

## 腾讯文档快速导航
### [GUGUbot](https://docs.qq.com/aio/DTFlheGZKY0RvYnRi?p=8zf59bKLGJK66HBlVLjqwJ)
1. [前置依赖](https://docs.qq.com/aio/DTFlheGZKY0RvYnRi?p=5lMm6oYzWp4nMSHHrcR1DG)
2. [安装（快速开始）](https://docs.qq.com/aio/DTFlheGZKY0RvYnRi?p=zdYp7EVd2d04QBQ0FrD7sX)
3. [功能列表](https://docs.qq.com/aio/DTFlheGZKY0RvYnRi?p=kKIaQMdRR7IvJ2AMa30Din)
    - [自定义说明](https://docs.qq.com/aio/DTFlheGZKY0RvYnRi?p=pEQyDIrFanCo9ErEZZPncf)
        - [群友提供的风格文件](https://docs.qq.com/aio/DTFlheGZKY0RvYnRi?p=9RglSRIzfpemyJ7gKdYVEM)
4. [配置](https://docs.qq.com/aio/DTFlheGZKY0RvYnRi?p=iXyl6g1K1p1dK2rujfGH7u)
5. [贡献](https://docs.qq.com/aio/DTFlheGZKY0RvYnRi?p=OreXhO8piOO7Ak7RnpPCMp)
6. [疑难解答](https://docs.qq.com/aio/DTFlheGZKY0RvYnRi?p=8kJWVjHPK8Zkujhwd73Zbb)
### [CQ-QQ-API](https://docs.qq.com/aio/DTFlheGZKY0RvYnRi?p=NJ5GySzVisEJ9xQp7iW8P7)
1. [快速开始](https://docs.qq.com/aio/DTFlheGZKY0RvYnRi?p=5PaUIBXxTwyMouazErWqIT)
2. [配置](https://docs.qq.com/aio/DTFlheGZKY0RvYnRi?p=vUShdYdligIgQvmxLZu3s8)
3. [群友提供的机器人食用指南](https://docs.qq.com/aio/DTFlheGZKY0RvYnRi?p=MgrkYFk9OPpK8wZEY8IeBU)
    - 例如：
4. [开发指南](https://docs.qq.com/aio/DTFlheGZKY0RvYnRi?p=kCIVuht8VcP2vDGLqA9VUW)
5. [致谢](https://docs.qq.com/aio/DTFlheGZKY0RvYnRi?p=w6BO9iUIonwXPN8xBof94F)

## 本文档快速导航

- [依赖配置](#依赖配置)
- [快速开始](#安装)
- [功能列表](#功能列表)
  - [基本功能](#基本功能)
  - [游戏内指令](#游戏内指令)
  - [群聊功能](#群聊功能)
  - [管理功能](#管理功能)
- [详细配置](#配置)
  - [前置cq\_qq\_api配置](#前置cq_qq_api配置)
  - [GUGUbot机器人配置](#gugubot机器人配置)
- [有BUG或是新的IDEA](#有bug或是新的idea)
- [TODO](#todo)
- [贡献](#贡献)

## 依赖配置

**Python 包:** 请确保已安装 [Python™](https://www.python.org/) 和 [pip](https://pypi.org/project/pip/) (pip通常在安装完python后会默认安装)。

**Python 模块:** 参考插件目录内的 `requirements.txt` 文件，使用命令 `pip install -r requirements.txt` 进行安装。

#### 前置插件
- [cq_qq_api](https://github.com/XueK66/PF-cq_qq_api/releases)
- [player_ip_logger](https://github.com/LoosePrince/PF-player_ip_logger)
- [online_player_api](https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/src/online_player_api)
- [whitelist_api](https://github.com/Aimerny/MCDRPlugins/tree/main/src/whitelist_api)
#### 可选插件
- [PF-MCDR-WebUI](https://github.com/LoosePrince/PF-MCDR-WebUI) : 在 2.0.0 版本后将是必选前置插件

## 安装
#### MCDR快捷安装: 
1. MCDR服务端输入 `!!MCDR plugin install gugubot`
2. 加载后，在`/config/cq_qq_api/config.json`中配置接收api
3. 加载后，在`/config/GUGUbot/config.yml`中配置机器人
4. 重载 cq_qq_api: `!!MCDR plugin reload cq_qq_api`

#### github下载安装: 
1. 下载[前置插件](#前置插件)并放入`/plugins`
2. 前往[Release](https://github.com/LoosePrince/PF-GUGUBot/releases)下载GUGUbot.mcdr放入`/plugins`
3. 加载后，在`/config/cq_qq_api/config.json`中配置服务
4. 加载后，在`/config/GUGUbot/config.yml`中配置机器人
5. 重载 cq_qq_api: `!!MCDR plugin reload cq_qq_api`

### 必要配置
*机器人*
- **正向websocket服务端口:** 接收数据上报的端口，例如`8080`
- **消息上报格式:** 机器人基于CQ码进行解析

*CQ-qq-api*
- **host:** 接收数据上报的地址，默认 `127.0.0.1`
- **port:** 对应数据上报的端口，默认`8080`

*GUGUbot*
- **admin_id:** 管理员QQ号 默认拥有GUGUbot管理员权限(仅私聊)
- **group_id:** 聊天转发的群

> [!IMPORTANT]
> 注: 如果您在安装完成后启动提示没有配置文件请下载[config_default.yml](https://github.com/LoosePrince/PF-GUGUBot/blob/main/config_default.yml)重名名为`config.yml`放入`/config/GUGUbot/config.yml`再运行<br>
> 请注意，以上仅为必要配置项，如果您想要更加私有的体验，请完整的阅读可选配置项！

## 功能列表
> QQ部分帮助，向QQ机器人发送，可以私聊也可以群聊发送 `#帮助`

#### 基本功能

- **聊天互相转发:** 支持 MCDR 与 QQ 群组/私聊之间的消息互通。
- **白名单绑定:** 支持在QQ群内进行白名单绑定，退群自动解绑；支持离线服务器或者正版与离线的混合服务器。

#### 详细功能

- [GUGUbot - 功能列表 - 腾讯文档](https://docs.qq.com/aio/DTFlheGZKY0RvYnRi?p=kKIaQMdRR7IvJ2AMa30Din)

#### 游戏内指令

```
!!klist','显示游戏内关键词
!!qq <msg>', '向QQ群发送消息(可以触发qq关键词)
!!add <关键词> <回复>','添加游戏内关键词回复
!!del <关键词>','删除指定游戏关键词
@ <QQ名/号> <消息>','让机器人在qq里@
```

#### 群聊功能(管理员私聊触发)

```
命令帮助如下:
#玩家                -> 获取在线玩家列表
#假人                -> 获取在线假人列表
#服务器              -> 同时获取在线玩家和假人列表
#绑定 <游戏ID>       -> 绑定你的游戏ID
#mc <消息>           -> 向游戏内发送消息（可以触发游戏内关键词）
#风格                -> 机器人风格帮助
#游戏关键词 列表     -> 显示现有游戏内关键词列表
#删除假人 <假人名字> -> 删除游戏内指定假人

关键词相关: 
#添加 <关键词> <回复> -> 添加游戏内关键词回复
#添加图片 <关键词>    -> 添加关键词图片
#删除 <关键词>        -> 删除关键词
#列表                 -> 获取关键词回复列表
#帮助                 -> 查看关键词相关帮助
```


#### 管理功能

```
管理员命令帮助如下
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
#重启 -> 重载机器人
```




## 配置

### 机器人的必要配置
| 配置项 | 默认值 | 说明 |
| - | - | - |
| 正向websocket服务端口 | `8080` | 接收数据上报的端口 |
| 消息上报格式 | CQ码 | 机器人基于CQ码进行解析 |

### 前置cq_qq_api配置

| 配置项 | 默认值 | 说明 |
| - | - | - |
| host | `127.0.0.1` | 接收数据上报的地址 |
| port | `8080` | 对应数据上报的端口 | 
| post_path | "" | 对应数据上报的终点名 |
| token | "" | 对应数据上报的token，用于加密信息 |

```
{
    "host": "127.0.0.1",
    "port": 8080,
    "post_path": "",
    "token": ""
}
```

以上为正向websocket

### GUGUbot机器人配置
> [!IMPORTANT]
> 非常建议看看[默认的配置文件](https://github.com/LoosePrince/PF-GUGUBot/blob/main/config_default.yml)<br>

**QQ相关设置 - 必要项**
- admin_id: 管理员QQ号 默认拥有GUGUbot管理员权限(仅私聊)
- group_id: 聊天转发的群

**QQ相关设置 - 可选项**
- 请前往：[GUGUbot - 功能列表 - 腾讯文档](https://docs.qq.com/aio/DTFlheGZKY0RvYnRi?p=iXyl6g1K1p1dK2rujfGH7u)


# 有BUG或是新的IDEA
如果需要更多联动或提交想法和问题请提交 [issues](https://github.com/LoosePrince/PF-GUGUBot/issues) 或 QQ [1377820366](http://wpa.qq.com/msgrd?v=3&uin=1377820366&site=qq&menu=yes) 提交！ <br />
如需要帮助或者交流请通过 QQ群 [726741344](https://qm.qq.com/q/TqmRHmTmcU) 进行询问或者交流 <br />
视情况添加，请勿联系他人（开发者: [雪开](https://github.com/XueK66)）

# TODO
- [ ] [多服聚合](https://github.com/LoosePrince/PF-GUGUBot/issues/106)
- [ ] [联动WebUI](https://github.com/LoosePrince/PF-GUGUBot/issues/107) & [WebUI的饼](https://github.com/LoosePrince/PF-MCDR-WebUI/issues/8)

# 贡献

代码贡献: [QQChat](https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/src/qq_chat) | [AnzhiZhang](https://github.com/AnzhiZhang)

技术支持: [XueK__](https://github.com/XueK66)
