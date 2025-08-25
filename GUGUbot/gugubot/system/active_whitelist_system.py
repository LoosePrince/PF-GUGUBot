# ActiveAWhiteList System
# 用于管理活跃白名单玩家
from gugubot.system.base_system import base_system
from gugubot.data.text import active_awhitelist_help

class ActiveWhiteListSystem(base_system):
    def __init__(self, path=None, server=None, bot_config=None):
        super().__init__(
            path,
            server,
            bot_config,
            system_name="activewhitelist",
            alias=["活跃白名单", "activewhitelist"],
            admin_help_msg=active_awhitelist_help
        )

    def add(self, parameter, info, bot, reply_style, admin:bool):
        """覆盖base_system的add方法，参数与base_system一致"""
        # command: add <player>
        if parameter[0] not in ['添加', 'add']:
            return True

        if len(parameter) < 2:
            bot.reply(info, "参数不足，需要指定玩家名")
            return

        player = parameter[1]
        if player in self.data:
            bot.reply(info, f"{player} 已在活跃白名单中")
            return

        self.data[player] = True
        self.data.save()
        bot.reply(info, f"{player} 已添加到活跃白名单")

    def remove(self, parameter, info, bot, reply_style, admin:bool):
        """覆盖base_system的remove方法，参数与base_system一致"""
        # command: del <player>
        if parameter[0] not in ['删除','移除', 'del']:
            return True

        if len(parameter) < 2:
            bot.reply(info, "参数不足，需要指定玩家名")
            return

        player = parameter[1]
        if player not in self.data:
            bot.reply(info, f"{player} 不在活跃白名单中")
            return

        del self.data[player]
        self.data.save()
        bot.reply(info, f"{player} 已从活跃白名单移除")

    def add_player(self, player):
        if player not in self.data:
            self.data[player] = True
            self.data.save()
            return True
        return False

    def remove_player(self, player):
        if player in self.data:
            del self.data[player]
            self.data.save()
            return True
        return False

    def is_active(self, player):
        return player in self.data

    def get_all(self):
        return list(self.data.keys())
