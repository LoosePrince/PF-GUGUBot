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
> 此Github文档不再维护详细内容，仅保留必要说明<br>
> 访问官方文档查看更详细的说明: https://pf-doc.pfingan.com/main.html?root=PF-gugubot
>
> 第三方授权文档（编写中）：https://docs.pfingan.com/PF-gugubot/

## 文档快速导航
### [GUGUbot](https://pf-doc.pfingan.com/main.html?root=PF-gugubot)
1. [前置依赖](https://pf-doc.pfingan.com/main.html?path=PF-gugubot/前置依赖.md&root=PF-gugubot)
2. [安装（快速开始）](https://pf-doc.pfingan.com/main.html?path=PF-gugubot/快速开始.md&root=PF-gugubot)
3. [功能列表](https://pf-doc.pfingan.com/main.html?path=PF-gugubot/功能列表.md&root=PF-gugubot)
4. [配置](https://pf-doc.pfingan.com/main.html?path=PF-gugubot/配置.md&root=PF-gugubot)
5. [文件说明文档](https://pf-doc.pfingan.com/main.html?path=PF-gugubot/文档说明文档.md&root=PF-gugubot)
5. [疑难解答](https://pf-doc.pfingan.com/main.html?path=常见问题/GUGUbot-疑难解答.md&root=PF-gugubot)
### [CQ-QQ-API](https://pf-doc.pfingan.com/main.html?root=PF-cq-api)
1. [快速开始](https://pf-doc.pfingan.com/main.html?path=PF-cq-api/快速开始.md&root=PF-cq-api)
2. [群友提供的机器人食用指南](https://pf-doc.pfingan.com/main.html?path=PF-cq-api/机器人食用指南.md&root=PF-cq-api)
    - [LiteLoaderQQNT + LLOneBot](https://pf-doc.pfingan.com/main.html?path=PF-cq-api/LLOneBot.md&root=PF-cq-api)
    - [NapCat](https://pf-doc.pfingan.com/main.html?path=PF-cq-api/NapCat.md&root=PF-cq-api)
    - [Lagrange](https://pf-doc.pfingan.com/main.html?path=PF-cq-api/Lagrange.md&root=PF-cq-api)
3. [开发指南](https://pf-doc.pfingan.com/main.html?path=PF-cq-api/开发指南.md&root=PF-cq-api)

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

包括但不限于：关键词、机器人风格、服务器管理、违禁词等

- [GUGUbot - 功能列表](https://pf-doc.pfingan.com/main.html?path=PF-gugubot/功能列表.md&root=PF-gugubot)



## 配置

### 机器人的必要配置
| 配置项 | 默认值 | 说明 |
| - | - | - |
| 正向websocket服务端口 | `8080` | 接收数据上报的端口 |
| 消息上报格式 | CQ码 | 机器人基于CQ码进行解析 |

### 前置cq_qq_api配置

- 请前往：[CQ-QQ-API - 配置](https://pf-doc.pfingan.com/main.html?path=PF-cq-api/快速开始.md&root=PF-cq-api)

### GUGUbot机器人配置
> [!IMPORTANT]
> 非常建议看看[默认的配置文件](https://github.com/LoosePrince/PF-GUGUBot/blob/main/config_default.yml)<br>

**QQ相关设置 - 必要项**
- admin_id: 管理员QQ号 默认拥有GUGUbot管理员权限(仅私聊)
- group_id: 聊天转发的群

**QQ相关设置 - 可选项**
- 请前往：[GUGUbot - 配置](https://pf-doc.pfingan.com/main.html?path=PF-gugubot/配置.md&root=PF-gugubot)


# 有BUG或是新的IDEA
如果需要更多联动或提交想法和问题请提交 [issues](https://github.com/LoosePrince/PF-GUGUBot/issues) 或 QQ [1377820366](http://wpa.qq.com/msgrd?v=3&uin=1377820366&site=qq&menu=yes) 提交！ <br />
如需要帮助或者交流请通过 QQ群 [726741344](https://qm.qq.com/q/TqmRHmTmcU) 进行询问或者交流 <br />
视情况添加，请勿联系他人（开发者: [雪开](https://github.com/XueK66)）

# TODO
- [ ] [多服聚合](https://github.com/LoosePrince/PF-GUGUBot/issues/106)
- [ ] [联动WebUI](https://github.com/LoosePrince/PF-GUGUBot/issues/107) & [WebUI的饼](https://github.com/LoosePrince/PF-MCDR-WebUI/issues/8)

# 贡献

代码贡献：[QQChat](https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/src/qq_chat) | [AnzhiZhang](https://github.com/AnzhiZhang)

技术支持：[@XueK__](https://github.com/XueK66)

反馈提交：请查发布版本

第三方文档：[@Dreamwxz](https://github.com/Dreamwxz) | [PF-plugins](https://docs.pfingan.com/PF-gugubot/)
