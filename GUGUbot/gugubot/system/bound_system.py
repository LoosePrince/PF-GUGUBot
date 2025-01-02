# -*- coding: utf-8 -*-
import random

from pathlib import Path

from mcdreforged.api.types import PluginServerInterface

from .base_system import base_system
from .whitelist_system import whitelist
from ..data.text import bound_help
from ..utils import get_style_template, is_robot

class bound_system(base_system):
    def __init__(self, 
                 path: str, 
                 server:PluginServerInterface,
                 bot_config,
                 whitelist:whitelist):
        super().__init__(path, server, bot_config, 
                         admin_help_msg=bound_help, 
                         system_name="bound",
                         alias=["绑定"])
        self.whitelist = whitelist
        self.__empty_double_check = None

    def get_func(self, admin:bool=False):
        """ Return allowed function """
        function_list = [
            self.add_group,
        ]

        if admin:
            function_list = [
                self.help,
                self.add_whitelist_switch,
                self.add,
                self.remove,
                self.search,
                self.sync_whitelist,
                self.show_list,
                self.reload,
                self.clean
            ] + function_list
        return function_list

    def get_qq_id(self, player_name:str):
        """Find corresponding player qq_id

        Args:
            player_name (str): player name

        Returns:
            str/None: player qq_id/None (not found)
        """
        for qq_id, name in self.items():
            if player_name in name:
                return qq_id
            
    def add_whitelist_switch(self, parameter, info, bot, reply_style, admin:bool)->bool:
        """Turn on the bound with whitelist

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        Output:
            break_signal (bool, None)
        """
        # command: boundwhitelist on
        if parameter[0] not in ["whitelist", "白名单"]:
            return True
        
        on = ["on", "开"]
        off = ["off", "关"]
        if parameter[1] not in on + off:
            bot.reply(info, get_style_template('lack_parameter', reply_style))
            return 
        
        self.bot_config["whitelist_add_with_bound"] = parameter[1] in on


    def add_group(self, parameter, info, bot, reply_style, admin:bool)->bool:
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
        # command: bound <player_name>
        if len(parameter) >= 2: # pass to add
            return True

        if len(parameter) < 1: # lack of parameters                                                     
            bot.reply(info, get_style_template('lack_parameter', reply_style))
            return 
        
        qq_id, player_name = str(info.user_id), parameter[0]
        if len(self.data.get(qq_id, [])) >= self.bot_config.get("max_bound", 2): # maximum reaches
            bot.reply(info, '绑定数量已达上限')
            return 
        
        elif self.get_qq_id(player_name): # name exists
            bot.reply(info, '该名称已被绑定')
            return

        # Add bound
        if qq_id not in self:
            self.data[qq_id] = []
        self.data[qq_id].append(player_name)
        self.data.save()
        bot.reply(info, f'[CQ:at,qq={qq_id}] {get_style_template("bound_success", reply_style)}')

        if len(self.data[qq_id]) == 1: # change name when first bound
            bot.set_group_card(info.source_id, qq_id, player_name)

        # Add whitelist
        if self.bot_config.get("whitelist_add_with_bound", False):
            self.whitelist.add_player(player_name)
            bot.reply(info, f'[CQ:at,qq={qq_id}] {get_style_template("bound_add_whitelist", reply_style)}')

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
        # command: bound <qq_id> <player_name>
        if not admin: # disallow groupmember to use it
            return True
        
        if not parameter[0].isdigit() and not parameter[0].startswith("[@"):
            return True

        if len(parameter) < 2: # lack of parameters                                                     
            bot.reply(info, get_style_template('lack_parameter', reply_style))
            return 

        qq_id, player_name = parameter[0], parameter[1]
        if qq_id.startswith("[@"): 
            qq_id = qq_id[2:-1]
        if len(self.data.get(qq_id, [])) >= self.bot_config.get("max_bound", 2): # maximum reaches
            bot.reply(info, '绑定数量已达上限')
            return 
        
        elif self.get_qq_id(player_name): # name exists
            bot.reply(info, '该名称已被绑定')
            return

        # Add bound
        if qq_id not in self:
            self.data[qq_id] = []
        self.data[qq_id].append(player_name)
        self.data.save()
        bot.reply(info, '已成功绑定')
        # Add whitelist
        if self.bot_config.get("whitelist_add_with_bound", False):
            self.whitelist.add_player(player_name)
            bot.reply(info, f'@{qq_id} {get_style_template("bound_add_whitelist", reply_style)}')

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
        # command: del <player_name/qq_id>
        if parameter[0] not in ["解绑", "unbound"]:
            return True
        
        if len(parameter) < 2: # lack parameter                             
            bot.reply(info, get_style_template('lack_parameter', reply_style))
            return
        
        word = parameter[1]
        qq_id = self.get_qq_id(word)
        if word not in self and not qq_id: # not exists
            bot.reply(info, f'{word} 未绑定')
            return
        
        if word in self: # word is qq_id
            del self.data[word]                  
        else: # word is player_name -> qq_id will be not None value
            self.data[qq_id].remove(word)
            if not self.data[qq_id]: # remove if empty
                del self.data[qq_id]
        self.data.save()
        bot.reply(info, f'已解除 {word} 绑定的ID')

    def search(self, parameter, info, bot, reply_style, admin):
        """Search the bound record

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        """
        # command: search <player_name/qq_id>
        if parameter[0] not in ['查询','search']:
            return True

        if len(parameter) < 2: # lack parameter                             
            bot.reply(info, get_style_template('lack_parameter', reply_style))
            return
        
        word = parameter[1]
        qq_id = self.get_qq_id(word) if word not in self else word
        if qq_id:
            name = self.data[word]
            bot.reply(info, f'绑定信息:{qq_id} {name}')
            return

        bot.reply(info, f'{word} 未绑定')


    def sync_whitelist(self, parameter, info, bot, reply_style, admin):
        """Search the bound record

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        """
        # command: sync_whitelist
        if parameter[0] not in ['白名单同步','sync_whitelist']:
            return True

        for game_name in self.values():
            self.whitelist.add_player(game_name)
        
        bot.reply(info, "白名单同步完成！")
    

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
            bot.reply(info, '还没有人绑定')
            return         
           
        # Response                                                          
        bound_list = [f'{qqid} - {", ".join(name)}' for qqid, name in self.items()]
        reply_msg = "\n".join(f'{i + 1}. {name}' for i, name in enumerate(bound_list))
        bot.reply(info, reply_msg)

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

    def clean(self, parameter, info, bot, reply_style, admin):
        """Clean the bound and whitelist

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        """
        if parameter[0] not in ["清空", "clean"]:
            return True
        
        if self.__empty_double_check == None:
            self.__empty_double_check = str(random.randint(100000, 999999))
            bot.reply(info, 
                        f'请输入 {self.bot_config["command_prefix"]}绑定 清空 {self.__empty_double_check} 来清空')
        elif len(parameter) >= 2 and self.__empty_double_check == parameter[1]:
            self.data.data = {}
            self.data.save() # 清空绑定

            for player_name in self.whitelist.values():
                self.whitelist.remove_player(player_name)

            bot.reply(info, '已成功清除')
            self.__empty_double_check = None

    def handle_bound_notice(self, info, bot)->bool:
        command_prefix = self.bot_config["command_prefix"]
        if self.bot_config.get('bound_notice', True) \
            and str(info.user_id) not in self \
            and not is_robot(bot, info.source_id, info.user_id):
            if bot.can_send_image(): # check if can send message
                bot.reply(info, f'[CQ:at,qq={info.user_id}][CQ:image,file={Path(self.bot_config["dict_address"]["bound_image_path"]).resolve().as_uri()}]')
            else:
                bot.reply(info, f'[CQ:at,qq={info.user_id}] 请使用  {command_prefix}绑定 玩家名称  来绑定~')
            return True
        return False