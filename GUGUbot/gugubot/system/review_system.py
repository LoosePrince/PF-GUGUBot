# -*- coding: utf-8 -*-
from collections import defaultdict

from mcdreforged.api.types import PluginServerInterface

from .base_system import base_system
from ..data.text import shenhe_help
from ..utils import get_style_template

class shenhe_system(base_system):
    def __init__(self, 
                 path: str, 
                 server:PluginServerInterface,
                 bot_config):
        super().__init__(path, server, bot_config, 
                         admin_help_msg=shenhe_help, 
                         system_name="shenhe",
                         alias=["审核"])

    def add(self, parameter, info, bot, reply_style, admin:bool)->bool:
        """Add member into the system

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        Output:
            break_signal (bool, None)
        """
        # command: add <qq id> <alias>
        if parameter[0] not in ['添加', 'add']:
            return True

        if len(parameter) < 3: # lack of parameters                                                     
            bot.reply(info, get_style_template('lack_parameter', reply_style))
            return 
        
        qq_id, alias = parameter[1], parameter[2]
        if alias in self.data: # check exist
            bot.reply(info, '已存在该别名')
            return 
        
        # Add word
        self.data[alias] = qq_id
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
        # command: del <qq_id/alias>
        if parameter[0] not in ['删除','移除', 'del']:
            return True
        
        if len(parameter) < 2: # lack parameter                             
            bot.reply(info, get_style_template('lack_parameter', reply_style))
            return
        
        word = parameter[1]
        if word not in self.data and word not in self.data.values(): # not exists
            bot.reply(info, '审核员不存在哦！')
            return
        
        if word in self.data: # del through alias
            del self.data[word]      

        else: # del through qq_id
            for alias, qq_id in self.data.items():
                if qq_id == word:
                    del self.data[alias]

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
        temp = defaultdict(list)
        for alias, qq_id in self.data.items():
            temp[qq_id].append(alias)
        bot.reply(info, "有如下审核员：\n"+"\n".join([k+'-'+",".join(v) for k,v in temp.items()]))