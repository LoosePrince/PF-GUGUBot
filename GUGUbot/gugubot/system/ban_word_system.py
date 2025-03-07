# -*- coding: utf-8 -*-
import json

from mcdreforged.api.types import PluginServerInterface

from gugubot.system.base_system import base_system
from gugubot.data.text import ban_word_help
from gugubot.utils.style import get_style_template

class ban_word_system(base_system):

    def __init__(self, 
                 path: str, 
                 server:PluginServerInterface,
                 bot_config):
        super().__init__(path, server, bot_config, 
                         admin_help_msg=ban_word_help,
                         system_name="ban_word",
                         alias=["违禁词"])

    def check_ban(self, sentence:str):  
        """ Check if ban word exist """
        for ban_word, respond in self.data.items():
            if ban_word in sentence:
                return ban_word, respond
        return ()
    
    def handle_banned_word_mc(self, player, message)->bool:
        """Check if ban word in the message

        Args:
            player : player info
            message : mc message

        Returns:
            bool: ban_word exist
        """
        if self.bot_config['command']['ban_word']:
            ban_response = self.check_ban(message)
            if ban_response:
                temp = json.dumps({
                    "text": f"消息包含违禁词无法转发到群聊请修改后重发，维护和谐游戏人人有责。\n违禁理由：{ban_response[1]}",
                    "color": "gray",
                    "italic": True
                })
                self.server.execute(f'tellraw {player} {temp}')
                return True
        return False
    
    def handle_banned_word_qq(self, info, bot, reply_style:str="正常")->bool:
        """Check if ban word in the message

        Args:
            info: qq info
            bot: qq bot

        Returns:
            bool: ban_word exist
        """
        if self.bot_config['command']['ban_word'] and (ban_response := self.check_ban(info.content)):
            # 包含违禁词 -> 撤回 + 提示 + 不转发
            bot.delete_msg(info.message_id)
            bot.reply(info, get_style_template('ban_word_find', reply_style).format(ban_response[1]))
            return True
        return False