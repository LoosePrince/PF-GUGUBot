# -*- coding: utf-8 -*-
"""RCON 管理器模块。

提供统一的命令执行接口，支持 RCON 和降级策略。
"""

from mcdreforged.api.types import PluginServerInterface


class RconManager:
    """RCON 管理器。

    提供统一的命令执行接口，自动根据 RCON 状态选择执行方式。
    
    Attributes
    ----------
    server : PluginServerInterface
        MCDR 服务器接口实例
    """

    def __init__(self, server: PluginServerInterface) -> None:
        """初始化 RCON 管理器。

        Parameters
        ----------
        server : PluginServerInterface
            MCDR 服务器接口实例
        """
        self.server = server

    def execute(self, command: str, use_mcdr_command: bool = False) -> str:
        """执行命令并返回结果。

        Parameters
        ----------
        command : str
            要执行的命令
        use_mcdr_command : bool, optional
            是否强制使用 MCDR 命令执行方式，默认为 False

        Returns
        -------
        str
            命令执行结果。RCON 模式下返回实际结果，非 RCON 模式返回"指令已执行"
        """
        # 如果强制使用 MCDR 命令执行方式
        if use_mcdr_command:
            self.server.execute_command(command)
            return "指令已执行"
        
        # 如果 RCON 可用，使用 RCON 查询
        if self.server.is_rcon_running():
            try:
                result = self.server.rcon_query(command)
                return result if result else ""
            except Exception as e:
                self.server.logger.error(f"[RconManager] RCON 查询失败: {e}")
                # RCON 查询失败时降级到普通执行方式
                return self._execute_fallback(command)
        
        # RCON 不可用，使用降级策略
        return self._execute_fallback(command)
    
    def _execute_fallback(self, command: str) -> str:
        """降级执行策略：RCON 不可用时的执行方式。

        Parameters
        ----------
        command : str
            要执行的命令

        Returns
        -------
        str
            返回"指令已执行"提示信息
        """
        # 检查是否为 MCDR 指令（通常以 !! 开头）
        if command.strip().startswith("!!"):
            self.server.execute_command(command)
        else:
            # 普通服务器指令
            self.server.execute(command)
        
        return "指令已执行"

