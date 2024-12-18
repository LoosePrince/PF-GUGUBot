
from mcdreforged.minecraft.rcon.rcon_connection import RconConnection
from ruamel.yaml import YAML


yaml = YAML()
yaml.preserve_quotes = True

class rcon_connector:

    def __init__(self, server):
        self.server = server
        self.rcon = None 

    def connect(self):
        """ connecting the rcon server for command execution """
        self.rcon = None
        try:
            MCDR_rcon_config = self.server.get_mcdr_config()["rcon"]
            if MCDR_rcon_config.get('enable', False) and self.server.is_rcon_running():
                address = str(MCDR_rcon_config['address'])
                port = int(MCDR_rcon_config['port'])
                password = str(MCDR_rcon_config['password'])
                
                self.server.logger.info(f"尝试连接rcon，rcon地址：{address}:{port}")
                self.rcon = RconConnection(address, port, password)
                self.rcon.connect()
        except Exception as e:
            self.server.logger.warning(f"Rcon 加载失败：{e}")
            self.rcon = None
    
    def send_command(self, command):
        if self.rcon is None and self.server.is_rcon_running():
            self.connect()
        
        if not self.server.is_rcon_running():
            self.server.logger.warning(f"Rcon 未开启")
            return 
        elif self.rcon is None:
            self.server.logger.warning(f"Rcon 连接失败")
            return 

        return self.rcon.send_command(command)

    def __bool__(self):
        if self.rcon is None and self.server.is_rcon_running():
            self.connect()
        return self.rcon is not None