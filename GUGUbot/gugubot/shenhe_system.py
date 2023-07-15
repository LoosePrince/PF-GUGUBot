# -*- coding: utf-8 -*-
from .base_system import base_system
from ..data.text import *

class shenhe_system(base_system):
    def __init__(self, path: str, help_msg = shenhe_help):
        super().__init__(path)
        self.help_msg = help_msg