from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from GUGUbot.gugubot.connector.basic_connector import BasicConnector


class ConnectorManager:
    """管理多个连接器实例的管理器。

    提供添加、移除连接器和消息广播功能。

    Attributes
    ----------
    connectors : List[BasicConnector]
        当前管理的所有连接器实例
    logger : logging.Logger
        日志记录器实例
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """初始化连接器管理器。

        Parameters
        ----------
        logger : Optional[logging.Logger]
            用于日志记录的Logger实例。如果未提供，将创建一个新的。
        """
        self.connectors: List[BasicConnector] = []
        self.logger = logger or logging.getLogger(__name__)

    async def add_connector(self, connector: BasicConnector) -> None:
        """添加一个新的连接器实例。

        Parameters
        ----------
        connector : BasicConnector
            要添加的连接器实例

        Raises
        ------
        ValueError
            如果连接器已经存在于管理器中
        """
        if connector in self.connectors:
            raise ValueError(f"连接器 {connector.source} 已经存在")

        try:
            await connector.connect()
            self.connectors.append(connector)
            self.logger.info(f"已添加并连接到连接器: {connector.source}")
        except Exception as e:
            self.logger.error(f"连接到 {connector.source} 失败: {str(e)}")
            raise

    async def remove_connector(self, connector: BasicConnector) -> None:
        """移除一个连接器实例。

        Parameters
        ----------
        connector : BasicConnector
            要移除的连接器实例

        Raises
        ------
        ValueError
            如果连接器不在管理器中
        """
        if connector not in self.connectors:
            raise ValueError(f"连接器 {connector.source} 不存在")

        try:
            await connector.disconnect()
            self.connectors.remove(connector)
            self.logger.info(f"已断开并移除连接器: {connector.source}")
        except Exception as e:
            self.logger.error(f"断开 {connector.source} 失败: {str(e)}")
            # 仍然从列表中移除，即使断开连接失败
            self.connectors.remove(connector)
            raise

    async def broadcast(self, message: Any) -> Dict[str, Exception]:
        """向所有连接器广播消息。

        Parameters
        ----------
        message : Any
            要广播的消息

        Returns
        -------
        Dict[str, Exception]
            发送失败的连接器及其对应的异常信息
        """
        failures: Dict[str, Exception] = {}
        tasks = []

        # 创建所有发送任务
        for connector in self.connectors:
            task = asyncio.create_task(
                self._safe_send(connector, message)
            )
            tasks.append((connector, task))

        # 等待所有任务完成
        for connector, task in tasks:
            try:
                await task
            except Exception as e:
                failures[connector.source] = e
                self.logger.error(f"向 {connector.source} 发送消息失败: {str(e)}")

        return failures

    async def _safe_send(self, connector: BasicConnector, message: Any) -> None:
        """安全地向单个连接器发送消息。

        Parameters
        ----------
        connector : BasicConnector
            目标连接器
        message : Any
            要发送的消息

        Raises
        ------
        Exception
            如果发送失败
        """
        try:
            await connector.send_message(message)
            self.logger.debug(f"成功发送消息到 {connector.source}")
        except Exception as e:
            self.logger.error(f"发送消息到 {connector.source} 失败: {str(e)}")
            raise

    async def disconnect_all(self) -> Dict[str, Exception]:
        """断开所有连接器的连接。

        Returns
        -------
        Dict[str, Exception]
            断开连接失败的连接器及其对应的异常信息
        """
        failures: Dict[str, Exception] = {}
        tasks = []

        # 创建所有断开连接的任务
        for connector in self.connectors[:]:  # 使用切片创建副本，因为我们会修改列表
            task = asyncio.create_task(self.remove_connector(connector))
            tasks.append((connector, task))

        # 等待所有任务完成
        for connector, task in tasks:
            try:
                await task
            except Exception as e:
                failures[connector.source] = e

        return failures
