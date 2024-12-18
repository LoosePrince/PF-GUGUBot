# -*- coding: utf-8 -*-

from mcdreforged.api.types import PluginServerInterface

from .base_system import base_system
from ..data.text import start_command_help
from ..utils import get_style_template

class start_command_system(base_system):
    def __init__(self, 
                 path: str, 
                 server:PluginServerInterface,
                 bot_config):
        super().__init__(path, server, bot_config, 
                         admin_help_msg=start_command_help, 
                         system_name="start_command",
                         alias=["启动指令"])

    def get_func(self, admin:bool=False):
        """ Return allowed function """
        function_list = [
        ]

        if admin:
            function_list += [
                self.help,
                self.add,
                self.remove,
                self.show_list,
                self.enable,
                self.disable,
                self.reload,
                self.exec  # new added
            ]
        return function_list

    def exec(self, parameter, info, bot, reply_style, admin):
        """Reload the data file

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        Output:
            break_signal (bool, None)
        """
        # command: exe
        if parameter[0] not in ['执行', 'exe']:
            return True
                                             
        for _, command in self.data.items():
            self.server.execute(command)
        bot.reply(info, get_style_template('command_success', reply_style))