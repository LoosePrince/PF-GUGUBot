# -*- coding: utf-8 -*-
import json
import random
import re
import time

from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

import asyncio

from mcdreforged.api.types import PluginServerInterface

from gugubot.system.base_system import base_system
from gugubot.system.whitelist_system import whitelist
from gugubot.data.text import bound_help
from gugubot.utils.style import get_style_template
from gugubot.utils.message import construct_CQ_at
from gugubot.utils.utils import is_robot

class bound_system(base_system):
    def __init__(self, 
                 path: str, 
                 server:PluginServerInterface,
                 bot_config,
                 whitelist:whitelist):
        super().__init__(path, server, bot_config, 
                         admin_help_msg=bound_help, 
                         system_name="bound",
                         alias=["绑定"])
        self.whitelist = whitelist
        self.__empty_double_check = None

    def get_func(self, admin:bool=False):
        """ Return allowed function """
        function_list = [
            self.add_group,
        ]

        if self.bot_config.get("member_can_unbound", False):
            function_list = [self.remove_group] + function_list
        if not admin:
            return function_list

        return [
                self.help,
                self.add_whitelist_switch,
                self.add,
                self.remove,
                self.search,
                self.sync_whitelist,
                self.show_list,
                self.reload,
                self.clean,
                self.check_bound_sync,
                self.remove_unbound_members,
                self.check_inactive_player_sync,
                self.remove_inactive_members,
                self.check_whitelist,
                self.remove_unbound_whitelist,
                self.remove_quit_member,
            ] + function_list

    def get_qq_id(self, player_name:str):
        """Find corresponding player qq_id

        Args:
            player_name (str): player name

        Returns:
            str/None: player qq_id/None (not found)
        """
        for qq_id, name in self.items():
            if player_name in name:
                return qq_id
            
    def add_whitelist_switch(self, parameter, info, bot, reply_style, admin:bool)->bool:
        """Turn on the bound with whitelist

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        Output:
            break_signal (bool, None)
        """
        # command: boundwhitelist on
        if parameter[0] not in ["whitelist", "白名单"]:
            return True
        
        on = ["on", "开"]
        off = ["off", "关"]
        if parameter[1] not in on + off:
            bot.reply(info, get_style_template('lack_parameter', reply_style))
            return 
        
        self.bot_config["whitelist_add_with_bound"] = parameter[1] in on


    def add_group(self, parameter, info, bot, reply_style, admin:bool)->bool:
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
        # command: bound <player_name>
        if len(parameter) > 1: # pass to add
            return True

        if len(parameter) < 1: # lack of parameters                                                     
            bot.reply(info, get_style_template('lack_parameter', reply_style))
            return 
        
        if not re.match(self.bot_config.get("player_name_pattern", "^[a-zA-Z0-9_]{3,16}$"), parameter[0]):
            bot.reply(info, get_style_template('invalid_player_name', reply_style))
            return

        qq_id, player_name = str(info.user_id), parameter[0]
        if len(self.data.get(qq_id, [])) >= self.bot_config.get("max_bound", 2): # maximum reaches
            bot.reply(info, '绑定数量已达上限')
            return 
        
        elif self.get_qq_id(player_name): # name exists
            bot.reply(info, '该名称已被绑定')
            return

        # Add bound
        if qq_id not in self:
            self.data[qq_id] = []
        self.data[qq_id].append(player_name)
        self.data.save()
        bot.reply(info, f'[CQ:at,qq={qq_id}] {get_style_template("bound_success", reply_style)}')

        if len(self.data[qq_id]) == 1: # change name when first bound
            bot.set_group_card(info.source_id, qq_id, player_name)

        # Add whitelist
        if self.bot_config.get("whitelist_add_with_bound", False):
            self.whitelist.add_player(player_name)
            bot.reply(info, f'[CQ:at,qq={qq_id}] {get_style_template("bound_add_whitelist", reply_style)}')

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
        # command: bound <qq_id> <player_name>
        if not admin: # disallow groupmember to use it
            return True
        
        if not parameter[0].isdigit() and not parameter[0].startswith("[@"):
            return True

        if len(parameter) < 2: # lack of parameters                                                     
            bot.reply(info, get_style_template('lack_parameter', reply_style))
            return 

        qq_id, player_name = parameter[0], parameter[1]
        match = re.match(r'\[@(\d+).*?\]\s+(\w+)', f"{qq_id} {player_name}")
        if qq_id.startswith("[@") and match: 
            qq_id = match.group(1)
            player_name = match.group(2)

        player_name_pattern = self.bot_config.get("player_name_pattern", "^[a-zA-Z0-9_]{3,16}$")
        if not re.match(player_name_pattern, player_name):
            bot.reply(info, get_style_template('invalid_player_name', reply_style))
            return

        if len(self.data.get(qq_id, [])) >= self.bot_config.get("max_bound", 2): # maximum reaches
            bot.reply(info, '绑定数量已达上限')
            return 
        
        elif self.get_qq_id(player_name): # name exists
            bot.reply(info, '该名称已被绑定')
            return  

        # Add bound
        if qq_id not in self:
            self.data[qq_id] = []
        self.data[qq_id].append(player_name)
        self.data.save()
        bot.reply(info, '已成功绑定')
        # Add whitelist
        if self.bot_config.get("whitelist_add_with_bound", False):
            self.whitelist.add_player(player_name)
            bot.reply(info, f'已将 {player_name} 添加到白名单中')

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
        # command: del <player_name/qq_id>
        if parameter[0] not in ["解绑", "unbound"]:
            return True
        
        if len(parameter) < 2: # lack parameter                             
            # bot.reply(info, get_style_template('lack_parameter', reply_style))
            return True
        
        word = parameter[1]
        qq_id = self.get_qq_id(word)
        if word not in self and not qq_id: # not exists
            bot.reply(info, f'{word} 未绑定')
            return

        if word in self: # word is qq_id
            for player_name in self.data[word]: # remove all bound
                if self.__remove_whitelist(player_name): # remove from whitelist if exists
                    bot.reply(info, f'已将 {player_name} 从白名单中移除')

            del self.data[word]                  
        else: # word is player_name -> qq_id will be not None value
            self.data[qq_id].remove(word)

            self.__remove_whitelist(word) # remove from whitelist if exists

            if not self.data[qq_id]: # remove if empty
                del self.data[qq_id]
        self.data.save()
        bot.reply(info, f'已解除 {word} 绑定的ID')

    def remove_group(self, parameter, info, bot, reply_style, admin):
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
        if len(parameter) >= 2: # pass to remove
            return True

        # command: del <player_name/qq_id>
        if parameter[0] not in ["解绑", "unbound"]:
            return True
        
        qq_id = str(info.user_id)
        
        if qq_id not in self: # not exists
            bot.reply(info, f'{construct_CQ_at(qq_id)} 你还没有绑定任何账号')
            return
        
        for player_name in self.data[qq_id]: # remove all bound
            if self.__remove_whitelist(player_name): # remove from whitelist if exists
                bot.reply(info, f'已将 {player_name} 从白名单中移除')

        del self.data[qq_id]  # remove all bound
        self.data.save()

        bot.reply(info, f'已解除 {qq_id} 绑定的ID')

    def search(self, parameter, info, bot, reply_style, admin):
        """Search the bound record

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        """
        # command: search <player_name/qq_id>
        if parameter[0] not in ['查询','search']:
            return True

        if len(parameter) < 2: # lack parameter                             
            bot.reply(info, get_style_template('lack_parameter', reply_style))
            return
        
        word = parameter[1]
        qq_id = self.get_qq_id(word) if word not in self else word
        if qq_id:
            name = self.data[word]
            bot.reply(info, f'绑定信息:{qq_id} {name}')
            return

        bot.reply(info, f'{word} 未绑定')


    def sync_whitelist(self, parameter, info, bot, reply_style, admin):
        """Search the bound record

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        """
        # command: sync_whitelist
        if parameter[0] not in ['白名单同步','sync_whitelist']:
            return True

        for game_names in self.values():
            for game_name in game_names:
                self.whitelist.add_player(game_name)
        
        bot.reply(info, "白名单同步完成！")
    

    def show_list(self, parameter, info, bot, reply_style, admin):
        """List the word stored

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

        if len(self.data) == 0: # not word                            
            bot.reply(info, '还没有人绑定')
            return         
           
        # Response                                                          
        bound_list = [f'{qqid} - {", ".join(name)}' for qqid, name in self.items()]
        reply_msg = "\n".join(f'{i + 1}. {name}' for i, name in enumerate(bound_list))
        bot.reply(info, reply_msg)

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

        self.data.load()
        bot.reply(info, get_style_template('reload_success', reply_style))

    def clean(self, parameter, info, bot, reply_style, admin):
        """Clean the bound and whitelist

        Args:
            parameter (list[str]): command parameters
            info: message info 
            bot: qqbot
            reply_style (str): reply template style
            admin (bool): Admin mode
        """
        if parameter[0] not in ["清空", "clean"]:
            return True
        
        if self.__empty_double_check == None:
            self.__empty_double_check = str(random.randint(100000, 999999))
            bot.reply(info, 
                        f'请输入 {self.bot_config["command_prefix"]}绑定 清空 {self.__empty_double_check} 来清空')
        elif len(parameter) >= 2 and self.__empty_double_check == parameter[1]:
            self.data.data = {}
            self.data.save() # 清空绑定

            for player_name in self.whitelist.values():
                self.whitelist.remove_player(player_name)

            bot.reply(info, '已成功清除')
            self.__empty_double_check = None

    def handle_bound_notice(self, info, bot)->bool:
        command_prefix = self.bot_config["command_prefix"]
        if self.bot_config.get('bound_notice', True) \
            and str(info.user_id) not in self \
            and not is_robot(bot, info.source_id, info.user_id):
            if bot.can_send_image_sync(): # check if can send message
                bot.reply(info, f'[CQ:at,qq={info.user_id}][CQ:image,file={Path(self.bot_config["dict_address"]["bound_image_path"]).resolve().as_uri()}]')
            else:
                bot.reply(info, f'[CQ:at,qq={info.user_id}] 请使用  {command_prefix}绑定 玩家名称  来绑定~')
            return True
        return False
    
    def __remove_whitelist(self, player_name:str):
        """Remove player from whitelist

        Args:
            player_name (str): player name
        """
        if self.bot_config.get("whitelist_add_with_bound", False):
            return self.whitelist.remove_player(player_name)

    ########################################################### unbound check ###########################################################

    async def __get_self_and_admin_ids(self, bot):
        # bot's qq_id
        self_qq_id = (await bot.get_login_info()).get('data', {}).get('user_id', None)
        # bot's admin's qq ids
        admin_qq_ids = self.bot_config.get("admin_id", [])
        # admin group's qq ids
        admin_group_qq_ids = []
        for group_id in self.bot_config.get("admin_group_id", []):
            group_info = await bot.get_group_member_list(group_id)
            if group_info and group_info.get('data', {}):
                admin_group_qq_ids.extend(
                    [i['user_id'] for i in group_info['data']]
                )

        group_admin_qq_ids = []
        for group_id in self.bot_config.get("group_id", []):
            group_info = await bot.get_group_member_list(group_id)
            if group_info and group_info.get('data', {}):
                group_admin_qq_ids.extend(
                    [i['user_id'] for i in group_info['data'] if i['role'] != 'member']
                )

        # filter out admin qq_ids and self_qq_id
        filtered_ids = set(admin_qq_ids + admin_group_qq_ids + [self_qq_id] + group_admin_qq_ids)
        filtered_ids = {str(i) for i in filtered_ids}

        return filtered_ids

    async def __get_unbound_members(self, bot):
        """Get unbound members in the group

        Args:
            group_id (str): group id

        Returns:
            list[dict]: unbound members
        """
        result = []

        # filter out admin qq_ids and self_qq_id
        filtered_ids = await self.__get_self_and_admin_ids(bot)

        for group_id in self.bot_config.get("group_id", []):
            
            group_member_list = await bot.get_group_member_list(group_id)
            if not group_member_list:
                continue

            group_member_list = group_member_list.get('data', [])

            result.append( (group_id, [i
                                       for i in group_member_list 
                                       if str(i['user_id']) not in self.data \
                                        and str(i['user_id']) not in filtered_ids \
                                        and time.time() - i['join_time'] > self.bot_config.get("unbound_member_time_limit", -1) * 3600 # 2 hours
                                    ]) )

        return result

    async def check_bound(self, parameter, info, bot, reply_style, admin:bool):
        """Check if there are group members didn't bound with any account"""
        # command: bound_check
        if parameter[0] not in ['绑定检查', "检查绑定", 'bound_check']:
            return True

        def __get_name(member:dict)->str:
            """Get player name from member info"""
            return member.get('card') or member.get('nickname', '')

        # update last check time
        self.bot_config["unbound_check_last_time"] = time.time()
        self.bot_config.save()

        result = await self.__get_unbound_members(bot)
        notice_option = self.bot_config.get("unbound_notice_option", []) # group, admin, admin_group
        # construct reply message
        # print([i[1] for i in result])

        response_msg = [
            '✅ 绑定情况核查完毕，暂无未绑定成员。',
            '定期检测：全部成员已完成绑定，状态良好。',
            '绑定审核通过，无遗漏人员~',
            '所有用户已绑定，无需额外操作~',
            '🔍 绑定检查完成：未发现未绑定账号。',
            '本轮绑定检查无异常，大家都很配合 👍',
            '例行绑定检查中：暂无未绑定记录。',
            '绑定状态良好，当前无未完成用户。',
            '✔️ 已确认，全员账号状态正常、已绑定。',
            '检查完毕：没有发现任何未绑定的成员~',
        ]

        if not any([i[1] for i in result]):
            if 'admin' in notice_option:
                for user_id in self.bot_config.get("admin_id", []):
                    bot.send_private_msg(user_id, random.choice(response_msg))

            if 'admin_group' in notice_option:
                for admin_group_id in self.bot_config.get("admin_group_id", []):
                    bot.send_group_msg(admin_group_id, random.choice(response_msg))
        else:
            reply_msg = []
            for group_id, members in result:
                if members:
                    reply_msg.append(f'群{group_id}:\n' + "\n".join(
                        [f'  {__get_name(i)}({i["user_id"]}) 未绑定' 
                        for i in sorted(members, key=lambda x: x['user_id'])]
                    ))
        
            if 'admin' in notice_option:
                for user_id in self.bot_config.get("admin_id", []):
                    bot.send_private_msg(user_id, "未绑定定期检查:\n"+"\n".join(reply_msg))
                    bot.send_private_msg(user_id, f"使用 {self.bot_config['command_prefix']}绑定 移除未绑定 来移除未绑定成员~")

            if 'admin_group' in notice_option:
                for admin_group_id in self.bot_config.get("admin_group_id", []):
                    bot.send_group_msg(admin_group_id, "未绑定定期检查:\n"+"\n".join(reply_msg))
                    bot.send_group_msg(admin_group_id, f"使用 {self.bot_config['command_prefix']}绑定 移除未绑定 来移除未绑定成员~")

            if 'group' in notice_option:
                reply_msg = []
                for group_id, members in result:
                    if members:
                        reply_msg.append(f'群{group_id}:\n' + "\n".join(
                            [f'  {__get_name(i)}({construct_CQ_at(str(i["user_id"]))}) 未绑定' 
                            for i in sorted(members, key=lambda x: x['user_id'])]
                        ))

                for group_id in self.bot_config.get("group_id", []):
                    bot.send_group_msg(group_id, "未绑定定期检查:\n"+"\n".join(reply_msg))

            reply_msg = []
            count = 0
            remove_time_limit = self.bot_config.get("unbound_member_tick_limit", -1)
            if remove_time_limit >= 0:
                for group_id, members in result:
                    for member in members:
                        time_left = int(remove_time_limit - (time.time() - member['join_time'])/3600)
                        if time_left <= 0:
                            bot.set_group_kick(group_id, member['user_id'])
                            reply_msg.append(f'已将 {__get_name(member)}({member["user_id"]}) 移除出群')
                            count += 1
                        elif self.bot_config.get("unbound_member_notice", False):
                            bot.send_private_msg(member['user_id'], 
                                f'请使用 {self.bot_config["command_prefix"]}绑定 玩家名称 来绑定~\n' +\
                                f'若不绑定将会在 {time_left} 小时后被移除出群哦~',
                                group_id=group_id
                            )
                if count > 0:
                    if 'admin' in notice_option:
                        for user_id in self.bot_config.get("admin_id", []):
                            bot.send_private_msg(user_id, f'已将 {count} 名未绑定成员移除出群:\n' + "\n".join(reply_msg))
                    if 'admin_group' in notice_option:
                        for admin_group_id in self.bot_config.get("admin_group_id", []):
                            bot.send_group_msg(admin_group_id, f'已将 {count} 名未绑定成员移除出群:\n' + "\n".join(reply_msg))
                    if 'group' in notice_option:
                        for group_id in self.bot_config.get("group_id", []):
                            bot.send_group_msg(group_id, f'已将 {count} 名未绑定成员移除出群:\n' + "\n".join(reply_msg))

    def check_bound_sync(self, parameter, info, bot, reply_style, admin:bool):
        return asyncio.run(self.check_bound(parameter, info, bot, reply_style, admin))

    def remove_unbound_members(self, parameter, info, bot, reply_style, admin:bool):
        """Remove unbound members from whitelist

        Args:
            bot (PluginServerInterface): bot instance
        """
        # command: remove_unbound
        if parameter[0] not in ['移除未绑定', 'remove_unbound']:
            return True

        unbound_members = asyncio.ru(self.__get_unbound_members(bot))

        if not any([i[1] for i in unbound_members]):
            bot.reply(info, '所有人都已绑定，没有人被移除~')
            return

        def __get_name(member:dict)->str:
            """Get player name from member info"""
            return member.get('card') or member.get('nickname', '')

        count = 0
        reply_detail = []
        for group_id, members in unbound_members:
            for member in members:
                bot.set_group_kick(group_id, member['user_id'])
                count += 1
            if members:
                reply_detail.append(f'群{group_id}:\n' + "\n".join([f'  {__get_name(i)}({i["user_id"]})' for i in members]))
        bot.reply(info, f'已将未绑定的成员({count}人)移除出群:\n' + "\n".join(reply_detail))
            
    ########################################################### inactive check ###########################################################

    async def __get_inactive_player(self, bot)->dict:
        """Check if there are group members didn't bound with any account"""

        # fetch player's last update time
        result = {}
        inactive_day_limit = self.bot_config.get("inactive_player_time_range", 30)
        player_data_folder = Path(self.server.get_mcdr_config()['working_directory']) / "world" / "playerdata"

        if not player_data_folder.exists():
            result = {}
    
        for uuid, whitelist_name in self.whitelist.items():
            if (player_data_path := (player_data_folder / f"{uuid}.dat")).exists():
                update_time = player_data_path.stat().st_mtime
                inactive_day = (datetime.now(timezone.utc) - datetime.fromtimestamp(update_time, timezone.utc)).days

                # map player name to qq_id
                for qq_id, player_names in self.data.items():
                    if whitelist_name.lower() not in [i.lower() for i in player_names]:
                        continue
                    result[qq_id] = min(inactive_day, result.get(qq_id, float('inf')))

        # filter out admin qq_ids and self_qq_id
        self_and_admin_ids = await self.__get_self_and_admin_ids(bot)
        existing_day_dict = await self.__get_member_existing_day_in_group(bot)

        # Add identifier to differentiate qq_id from result and existing_day_dict
        merged_result = {}
        for qq_id, inactive_days in existing_day_dict.items():
            merged_result[qq_id] = {'inactive_days': inactive_days, 'source': 'existing_day_dict'}
        for qq_id, inactive_days in result.items():
            if qq_id in merged_result:
                merged_result[qq_id]['inactive_days'] = min(merged_result[qq_id]['inactive_days'], inactive_days)
                merged_result[qq_id]['source'] = 'game' if merged_result[qq_id]['inactive_days'] == inactive_days else merged_result[qq_id]['source']
            else:
                merged_result[qq_id] = {'inactive_days': inactive_days, 'source': 'game'}

        # filter out active members
        merged_result = {qq_id: data for qq_id, data in merged_result.items() if data['inactive_days'] >= inactive_day_limit}
        # filter out admin and self
        merged_result = {qq_id: data for qq_id, data in merged_result.items() if str(qq_id) not in self_and_admin_ids}

        return merged_result
    
    async def __get_member_existing_day_in_group(self, bot):
        existing_day_dict = defaultdict(int)

        for group_id in self.bot_config.get("group_id", []):
            group_member_list = await bot.get_group_member_list(group_id)
            if not group_member_list:
                continue

            group_member_list = group_member_list.get('data', [])
            for i in group_member_list:
                qq_id = str(i['user_id'])
                existing_day_dict[qq_id] = max(existing_day_dict.get(qq_id,0), i['join_time'])
        
        existing_day_dict = {k:round((time.time()-v)/3600/24) for k,v in existing_day_dict.items()}

        return existing_day_dict

    def __get_inactive_string(self, inactive_dict:dict)->str:
        inactive_days = inactive_dict['inactive_days']
        inactive_source_game = inactive_dict['source'] == "game"

        if inactive_days == float('inf'):
            inactive_str = '未登录且退群'
        elif inactive_source_game:
            inactive_str = f"{int(inactive_days)} 天"
        else:
            inactive_str = f"已进群 {int(inactive_days)} 天（未登录）"
        
        return inactive_str

    async def check_inactive_player(self, parameter, info, bot, reply_style, admin:bool):
        """Check if there are group members didn't bound with any account"""
        # command: bound_check
        if parameter[0] not in ['活跃', '活跃检查', 'active_check']:
            return True

        # update last check time
        self.bot_config["inactive_player_check_last_time"] = time.time()
        
        self.bot_config.save()

        result = await self.__get_inactive_player(bot)
        
        notice_option = self.bot_config.get("inactive_notice_option", []) # group, admin, admin_group
        # construct reply message
        # print([i[1] for i in result])
        response_msg = [
            '✅ 活跃检查完成，暂无发现不活跃成员。',
            '活跃度审核通过，当前所有玩家状态良好~',
            '定期检测中，暂无非活跃用户，继续保持！',
            '活跃状态良好，无需处理闲置玩家。',
            '🔍 扫描结束：无不活跃成员。',
            '例行检查：所有成员都在线活跃中~',
            '状态检测完成，暂无低活跃账号~',
            '无不活跃情况，群内活跃正常。',
            '活跃监测：暂无异常，继续愉快交流！',
            '✔️ 成员活跃状态正常，无需清理。',
        ]

        if not result:
            if 'admin' in notice_option:
                for user_id in self.bot_config.get("admin_id", []):
                    bot.send_private_msg(user_id, random.choice(response_msg))

            if 'admin_group' in notice_option:
                for admin_group_id in self.bot_config.get("admin_group_id", []):
                    bot.send_group_msg(admin_group_id, random.choice(response_msg))
        else:
            reply_msg = []
            for qq_id, inactive_dict in result.items():
                player_names = ",".join(self.data.get(qq_id, []))
                
                inactive_str = self.__get_inactive_string(inactive_dict)

                reply_msg.append(f'{player_names}({qq_id}) -> {inactive_str}')
            
            
            if 'admin' in notice_option:
                for user_id in self.bot_config.get("admin_id", []):
                    bot.send_private_msg(user_id, "活跃度定期检查:\n"+"\n".join(reply_msg))
                    bot.send_private_msg(user_id, f"使用 {self.bot_config['command_prefix']}绑定 移除不活跃 来移除不活跃成员~")

            if 'admin_group' in notice_option:
                for admin_group_id in self.bot_config.get("admin_group_id", []):
                    bot.send_group_msg(admin_group_id, "活跃度定期检查:\n"+"\n".join(reply_msg))
                    bot.send_group_msg(admin_group_id, f"使用 {self.bot_config['command_prefix']}绑定 移除不活跃 来移除不活跃成员~")

            if 'group' in notice_option:
                reply_msg = []
                for qq_id, inactive_dict in result.items():
                    player_names = ",".join(self.data.get(qq_id, []))

                    inactive_str = self.__get_inactive_string(inactive_dict)

                    reply_msg.append(f'{player_names}({construct_CQ_at(str(qq_id))}) -> {inactive_str}')

                for group_id in self.bot_config.get("group_id", []):
                    bot.send_group_msg(group_id, "活跃度定期检查:\n"+"\n".join(reply_msg))
            
    def check_inactive_player_sync(self, parameter, info, bot, reply_style, admin:bool):
        return asyncio.run(self.check_inactive_player(parameter, info, bot, reply_style, admin))

    def remove_inactive_members(self, parameter, info, bot, reply_style, admin:bool):
        """Remove inactive members from whitelist

        Args:
            bot (PluginServerInterface): bot instance
        """
        # command: remove_inactive
        if parameter[0] not in ['移除不活跃', 'remove_inactive']:
            return True

        inactive_members = asyncio.run(self.__get_inactive_player(bot))

        if not inactive_members:
            bot.reply(info, '没有不活跃成员~')
            return

        group_member_dict = defaultdict(set)
        for group_id in self.bot_config.get("group_id", []):
            group_member_list = bot.get_group_member_list_sync(group_id)
            if not group_member_list:
                continue

            group_member_list = group_member_list.get('data', [])
            for i in group_member_list:
                qq_id = str(i['user_id'])
                group_member_dict[qq_id].add(group_id)

        count = 0
        reply_detail = []
        # 先保存要输出的信息，避免del后访问
        for qq_id, inactive_dict in inactive_members.items():
            player_names = ",".join(self.data.get(qq_id, []))
            inactive_str = self.__get_inactive_string(inactive_dict)
            reply_detail.append(f'{player_names}({qq_id}) -> {inactive_str}')

        # 再执行删除和踢人
        for qq_id in list(inactive_members.keys()):
            for player_name in self.data.get(qq_id, []):
                self.__remove_whitelist(player_name)
            if qq_id in self.data:
                del self.data[qq_id]
        self.data.save()

        for qq_id in inactive_members.keys():
            for group_id in group_member_dict.get(qq_id, []):
                bot.set_group_kick(group_id, qq_id)
            count += 1

        bot.reply(info, f'已将不活跃的成员({count}人)移除出群:\n' + "\n".join(reply_detail))

    ############################################################## check name ##############################################################
    async def check_name(self, bot):
        """Check if there are group members didn't bound with any account"""
        for group_id in self.bot_config.get("group_id", []):
            group_member_list = await bot.get_group_member_list(group_id)
            if not group_member_list:
                continue

            group_member_list = group_member_list.get('data', [])
            for member in group_member_list:
                user_id = str(member['user_id'])
                if user_id in self and member['card'] != self[user_id][-1]:
                    # update group card
                    bot.set_group_card(group_id, member['user_id'], self[user_id][-1])

    ############################################################## check whitelist ##############################################################
    def __get_unbound_whitelist(self):
        """Get unbound members in the whitelist

        Returns:
            list[tuple]: unbound members (uuid, player_name)
        """
        result = []

        all_player_names = {i.lower() for player_names in self.values() for i in player_names}

        for uuid, whitelist_player_name in self.whitelist.items():
            if whitelist_player_name.lower() not in all_player_names:
                result.append((uuid, whitelist_player_name))

        return result
    
    def check_whitelist(self, parameter, info, bot, reply_style, admin:bool):
        """Check if there are group members didn't bound with any account"""
        # command: bound_check
        if parameter[0] not in ['白名单检查', 'whitelist_check']:
            return True

        result = self.__get_unbound_whitelist()

        if not result:
            bot.reply(info, '白名单检查: 所有玩家都已绑定~')
            return
        
        reply_msg = []
        for uuid, player_name in result:
            reply_msg.append(f'{player_name}({uuid}) 未绑定')

        bot.reply(info, "白名单检查:\n"+"\n".join(reply_msg))

    def remove_unbound_whitelist(self, parameter, info, bot, reply_style, admin:bool):
        """Remove unbound members from whitelist

        Args:
            bot (PluginServerInterface): bot instance
        """
        # command: remove_unbound_whitelist
        if parameter[0] not in ['移除未绑定白名单', 'remove_unbound_whitelist']:
            return True

        result = self.__get_unbound_whitelist()

        if not result:
            bot.reply(info, '没有未绑定的白名单成员~')
            return
        
        reply_msg = []
        for uuid, player_name in result:
            self.whitelist.remove_player(player_name)
            reply_msg.append(f'{player_name}({uuid}) 已从白名单中移除')

        bot.reply(info, "已将未绑定的白名单成员移除:\n"+"\n".join(reply_msg))

    ############################################################## check quit ##############################################################
    def __get_member_in_group(self, bot):
        member_id_list = set()

        for group_id in self.bot_config.get("group_id", []):
            group_member_list = bot.get_group_member_list_sync(group_id)
            if not group_member_list:
                continue

            group_member_list = group_member_list.get('data', [])
            for i in group_member_list:
                qq_id = str(i['user_id'])
                member_id_list.add(qq_id)
        
        return member_id_list


    def remove_quit_member(self, parameter, info, bot, reply_style, admin:bool):
        """Remove unbound members from whitelist

        Args:
            bot (PluginServerInterface): bot instance
        """
        # command: remove_unbound_whitelist
        if parameter[0] not in ['移除退群', 'remove_quit']:
            return True

        result = self.__get_member_in_group(bot)

        quit_members = {qq_id for qq_id in self.data.keys() if qq_id not in result}

        if not quit_members:
            bot.reply(info, '没有退群的绑定成员~')
            return
        
        reply_msg = []
        for qq_id in quit_members:
            for player_name in self.get(qq_id, []):
                self.__remove_whitelist(player_name)
                reply_msg.append(f'\t{player_name} 已从白名单中移除')
            del self.data[qq_id]
            self.data.save()
            reply_msg.append(f'\t{qq_id} 已解除绑定')

        bot.reply(info, "已将退群成员绑定及白名单移除:\n"+"\n".join(reply_msg))


    async def trigger_time_functions(self, bot):
        """Trigger time functions"""
        last_check_time_unbound = self.bot_config.get("unbound_check_last_time", -1)
        check_interval_unbound = self.bot_config.get("unbound_check_interval", -1) * 3600 # convert to seconds
        last_check_time_inactive = self.bot_config.get("inactive_player_check_last_time", -1)
        check_interval_inactive = self.bot_config.get("inactive_check_interval", -1) * 3600
        current_time = time.time()

        # check off
        if check_interval_unbound > 0 and (last_check_time_unbound < 0 or (current_time - last_check_time_unbound >= check_interval_unbound)):
            await self.check_bound(['绑定检查'], None, bot, None, True)
        
        if check_interval_inactive > 0 and (last_check_time_inactive < 0 or (current_time - last_check_time_inactive >= check_interval_inactive)):
            await self.check_inactive_player(['活跃'], None, bot, None, True)

        if self.bot_config.get("force_game_name", False):
            await self.check_name(bot)