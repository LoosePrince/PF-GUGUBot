import logging

from typing import TYPE_CHECKING, List, Optional

from gugubot.builder import MessageBuilder
from gugubot.config.BotConfig import BotConfig
from gugubot.utils.types import BoardcastInfo, ProcessedInfo

if TYPE_CHECKING:
    from gugubot.logic.system.system_manager import SystemManager
    

class BasicSystem:
    """基础系统类，所有系统都应该继承此类。

    提供系统的基本功能和接口。

    Attributes
    ----------
    name : str
        系统名称
    system_manager : SystemManager
        系统管理器的引用
    logger : logging.Logger
        日志记录器实例
    """

    def __init__(self, name: str, enable: bool = True, config: Optional[BotConfig] = None) -> None:
        """初始化基础系统。

        Parameters
        ----------
        name : str
            系统名称
        enable : bool
            默认启用状态，如果config中有配置则使用config的值
        config : Optional[BotConfig]
            配置对象，用于读取enable状态
        """
        self.name = name
        self.system_manager: Optional[SystemManager] = None
        self.logger: Optional[logging.Logger] = None
        self.config: Optional[BotConfig] = config
        
        # 从配置读取enable状态，如果没有配置则使用传入的enable参数
        if config:
            self.enable = config.get_keys(["system", name, "enable"], enable)
        else:
            self.enable = enable

    def initialize(self) -> None:
        """初始化系统。

        在系统被注册到系统管理器时调用。
        子类应该重写此方法以实现自己的初始化逻辑。
        """
        pass

    async def process_boardcast_info(self, boardcast_info: BoardcastInfo) -> bool:
        """处理接收到的命令。

        Parameters
        ----------
        boardcast_info : BoardcastInfo
            命令信息

        Returns
        -------
        bool
            命令是否成功处理

        子类必须重写此方法以实现命令处理逻辑。
        """
        raise NotImplementedError("子类必须实现process_boardcast_info方法")

    def is_command(self, boardcast_info: BoardcastInfo) -> bool:
        """判断是否是命令
        
        Parameters
        ----------
        boardcast_info : BoardcastInfo
            广播信息

        Returns
        -------
        bool
            是否是命令
        """
        message = boardcast_info.message
        if not message:
            return False
        
        first_message = message[0]
        if first_message.get("type") != "text":
            return False
        
        content = first_message.get("data",{}).get("text", "")
        command_prefix = self.config.get("GUGUBot", {}).get("command_prefix", "#")

        if not content.startswith(command_prefix):
            return False

        group_admin = self.config.get_keys(["command", "group_admin"], False)
        if group_admin and not boardcast_info.is_admin:
            return False

        return True

    @staticmethod
    def create_processed_info(boardcast_info: BoardcastInfo) -> ProcessedInfo:
        """创建用于转发的处理后消息对象。

        Parameters
        ----------
        boardcast_info : BoardcastInfo
            原始广播信息

        Returns
        -------
        ProcessedInfo
            处理后的消息对象
        """
        # 构造转发消息的格式

        return ProcessedInfo(
            processed_message=boardcast_info.message,
            source=boardcast_info.source,
            source_id=boardcast_info.source_id,
            sender=boardcast_info.sender,
            sender_id=boardcast_info.sender_id,
            raw=boardcast_info.raw,
            server=boardcast_info.server,
            logger=boardcast_info.logger
        )

    async def reply(self, boardcast_info: BoardcastInfo, message: List[dict]) -> None:
        # 构造基础 target
        target = {boardcast_info.source: boardcast_info.event_sub_type}
        
        # 检查是否是 bridge 回复（receiver_source 是 Bridge，但 source 不是 Bridge）
        bridge_name = self.config.get_keys(
            ["connector", "minecraft_bridge", "source_name"],
            "Bridge"
        )
        
        if boardcast_info.receiver_source == bridge_name and boardcast_info.source != bridge_name:
            # 如果 receiver_source 是 Bridge，但 source 不是 Bridge, 则将 target 设置为 source
            target[boardcast_info.receiver_source] = boardcast_info.event_sub_type

        respond = ProcessedInfo(
            processed_message=message,
            source=boardcast_info.source,
            source_id=boardcast_info.source_id,
            sender=self.system_manager.server.tr("gugubot.bot_name"),
            sender_id=None,
            raw=boardcast_info.raw,
            server=boardcast_info.server,
            logger=boardcast_info.logger,
            target=target
        )

        receiver_source = boardcast_info.receiver_source if boardcast_info.receiver_source else boardcast_info.source
        await self.system_manager.connector_manager.broadcast_processed_info(
            respond,
            include=[receiver_source]
        )

    def get_tr(self, key: str, global_key: bool = False, **kwargs) -> str:
        server = self.system_manager.server
        full_key = key if global_key else f"gugubot.system.{self.name}.{key}"
        
        # 优先从风格管理器获取翻译
        if getattr(self.system_manager, 'style_manager', None):
            custom_translation = self.system_manager.style_manager.get_translation(full_key, **kwargs)
            if custom_translation is not None:
                return custom_translation
        
        # 回退到默认翻译
        return server.tr(full_key, **kwargs)

    async def handle_enable_disable(self, boardcast_info: BoardcastInfo) -> bool:
        """处理开启/关闭命令
        
        Parameters
        ----------
        boardcast_info : BoardcastInfo
            广播信息
            
        Returns
        -------
        bool
            是否处理了命令
        """
        if not self.is_command(boardcast_info):
            return False
            
        if not boardcast_info.is_admin:
            return False
            
        command = boardcast_info.message[0].get("data", {}).get("text", "")
        command_prefix = self.config.get("GUGUBot", {}).get("command_prefix", "#")
        system_name = self.get_tr("name")
        
        command = command.replace(command_prefix, "", 1).strip()
        
        if not command.startswith(system_name):
            return False
        
        command = command.replace(system_name, "", 1).strip()
        
        enable_cmd = self.get_tr("gugubot.enable", global_key=True)
        disable_cmd = self.get_tr("gugubot.disable", global_key=True)
        
        if command in [enable_cmd, disable_cmd]:
            return await self._handle_switch(command == enable_cmd, boardcast_info)
        
        return False

    async def _handle_switch(self, enable: bool, boardcast_info: BoardcastInfo) -> bool:
        """处理开启系统命令"""
        self.enable = enable
        self._save_enable_state()
        await self.reply(boardcast_info, [MessageBuilder.text(self.get_tr(f"gugubot.enable_success" if enable else "gugubot.disable_success", global_key=True))])
        return True

    def _save_enable_state(self) -> None:
        """保存enable状态到配置文件"""
        if self.config:
            system_config = self.config.get("system", {})
            if self.name in system_config:
                system_config[self.name]["enable"] = self.enable
                self.config.save()
        
        
