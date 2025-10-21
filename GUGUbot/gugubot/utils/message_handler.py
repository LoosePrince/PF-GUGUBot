# -*- coding: utf-8 -*-
#+----------------------------------------------------------------------+
import re
import time
from typing import Dict, Any

from mcdreforged.api.types import Info
from gugubot.builder.basic_builder import MessageBuilder
from gugubot.builder.mc_builder import McMessageBuilder
from gugubot.builder.qq_builder import CQHandler

#+----------------------------------------------------------------------+

class MessageHandler:
    """消息处理器"""
    
    def __init__(self, bot_core):
        self.bot = bot_core
        self.server = bot_core.server
        self.config = bot_core.config
    
    def handle_qq_message(self, qq_info, bot):
        """处理QQ消息"""
        try:
            # 检查是否是机器人消息
            if self._is_bot_message(qq_info):
                return
            
            # 检查违禁词
            if self._check_ban_words(qq_info.message):
                return
            
            # 处理关键词回复
            if self._handle_keyword_reply(qq_info, bot):
                return
            
            # 转发到MC
            if self.config.get("forward", {}).get("qq_to_mc", True):
                self._forward_to_mc(qq_info, bot)
                
        except Exception as e:
            self.server.logger.error(f"处理QQ消息时出错: {e}")
    
    def handle_qq_command(self, source, command):
        """处理QQ命令"""
        try:
            # 这里可以添加QQ命令处理逻辑
            pass
        except Exception as e:
            self.server.logger.error(f"处理QQ命令时出错: {e}")
    
    def handle_qq_request(self, qq_info, bot):
        """处理QQ请求"""
        try:
            # 这里可以添加QQ请求处理逻辑
            pass
        except Exception as e:
            self.server.logger.error(f"处理QQ请求时出错: {e}")
    
    def handle_qq_notice(self, qq_info, bot):
        """处理QQ通知"""
        try:
            # 这里可以添加QQ通知处理逻辑
            pass
        except Exception as e:
            self.server.logger.error(f"处理QQ通知时出错: {e}")
    
    def handle_mc_message(self, info: Info):
        """处理MC消息"""
        try:
            # 检查是否是服务器消息
            if "[Server]" in info.content:
                return
            
            # 检查是否是玩家消息
            if not self._is_player_message(info.content):
                return
            
            # 处理游戏内关键词
            if self._handle_ingame_keyword(info):
                return
            
            # 转发到QQ
            if self.config.get("forward", {}).get("mc_to_qq", True):
                self._forward_to_qq(info)
                
        except Exception as e:
            self.server.logger.error(f"处理MC消息时出错: {e}")
    
    def _is_bot_message(self, qq_info):
        """检查是否是机器人消息"""
        # 检查是否是机器人自己的消息
        return qq_info.user_id == qq_info.self_id
    
    def _check_ban_words(self, message):
        """检查违禁词"""
        if not self.config.get("command", {}).get("ban_word", True):
            return False
        
        # 检查违禁词
        for ban_word in self.bot.ban_word.data:
            if ban_word in message:
                # 撤回消息
                # self.bot.qq_bot.delete_msg(message_id)
                return True
        
        return False
    
    def _handle_keyword_reply(self, qq_info, bot):
        """处理关键词回复"""
        if not self.config.get("command", {}).get("key_word", True):
            return False
        
        # 检查关键词
        for keyword, reply in self.bot.key_word.data.items():
            if keyword in qq_info.message:
                # 使用MessageBuilder构建回复消息
                message_array = [MessageBuilder.text(reply)]
                cq_message = CQHandler.build(message_array)
                
                # 发送回复
                if qq_info.message_type == "group":
                    bot.send_group_msg(group_id=qq_info.group_id, message=cq_message)
                else:
                    bot.send_private_msg(user_id=qq_info.user_id, message=cq_message)
                return True
        
        return False
    
    def _handle_ingame_keyword(self, info):
        """处理游戏内关键词"""
        if not self.config.get("command", {}).get("ingame_key_word", True):
            return False
        
        message = info.content
        
        # 检查关键词
        for keyword, reply in self.bot.key_word_ingame.data.items():
            if keyword in message:
                # 发送回复
                self.server.execute(f'tellraw @a {{"text":"{reply}","color":"yellow"}}')
                return True
        
        return False
    
    def _forward_to_mc(self, qq_info, bot):
        """转发消息到MC"""
        try:
            # 获取发送者信息
            sender_name = self._get_sender_name(qq_info)
            group_name = self._get_group_name(qq_info.group_id) if qq_info.message_type == "group" else "私聊"
            group_id = str(qq_info.group_id) if qq_info.message_type == "group" else None
            
            # 解析CQ消息
            message_array = CQHandler.parse(qq_info.message)
            
            # 使用McMessageBuilder构建RText消息
            rtext_message = McMessageBuilder.array_to_RText(message_array)
            
            # 构建完整的消息
            full_message = McMessageBuilder.build(
                rtext_message,
                group_name=group_name,
                group_id=group_id,
                sender=sender_name
            )
            
            # 发送到MC
            self.server.execute(f'tellraw @a {full_message.to_json_str()}')
            
        except Exception as e:
            self.server.logger.error(f"转发到MC失败: {e}")
    
    def _forward_to_qq(self, info):
        """转发消息到QQ"""
        try:
            # 解析玩家消息
            player_name, message = self._parse_player_message(info.content)
            
            if not player_name or not message:
                return
            
            # 使用MessageBuilder构建消息
            from gugubot.builder.basic_builder import MessageBuilder
            
            # 构建消息数组
            message_array = [
                MessageBuilder.text(f"[MC] {player_name}: {message}")
            ]
            
            # 转换为CQ字符串
            cq_message = CQHandler.build(message_array)
            
            # 发送到QQ群
            self.bot.send_msg_to_all_qq(cq_message)
            
        except Exception as e:
            self.server.logger.error(f"转发到QQ失败: {e}")
    
    def _is_player_message(self, content):
        """检查是否是玩家消息"""
        # 简单的玩家消息检测
        return "<" in content and ">" in content
    
    def _parse_player_message(self, content):
        """解析玩家消息"""
        try:
            # 匹配玩家消息格式: <PlayerName> message
            match = re.match(r'<([^>]+)>\s*(.*)', content)
            if match:
                return match.group(1), match.group(2)
            return None, None
        except Exception:
            return None, None
    
    def _get_sender_name(self, qq_info):
        """获取发送者名称"""
        # 从QQ信息中获取发送者名称
        return getattr(qq_info, 'sender', {}).get('nickname', f"用户{qq_info.user_id}")
    
    def _get_group_name(self, group_id):
        """获取群名称"""
        # 从配置中获取自定义群名
        custom_name = self.bot.group_name.get(str(group_id))
        if custom_name:
            return custom_name
        
        # 这里可以添加获取真实群名的逻辑
        return f"群{group_id}"
