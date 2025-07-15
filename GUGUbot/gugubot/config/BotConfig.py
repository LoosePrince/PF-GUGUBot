import json

from gugubot.config.BasicConfig import BasicConfig, yaml

class BotConfig(BasicConfig):
    def __init__(self, path = "./default.yml", default_content = None, yaml_format = True, logger = None):
        self.logger = logger
        super().__init__(path, default_content, yaml_format)

    def load(self):
        super().load()
        self.plugin_check()

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
        try:
            with open(self.path, 'r', encoding='UTF-8') as f:
                if self.yaml:
                    yaml.load(f)
                else:
                    json.load(f)
        except Exception as e:
            if self.yaml:
                mark = getattr(e, 'problem_mark', None)
                if mark:
                    msg = f"YAML 配置文件语法错误: 出错位置：第 {mark.line + 1} 行，第 {mark.column + 1} 列\n详细信息: {e}"
                else:
                    msg = f"YAML 配置文件语法错误: {e}\n请检查 YAML 文件的缩进和冒号(:)是否正确。"
            else:
                lineno = getattr(e, 'lineno', None)
                colno = getattr(e, 'colno', None)
                if lineno and colno:
                    msg = f"JSON 配置文件语法错误: 出错位置：第 {lineno} 行，第 {colno} 列\n详细信息: {e}"
                else:
                    msg = f"JSON 配置文件语法错误: {e}\n请检查 JSON 文件的格式是否正确。"

                if self.logger:
                    self.logger.error(msg)
                else:
                    print(msg)
                    
            return False
