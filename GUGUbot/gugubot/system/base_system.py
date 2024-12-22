# -*- coding: utf-8 -*-
from mcdreforged.api.types import PluginServerInterface

from ..data.text import (
    key_word_help,
    ban_word_help,
    start_command_help,
    shenhe_help
)
from ..config import autoSaveDict
from ..utils import get_style_template

class base_system(object):
    def __init__(self, 
                 path:str, 
                 server:PluginServerInterface,
                 bot_config,
                 help_msg:str="", 
                 admin_help_msg:str="",
                 system_name:str="",
                 alias:list=None):
        self.path = path
        self.data = autoSaveDict(path) if path else None
        self.server = server
        self.bot_config = bot_config
        self.help_msg = help_msg
        self.admin_help_msg = admin_help_msg
        self.system_name = system_name
        self.alias = alias if alias else []
        self.alias += [system_name]

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
            ]
        return function_list

    def handle_command(self, raw_command:str, info, bot, admin:bool=False)->bool:
        """handle the command

        Args:
            raw_command (str): raw_command
            info: message info
            bot: qqbot
            admin (bool, optional): Is admin permission? Defaults to False.
        
        Output:
            break_signal (bool, None)
        """
        # validate command
        command_prefix = self.bot_config.get("command_prefix", "#")
        raw_command = raw_command.replace(command_prefix, "", 1)
        if not any([raw_command.startswith(i) for i in self.alias]):
            return 

        reply_style = self.bot_config.get("style", "正常")

        parameter = raw_command.strip().split(maxsplit=3)[1:] # remove system_name        

        function_list = self.get_func(admin)

        for func in function_list:
            continue_loop =  func(
                parameter, info, bot, reply_style, admin
            )

            if not continue_loop: 
                return True
            
    def help(self, parameter, info, bot, _, admin)->bool:
        """Print help msg

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        Output:
            break_signal (bool, None)
        """
        # command: 
        # command: help

        if parameter and parameter[0] not in ['帮助', 'help']:
            return True

        help_msg = self.admin_help_msg if admin else self.help_msg
        command_prefix = self.bot_config.get("command_prefix", "#")
        bot.reply(info, help_msg.replace("#", command_prefix))


    def add(self, parameter, info, bot, reply_style, admin:bool)->bool:
        """Add word into the system

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        Output:
            break_signal (bool, None)
        """
        # command: add <word> <respond>
        if parameter[0] not in ['添加', 'add']:
            return True

        if len(parameter) < 3: # lack of parameters                                                     
            bot.reply(info, get_style_template('lack_parameter', reply_style))
            return 
        
        word, response = parameter[1], parameter[2]
        if word in self.data: # check exist
            bot.reply(info, get_style_template('add_existed', reply_style))
            return 
        
        # Add word
        self.data[word] = response
        bot.reply(info, get_style_template('add_success', reply_style))

    def remove(self, parameter, info, bot, reply_style, admin):
        """Remove word in the system

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style: reply template style
            admin (bool): Admin mode
        Output:
            break_signal (bool, None)
        """
        # command: del <word>
        if parameter[0] not in ['删除','移除', 'del']:
            return True
        
        if len(parameter) < 2: # lack parameter                             
            bot.reply(info, get_style_template('lack_parameter', reply_style))
            return
        
        word = parameter[1]
        if word not in self.data: # not exists
            bot.reply(info, get_style_template('del_no_exist', reply_style))
            return
        
        # del
        del self.data[word]                                            
        bot.reply(info, get_style_template('delete_success', reply_style))

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
        keys_string = '\n'.join(self.data.keys())
        reply_string = get_style_template('list', reply_style).format(keys_string)
        bot.reply(info, reply_string)

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

        self.data.load()
        bot.reply(info, get_style_template('reload_success', reply_style))

    def enable(self, parameter, info, bot, reply_style, admin):
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
        # command: on
        if parameter[0] not in ['开', 'enable', 'on']:
            return True

        self.bot_config["command"][self.system_name] = True
        self.bot_config.save()
        bot.reply(info, f'已开启{self.alias[0]}！')

    def disable(self, parameter, info, bot, reply_style, admin):
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
        # command: off
        if parameter[0] not in ['关', 'disable', 'off']:
            return True
        
        self.bot_config["command"][self.system_name] = False
        self.bot_config.save()
        bot.reply(info, f'已关闭{self.alias[0]}！')
        
    def __contains__(self, key:str)->bool:
        return key in self.data
    
    def __getitem__(self, key:str)->str: 
        return self.data[key] 
    
    def __setitem__(self, key:str, value):
        self.data[key] = value   

    def __delitem__(self, key:str):
        if key in self.data:
            del self.data[key]
            self.data.save()

    def get(self, key, default=None):
        if key in self:
            return self[key]
        return default

    def keys(self):
        if self.data is not None:
            return self.data.keys()
    
    def values(self):
        if self.data is not None:
            return self.data.values()

    def items(self):
        if self.data is not None:
            return self.data.items()
