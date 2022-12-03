# -*- coding: utf-8 -*-
from base_system import base_system
import text

class shenhe_system(base_system):
    def __init__(self, path: str, help_msg = text.shenhe_help):
        super().__init__(path)
        self.help_msg = help_msg