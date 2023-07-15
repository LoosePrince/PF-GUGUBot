# -*- coding: utf-8 -*-
from .base_system import base_system
from ..data.text import ban_word_help

class ban_word_system(base_system):

    def __init__(self, path: str):
        super().__init__(path, ban_word_help)
        
    def check_ban(self, sentence:str):                                                     # 检测违禁词
        for k, v in self.data.items():
            if k in sentence:
                return k, v
        return ()
                