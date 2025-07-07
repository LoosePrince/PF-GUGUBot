# -*- coding: utf-8 -*-
import json
import os

from pathlib import Path
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True

class autoSaveDict(object):    

    def __init__(
            self, 
            path:str="./default.json", 
            default_content:dict=None, 
            yaml:bool=False
        ) -> None:

        self.yaml = yaml
        self.path = Path(path)
        self.path = self.path.with_suffix(".yml") if self.yaml else self.path

        self.default_content = default_content if default_content else {}

        self.load()    

    #================ file methods ================#
    def load(self) -> None:
        """ Load data from file """
        if os.path.isfile(self.path) and os.path.getsize(self.path) != 0:
            with open(self.path, 'r', encoding='UTF-8') as f:
                if self.yaml:
                    self.data = yaml.load(f)
                else:
                    self.data = json.load(f)
        else:
            self.data = self.default_content
            self.save()

    def save(self) -> None:
        """ Save data to file """
        self.path.parents[0].mkdir(parents=True, exist_ok=True)
        if self.yaml:
            with open(self.path, 'w', encoding='UTF-8') as f:
                yaml.dump(self.data, f)        
        else:
            with open(self.path, 'w', encoding='UTF-8') as f:
                json.dump(self.data, f, ensure_ascii= False)        
    
    #================ dict methods ================#
    def __getitem__(self, key:str):
        return self.data[key]    

    def __setitem__(self, key:str, value):
        self.data[key] = value
        self.save()   

    def __contains__(self,key:str): 
        return key in self.data

    def __delitem__(self,key:str):
        if key in self.data:
            del self.data[key]
            self.save()

    def __iter__(self):
        return iter(self.data.keys())

    def __repr__(self) -> str:
        if self.data is None:
            return ""
        return str(self.data)

    def __len__(self):
        return len(self.data)

    def get(self, key:str, default=None):
        return self.data.get(key, default)

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.items()
    

class botConfig(autoSaveDict):
    def __init__(self, path = "./default.yml", default_content = None, yaml = True, logger = None):
        self.logger = logger
        super().__init__(path, default_content, yaml)

    def addNewConfig(self, server):
        """ Add new configs from latest version to current config """
        # read latest config file from MCDR package
        with server.open_bundled_file("gugubot/data/config_default.yml") as file_handler:
            message = file_handler.read()
        message_unicode = message.decode('utf-8').replace('\r\n', '\n')
        yaml_data = yaml.load(message_unicode)

        # update
        for key, value in self.items():
            if isinstance(value, dict):
                for sub_k, sub_v in value.items():
                    yaml_data[key][sub_k] = sub_v
            else:
                yaml_data[key] = value

        for key in ['group_id', 'admin_id', 'admin_group_id']:
            if key not in self:
                del yaml_data[key]

        self.data = yaml_data
        self.save()

    def load(self):
        self.validate()
        super().load()
        self.plugin_check()

    def plugin_check(self):
        """ Avoid None or empty value in config """
        
        # Not exist/None -> error
        # not list -> [value]
        # extra empty value -> remove empty value
        listTypeConfigs = ["admin_id", "group_id"]

        for config_name in listTypeConfigs:
            if not self.get(config_name):
                if self.logger: self.logger.error(f"请设置 {config_name}")
                continue

            value = self[config_name]
            if not isinstance(value, list):
                self[config_name] = [value]
                continue

            if any(value):
                self[config_name] = [i for i in value if i]
    
        # prevent None value/not list type
        if "admin_group_id" in self:
            if not self["admin_group_id"]:
                self["admin_group_id"] = []
            
            elif not isinstance(self["admin_group_id"], list):
                self["admin_group_id"] = [self["admin_group_id"]]

        self.save()

    def validate(self):
        """Validate config file and prompt user where is wrong, including YAML/JSON syntax errors."""
        # Check YAML or JSON syntax
        if self.yaml:
            try:
                with open(self.path, 'r', encoding='UTF-8') as f:
                    yaml.load(f)
            except Exception as e:
                msg = f"YAML 配置文件语法错误: {e}"
                if self.logger:
                    self.logger.error(msg)
                else:
                    print(msg)
                return False
        else:
            try:
                with open(self.path, 'r', encoding='UTF-8') as f:
                    json.load(f)
            except Exception as e:
                msg = f"JSON 配置文件语法错误: {e}"
                if self.logger:
                    self.logger.error(msg)
                else:
                    print(msg)
                return False
    

