# -*- coding: utf-8 -*-
from .table import table
from data.text import *
from mcdreforged.api.types import Info

class base_system(object):
    def __init__(self, path:str, help_msg='帮助文件缺失'):
        self.path = path
        self.data = table(self.path)
        self.help_msg = help_msg

    def handle_command(self, raw_command:str, info:Info, bot, reply_style:str='正常', *arg, **kargs):
        parameter = raw_command.strip().split()[1:]                               
        parameter_length = len(parameter)

        if not parameter_length or parameter[0] in ['帮助', 'help']:                         
            bot.reply(info, self.help_msg)

        elif parameter[0] in ['添加', 'add']: 
            # lack of para          
            if parameter_length < 3:                                                
                bot.reply(info, style[reply_style]['add_lack_parameter'])
                return
            # get word & response
            word, response = parameter[1], parameter[2]
            # existed
            if word in self.data:
                bot.reply(info, style[reply_style]['add_existed'])
                return 
            # add 
            self.data[word] = response
            bot.reply(info, style[reply_style]['add_success'])
                
        elif parameter[0] in ['删除','移除', 'del']:
            # lack para
            if parameter_length < 2:                                                  
                bot.reply(info, style[reply_style]['del_lack_parameter'])
                return
            # # get word
            word = parameter[1]
            # not exists
            if word not in self.data:    
                bot.reply(info, style[reply_style]['del_no_exist'])
            # del
            del self.data[word]                                            
            bot.reply(info, style[reply_style]['del_success'])
        
        elif parameter[0] in ['列表','list']:
            # not word
            if len(self.data) == 0:                                                    
                bot.reply(info, style[reply_style]['no_word'])
                return            
            # print                                                          
            key_string = '\n'.join(self.data.keys())
            reply_string = style[reply_style]['list'].format(key_string)
            bot.reply(info, reply_string)

        elif parameter[0] in ['重载', '刷新', 'reload']:                               
            self.reload()
            bot.reply(info, style[reply_style]['reload_success'])

    def reload(self)->None:
        self.data.load()

    def __contains__(self, key:str)->bool:
        return key in self.data
    
    def __getitem__(self, key:str)->str: 
        return self.data[key] 
    