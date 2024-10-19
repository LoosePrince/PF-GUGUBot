# -*- coding: utf-8 -*-
from .base_system import base_system
from .data.text import key_word_help

class key_word_system(base_system):
    def __init__(self, path: str, help_msg:str = key_word_help):
        super().__init__(path, help_msg)

    def check_response(self, key_word:str):                                                
        if key_word in self.data:
            return self.data[key_word]
