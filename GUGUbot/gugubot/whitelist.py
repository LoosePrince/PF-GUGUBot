from mcdreforged.api.types import PluginServerInterface

class whitelist(object):
    def __init__(self, server:PluginServerInterface):
        self.__api = server.get_plugin_instance('whitelist_api')

    def add(self, game_id:str):
        whitelist = self.__api.get_whitelist_names()

        if game_id not in whitelist:
            self.__api.add_online_player(game_id)
            # Refresh whitelist to check if added to whitelist
            whitelist = self.__api.get_whitelist_names()

            if game_id not in whitelist:
                self.__api.add_offline_player(game_id)

    def remove(self, game_id:str):
        whitelist = self.__api.get_whitelist_names()

        if game_id in whitelist:
            self.__api.remove_player(game_id, force_offline=True)

    def enable(self):
        self.__api.enable_whitelist()

    def disable(self):
        self.__api.disable_whitelist()

    def __contain__(self, uuid):
        whitelist = self.__api.get_whitelist_uuids()
        return uuid in whitelist
    
    def __getitem__(self, uuid):
        for player in self.__api.get_whitelist():
            player_uuid, player_name = player.uuid, player.name
            if uuid == player_uuid:
                return player_name
        return None
    
    def keys(self):
        return self.__api.get_whitelist_uuids()

    def values(self):
        return self.__api.get_whitelist_names()

    def items(self):
        for player in self.__api.get_whitelist():
            yield player.uuid, player.name