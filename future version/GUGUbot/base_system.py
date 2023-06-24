# -*- coding: utf-8 -*-
from .table import table
from .text import *

class base_system(object):
    def __init__(self, path:str, help_msg='帮助文件缺失'):
        self.path = path
        self.data = table(self.path)
        self.help_msg = help_msg

    def handle_command(self, raw_command, bot, info, reply_style='正常', *arg, **kargs):
        parameter = raw_command.strip().split()[1:]                                 # 移除系统名
        parameter_length = len(parameter)

        if (parameter_length == 1 and parameter[0] == '帮助') or parameter_length == 0:                        # 打印帮助 
            bot.reply(info, self.help_msg)

        elif parameter[0] in ['添加', 'add']:           
            if parameter_length < 3:                                                # 缺少参数
                bot.reply(info, style[reply_style]['lack_parameter'])
            else:
                if word not in self.data:                                           # 正常添加
                    word, response = parameter[1], ' '.join(parameter[2:])
                    self.data[word] = response
                    bot.reply(info, style[reply_style]['add_success'])
                else:                                                               # 已存在
                    bot.reply(info, style[reply_style]['key_word_exist'])
        
        elif parameter[0] in ['删除','移除', 'del']:
            if parameter_length < 2:                                                   # 缺少参数
                bot.reply(info, style[reply_style]['lack_parameter'])
            else:
                word = parameter[1]
                if word in self.data:    
                    del self.data[word]                                                # 正常删除
                    bot.reply(info, style[reply_style]['delete_success'])
                else:                                                                  # 词不存在
                    bot.reply(info, style[reply_style]['del_no_exist'])
        
        elif parameter[0] in ['列表','list']:
            if len(self.data) == 0:                                                    # 无词
                bot.reply(info, style[reply_style]['no_word'])
            else:                                                                      # 正常打印
                temp_string = '\n'.join(self.data.keys())
                bot.reply(info, style[reply_style]['list'].format(temp_string))

        elif parameter[0] in ['重载', '刷新', 'reload']:                               # 重载
            self.data.load()
            bot.reply(info, style[reply_style]['reload_success'])