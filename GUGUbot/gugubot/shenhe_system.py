# -*- coding: utf-8 -*-
from .base_system import base_system
from ..data.text import shenhe_help

class shenhe_system(base_system):
    def __init__(self, path: str, help_msg:str = shenhe_help):
        super().__init__(path, help_msg)

    def under_construct(self)->None:
        raise NotImplementedError