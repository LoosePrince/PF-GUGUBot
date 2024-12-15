# -*- coding: utf-8 -*-

from mcdreforged.api.types import PluginServerInterface

from .base_system import base_system
from ..data.text import ingame_key_word_help
from ..utils import get_style_template

class ingame_key_word_system(base_system):
    def __init__(self, 
                 path: str, 
                 server:PluginServerInterface,
                 bot_config):
        super().__init__(path, server, bot_config, 
                         admin_help_msg=ingame_key_word_help,
                         system_name="ingame_key_word", 
                         alias=["游戏关键词"])

    def get_func(self, admin:bool=False):
        """ Return allowed function """
        function_list = [
            self.add,
            self.remove,
            self.show_list,
        ]

        if admin:
            function_list += [
                self.help,
                self.enable,
                self.disable,
                self.reload
            ]
        return function_list

    def check_response(self, key_word:str):                                                
        if key_word in self.data:
            return self.data[key_word]
        
    def handle_ingame_keyword(self, server, info):
        if self.bot_config['command']['ingame_key_word']:
            if info.content.startswith('!!add '):
                return self.__add_ingame_keyword(server, info)
            elif info.content.startswith('!!del '):
                return self.__delete_ingame_keyword(server, info)
        return False
        
    def __add_ingame_keyword(self, server, info):
        temp = info.content.replace("!!add", "", 1).strip().split(maxsplit=1)
        if len(temp) == 2 and temp[0] not in self:
            self.data[temp[0]] = temp[1]
            server.say(get_style_template('add_success', self.style))
        else:
            server.say('关键词重复或者指令无效~')
        return True
    
    def __delete_ingame_keyword(self, server, info):
        key_word = info.content.replace("!!del", "", 1).strip()
        if key_word in self:
            del self[key_word]
            server.say(get_style_template('delete_success', self.style))
        else:
            server.say('未找到对应关键词~')
        return True
    
    def check_ingame_keyword(self, server, info, bot, message):
        if self.bot_config["command"]["ingame_key_word"]:
            response = self.check_response(message)
            if response:
                bot.reply(info, response)
                server.say(f'§a[机器人] §f{response}')

