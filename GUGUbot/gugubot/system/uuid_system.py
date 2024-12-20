# -*- coding: utf-8 -*-
from mcdreforged.api.types import PluginServerInterface

from .base_system import base_system
from .bound_system import bound_system
from .whitelist_system import whitelist
from ..data.text import uuid_help
from ..utils import get_style_template

class uuid_system(base_system):
    def __init__(self, 
                 path: str, 
                 server:PluginServerInterface,
                 bot_config,
                 bound_system:bound_system, 
                 whitelist:whitelist):
        self.bound_system = bound_system
        self.whitelist = whitelist
        super().__init__(path, server, bot_config, 
                         admin_help_msg=uuid_help, 
                         system_name="uuid",
                         alias=["uuid"])

    def get_func(self, admin:bool=False):
        """ Return allowed function """
        function_list = []

        if admin:
            function_list += [
                self.help,
                self.show_list,
                self.reload
            ]
        return function_list

    def show_list(self, parameter, info, bot, reply_style, admin):
        """List the word stored

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        Output:
            break_signal (bool, None)
        """
        # command: list
        if parameter[0] not in ['列表','list']:
            return True

        if len(self.data) == 0: # not word                            
            bot.reply(info, get_style_template('no_word', reply_style))
            return         
           
        # Response                        
        respond = "uuid匹配如下：\n"+ \
                '\n'.join([str(k)+'-'+str(v)+'-'+str(self.bound_system[v]) for k,v in self.items() if v in self.bound_system])                                  

        bot.reply(info, respond)

    def match_id(self) -> None:
        """ reload the {uuid: qq_id} dict """
        self.data = {}
        whitelist_dict = {game_name: uuid for uuid, game_name in self.whitelist.items()}
        
        for qq_id, names in self.bound_system.items(): # {qq_id: list[name]}
            for name in names: # [name1, name2]
                clean_name = name.split('(')[0].split('（')[0]
                if clean_name in whitelist_dict:
                    self.data[whitelist_dict[clean_name]] = qq_id

    def reload(self, parameter, info, bot, reply_style, admin):
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
        # command: reload
        if parameter[0] not in ['重载', '刷新', 'reload']:
            return True

        self.match_id()
        bot.reply(info, get_style_template('reload_success', reply_style))
    
    