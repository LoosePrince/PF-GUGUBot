# -*- coding: utf-8 -*-
import time

from collections import defaultdict

from mcdreforged.api.types import PluginServerInterface

from gugubot.system.base_system import base_system
from gugubot.data.text import shenhe_help
from gugubot.utils.style import get_style_template

class shenhe_system(base_system):
    def __init__(self, 
                 path: str, 
                 server:PluginServerInterface,
                 bot_config):
        self.review_queue = {}
        super().__init__(path, server, bot_config, 
                         admin_help_msg=shenhe_help, 
                         system_name="shenhe",
                         alias=["审核"])

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
        for v in self.values(): # check exist
            if alias in v:
                bot.reply(info, '已存在该别名')
                return 
        
        # Add word
        self.data[qq_id] = self.data.get(qq_id, []) + [alias]
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
        if word not in self.data and word not in self.values(): # not exists
            bot.reply(info, '审核员不存在哦！')
            return
        
        if word in self.data: # del through qq_id
            del self.data[word]      

        else: # del through alias
            for qq_id, alias in self.items():
                if alias == word:
                    self.data[qq_id].remove(alias)
                    return

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
        for qq_id, alias in self.data.items():
            temp[qq_id].append(alias)
        bot.reply(info, "有如下审核员：\n"+"\n".join([k+'-'+",".join(v) for k,v in temp.items()]))

    def respond(self, raw_commend, info, bot, reply_style):
        """Handle the respond from registed admin

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
        Output:
            break_signal (bool, None)
        """
        # command: list
        parameter = raw_commend.replace(self.bot_config["command_prefix"], "", 1).split()
        agree_list = ['agree', "同意", "通过"]
        disagree_list = ['disagree', "拒绝", "不通过"]
        if parameter[0] not in agree_list + disagree_list:
            return True

        action:bool = parameter[0] in agree_list
        qq_id = info.user_id
        if qq_id not in self or not self.review_queue[qq_id]: # no admin or not this admin
            return
        
        request_name, flag, sub_type = self.review_queue[qq_id].pop(0)
        bot.set_group_add_request_sync(flag, sub_type, action) # send command to bot
        
        with open(self.bot_config["dict_address"]['shenhe_log'], 'a+', encoding='utf-8') as f:  # record log
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} {flag} {qq_id} {'通过' if action else '拒绝'}\n")
        
        template = 'authorization_pass' if action else 'authorization_reject'
        bot.reply(info, get_style_template(template, reply_style).format(flag)) # bot reply 

    def get_id(self, name:str)->str:
        """Return admin qq_id

        Args:
            name (str): admin name

        Returns:
            str: qq_id
        """

        for k, v in self.items():
            if name in v:
                return k
        
        return "" if not self.data else list(self.keys())[0]