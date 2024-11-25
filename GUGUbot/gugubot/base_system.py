# -*- coding: utf-8 -*-
from .table import table
from .utils import get_style_template
from mcdreforged.api.types import Info

class base_system(object):
    def __init__(self, path:str, help_msg='帮助文件缺失'):
        self.path = path
        self.data = table(self.path)
        self.help_msg = help_msg

    def handle_command(self, raw_command:str, info:Info, bot, reply_style:str='正常', *arg, **kargs):
        parameter = raw_command.strip().split(maxsplit=3)[1:]                               
        parameter_length = len(parameter)

        if not parameter_length or parameter[0] in ['帮助', 'help']:                         
            bot.reply(info, self.help_msg)

        elif parameter[0] in ['添加', 'add']: 
            # lack of para          
            if parameter_length < 3:                                                
                bot.reply(info, get_style_template('lack_parameter', reply_style))
                return
            # get word & response
            word, response = parameter[1], parameter[2]
            # existed
            if word in self.data:
                bot.reply(info, get_style_template('add_existed', reply_style))
                return 
            # add 
            self.data[word] = response
            bot.reply(info, get_style_template('add_success', reply_style))
                
        elif parameter[0] in ['删除','移除', 'del']:
            # lack para
            if parameter_length < 2:                                                  
                bot.reply(info, get_style_template('lack_parameter', reply_style))
                return
            # # get word
            word = parameter[1]
            # not exists
            if word not in self.data:    
                bot.reply(info, get_style_template('del_no_exist', reply_style))
                return
            # del
            del self.data[word]                                            
            bot.reply(info, get_style_template('delete_success', reply_style))
        
        elif parameter[0] in ['列表','list']:
            # not word
            if len(self.data) == 0:                                                    
                bot.reply(info, get_style_template('no_word', reply_style))
                return            
            # print                                                          
            key_string = '\n'.join(self.data.keys())
            reply_string = get_style_template('list', reply_style).format(key_string)
            bot.reply(info, reply_string)

        elif parameter[0] in ['重载', '刷新', 'reload']:                               
            self.reload()
            bot.reply(info, get_style_template('reload_success', reply_style))

    def reload(self)->None:
        self.data.load()

    def __contains__(self, key:str)->bool:
        return key in self.data
    
    def __getitem__(self, key:str)->str: 
        return self.data[key] 
    
    def __setitem__(self, key:str, value):
        self.data[key] = value   
    