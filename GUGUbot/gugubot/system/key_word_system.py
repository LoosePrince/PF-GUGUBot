# -*- coding: utf-8 -*-
import re
import time

from mcdreforged.api.types import PluginServerInterface

from .base_system import base_system
from ..data.text import key_word_help
from ..utils import get_style_template

class key_word_system(base_system):
    def __init__(self, 
                 path: str, 
                 server:PluginServerInterface,
                 bot_config):
        self.picture_record_dict = {}
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

            self.add_image,
            self.cancel,
        ]

        if admin:
            function_list = [
                self.help,
                self.enable,
                self.disable,
                self.reload
            ] + function_list
        return function_list

    def check_response(self, key_word:str):                                                
        if key_word in self.data:
            return self.data[key_word]

    def add_image(self, parameter, info, bot, reply_style, admin:bool)->bool:
        """Add image into the system

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
        command_prefix = self.bot_config.get("command_prefix", "#")
        parameter = info.content.replace(command_prefix, "", 1)
        if not parameter.startswith("添加图片"):
            return True

        keyword = parameter.replace("添加图片", "", 1).strip()
        if not keyword: # lack of parameters                                                     
            bot.reply(info, get_style_template('lack_parameter', reply_style))
            return 
        
        elif keyword in self.data: # check exist
            bot.reply(info, get_style_template('add_existed', reply_style))
            return 
        
        elif info.user_id in self.picture_record_dict:
            bot.reply(info, get_style_template('add_image_previous_no_done', reply_style))
            return

        self.picture_record_dict[info.user_id] = (keyword, time.time())
        bot.reply(info, get_style_template('add_image_instruction', reply_style))

    def cancel(self, parameter, info, bot, reply_style, admin:bool)->bool:
        """cancel adding image into the system

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        Output:
            break_signal (bool, None)
        """
        command_prefix = self.bot_config.get("command_prefix", "#")
        parameter = info.content.replace(command_prefix, "", 1)
        if not parameter.startswith("取消"):
            return True
        
        elif info.user_id not in self.picture_record_dict:
            return True
        
        del self.picture_record_dict[info.user_id]
        respond = get_style_template('add_cancel', reply_style)

        
        bot.reply(info, respond)

    def add_image_handler(self, info, bot, reply_style)->bool:
        """Adding image into the system

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        Output:
            break_signal (bool, None)
        """
        # user_id added keyword & send image
        if info.user_id not in self.picture_record_dict or \
                not (info.raw_message.startswith('[CQ:image') \
                    or info.raw_message.startswith("[CQ:mface")):
            return True

        # timeout
        if  time.time() - self.picture_record_dict[info.user_id][1] >= 30:
            bot.reply(info, f"添加图片 <{self.picture_record_dict[info.user_id][0]}> 已超时")
            del self.picture_record_dict[info.user_id]
            return

        
        try:  # parse url
            url_match = re.search(r'url=([^,\]]+)', info.raw_message)
            url = url_match.group(1) if url_match else None

            if not url:
                file_match = re.search(r'file=([^\s,\]]+)', info.raw_message)
                url = file_match.group(1) if file_match else None
                
            url = re.sub('&amp;', "&", url)
            
            self.data[self.picture_record_dict[info.user_id][0]]=f"[CQ:image,file={url}]"
            bot.reply(info, get_style_template('add_success', reply_style))

        except Exception as e:
            bot.reply(info, get_style_template('add_image_fail', reply_style))
            self.server.logger.warning(f"保存图片失败：{info.raw_message}\n报错如下： {e}")

        del self.picture_record_dict[info.user_id]          
    
        