from mcdreforged.api.types import PluginServerInterface

from .base_system import base_system
from ..data.text import whitelist_help
from ..utils import get_style_template

class whitelist(base_system):
    def __init__(self, 
                 server:PluginServerInterface,
                 bot_config):
        super().__init__(path=None,
                         server=server, 
                         bot_config=bot_config, 
                         admin_help_msg=whitelist_help, 
                         system_name="whitelist",
                         alias=["白名单"])
        self.__api = server.get_plugin_instance('whitelist_api')
        if bot_config["command"]["whitelist"]:
            self.__api.enable_whitelist()
        else:
            self.__api.disable_whitelist()

    def add_player(self, game_id:str)->bool:
        """Add player to whitelist

        Args:
            game_id (str): player name

        Returns:
            bool: whether success
        """
        whitelist = self.__api.get_whitelist_names()

        if game_id not in whitelist:
            self.__api.add_online_player(game_id)
            # Refresh whitelist to check if added to whitelist
            whitelist = self.__api.get_whitelist_names()

            if game_id not in whitelist:
                self.__api.add_offline_player(game_id)
            return True
        
        return False

    def remove_player(self, game_id:str)->bool:
        """Remove player from whitelist

        Args:
            game_id (str): player name

        Returns:
            bool: whether remove success
        """
        whitelist = self.__api.get_whitelist_names()

        if game_id in whitelist:
            self.__api.remove_player(game_id, force_offline=True)
            return True
        
        return False

    def enable(self, parameter, info, bot, reply_style, admin:bool)->bool:
        if_continue = super().enable(parameter, info, bot, reply_style, admin)

        if not if_continue: # is enable command
            self.__api.enable_whitelist()

        return if_continue

    def disable(self, parameter, info, bot, reply_style, admin:bool)->bool:
        if_continue = super().disable(parameter, info, bot, reply_style, admin)

        if not if_continue: # is disable command
            self.__api.disable_whitelist()

        return if_continue

    def add(self, parameter, info, bot, reply_style, admin:bool)->bool:
        """Add word into the system

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        Output:
            break_signal (bool, None)
        """
        # command: add <player_name> 
        if parameter[0] not in ['添加', 'add']:
            return True

        if len(parameter) < 2: # lack of parameters                                                     
            bot.reply(info, get_style_template('lack_parameter', reply_style))
            return 
        
        player_name = parameter[1]
        add_success = self.add_player(player_name)
        if not add_success: # player already exists
            bot.reply(info, get_style_template('add_existed', reply_style))
            return 
    
        # adding success
        bot.reply(info, get_style_template('add_success', reply_style))
        

    def remove(self, parameter, info, bot, reply_style, admin):
        """Remove word in the system

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style: reply template style
            admin (bool): Admin mode
        Output:
            break_signal (bool, None)
        """
        # command: del <player_name>
        if parameter[0] not in ['删除','移除', 'del']:
            return True
        
        if len(parameter) < 2: # lack parameter                             
            bot.reply(info, get_style_template('lack_parameter', reply_style))
            return
        
        player_name = parameter[1]
        remove_success = self.remove_player(player_name)

        if not remove_success: # player not in whitelist
            bot.reply(info, get_style_template('del_no_exist', reply_style))
            return

        # removing success                                           
        bot.reply(info, get_style_template('delete_success', reply_style))

    def change(self, parameter, info, bot, reply_style, admin):
        """Change player's whitelist name

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        """
        # command: change pre_name cur_name
        if parameter[0] not in ['修改','更改','更新','change']:
            return True
        
        if len(parameter) < 2: # lack parameter                             
            bot.reply(info, get_style_template('lack_parameter', reply_style))
            return

        pre_name, cur_name = parameter[1], parameter[2]
        if pre_name not in self.values():
            bot.reply(info, '未找到对应名字awa！')      
        else:
            self.remove_player(pre_name)
            self.add_player(cur_name)
        
            bot.reply(info,'已将 {} 改名为 {}'.format(pre_name,cur_name))

    def show_list(self, parameter, info, bot, reply_style, admin):
        """List the whitelist stored

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        Output:
            break_signal (bool, None)
        """
        # command: list
        if parameter[0] not in ['列表','list']:
            return True

        if len(self.keys()) == 0: # not word                            
            bot.reply(info, get_style_template('no_word', reply_style))
            return         
           
        # Response                                                          
        keys_string = '\n'.join(sorted(self.values()))
        reply_string = get_style_template('list', reply_style).format(keys_string)
        bot.reply(info, reply_string)

    def reload(self, parameter, info, bot, reply_style, admin):
        """Reload the data file

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        Output:
            break_signal (bool, None)
        """
        # command: reload
        if parameter[0] not in ['重载', '刷新', 'reload']:
            return True

        bot.reply(info, get_style_template('reload_success', reply_style))


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