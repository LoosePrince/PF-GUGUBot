# -*- coding: utf-8 -*-
from base_system import base_system
import text

class key_word_system(base_system):
    def __init__(self, path: str, help_msg = text.key_word_help):
        super().__init__(path)
        self.help_msg = help_msg

    def check_response(self, key_word):                                                # 检测关键词
        if key_word in self.data:
            return self.data[key_word]
