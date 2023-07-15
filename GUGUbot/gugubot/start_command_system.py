# -*- coding: utf-8 -*-
from .base_system import base_system
from ..data.text import *
from aiocqhttp import CQHttp
from mcdreforged.api.types import PluginServerInterface, Info

class start_command_system(base_system):
    def __init__(self, path:str, help_msg:str = start_command_help):
        super().__init__(path, help_msg)

    def handle_command(self, raw_command:str, bot:CQHttp, info:Info, reply_style:str='正常', *arg, **kargs):
        parameter = raw_command.strip().split(maxsplit=2)[1:]                                

        super().handle_command(raw_command, bot, info, reply_style, *arg, **kargs)

        # need a server kargs
        if parameter[0] in ['执行', 'exe']:                                          
            self.exec(kargs['server'])
            bot.reply(info, style[reply_style]['command_success'])

    def exec(self, server:PluginServerInterface)->None:
        for _, command in self.data.items():
            server.execute(command)
