# -*- coding: utf-8 -*-

from mcdreforged.api.types import PluginServerInterface

from .base_system import base_system
from ..data.text import key_word_help

class key_word_system(base_system):
    def __init__(self, 
                 path: str, 
                 server:PluginServerInterface,
                 bot_config):
        super().__init__(path, server, bot_config, 
                         admin_help_msg=key_word_help, 
                         system_name="key_word",
                         alias=["关键词"])

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
