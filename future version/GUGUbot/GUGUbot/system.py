# -*- coding: utf-8 -*-
from email.mime import base
from table import table
from text import style

class base_system(object):
    def __init__(self, path:str) -> None:
        self.table = table(path)

    def add(self, key, value, *args, **kwargs):
        if key not in self.table:
            self.table[key] = value
            return True, style[kwargs['style']]['add_success']
        return False, style[kwargs['style']]['key_word_exist']

    def delete(self, key, *args, **kwargs):
        if key in self.table:
            del self.table[key]
            return True, style[kwargs['style']]['delete_success']
        return False, '删除失败, 咕'

    def search(self, *args, **kwargs):
        return self.table.items()

    def change(self, new_key, new_value, *args, **kwargs):
        if new_key in self.table:
            self.table[new_key] = new_value
            return True, '修改成功, 咕'
        return False, '修改失败, 咕'

    def process_command(self, command, *args, **kwargs):
        words = len(command.split())
        operation = command.split()[0]
        if operation in ["添加", "增加"] and words >= 3:
            _, command_key, command_value = command.split(maxsplit=2)
            return self.add(command_key, command_value, *args, **kwargs)

        elif operation in ['删除'] and words >= 2:
            _, command_key = command.split(maxsplit=1)
            return self.delete(command_key, *args, **kwargs)

        elif operation in ['查询','查找','查看'] and words==1:
            return self.search(*args, **kwargs)
        
        elif operation in ['修改'] and words >= 3:
            _, command_key, command_value = command.split(maxsplit=2)
            return self.change(command_key, command_value, *args, **kwargs)
        return '无效指令'

class ban_system(base_system):
    def ban_word_list(self, *args, **kwargs):
        return self.table.keys()
    
    def check_ban(self, string, reply=False, *args, **kwargs):
        for ban_word in self.ban_word_list():
            if ban_word in string:
                reason = self.table[ban_word]
                # required [bot, info, style]
                if reply:
                    kwargs['bot'].delete_msg(kwargs['info'].message_id)
                    kwargs['bot'].reply(kwargs['info'], style[kwargs['style']]['ban_word_find'].format(reason))
                return True, reason
        return False, ''
    
class key_system(base_system):
    def add(self, key, value, ban_system=None, reply = False, *args, **kwargs):
        if ban_system is not None:
            b1, reason1 = ban_system.check_ban(key, reply = reply, *args, **kwargs)
            b2, reason2 = ban_system.check_ban(value, reply = reply, *args, **kwargs)
            if b1: return False, reason1
            elif b2: return False, reason2
        if key not in self.table:
            self.table[key] = value
            return True, style[kwargs['style']]['add_success']
        return False, style[kwargs['style']]['key_word_exist']

    def check_word(self, string, ban_system=None, reply = False, *args, **kwargs):
        if ban_system is not None:
            b1, reason1 = ban_system.check_ban(string, reply = reply)
            if b1: return False, reason1
        # required [bot, info]
        if string in self.table:
            response = self.table[string]
            if reply:
                kwargs['bot'].reply(kwargs['info'], response)
            return True, response
        return False, ''

if __name__ == "__main__":
    key_word_system = key_system('./test.json')
    print(key_word_system.add("1",2))
    print(key_word_system.check_word("1"))
    key_word_system.process_command('添加 1 3')
    print(key_word_system.check_word("1"))
    key_word_system.process_command('添加 1')
    print(key_word_system.process_command('删除 2'))
    print(key_word_system.process_command('查询'))
    print(key_word_system.process_command('查询 ,'))
    print(key_word_system.process_command('修改 1 4'))

    ban_word_system = ban_system('./test.json')
    print(ban_word_system.check_ban('213'))
