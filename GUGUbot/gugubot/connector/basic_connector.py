from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BasicConnector(ABC):
	"""Abstract base connector class.

	Attributes
	----------
	source: str
		Identifier or description of the underlying source (for example a URL,
		websocket address, or client name). Concrete implementations should set
		this value to describe where messages come from.
	parser: Any
		Object responsible for parsing raw incoming data into internal message
		objects.
	builder: Any
		Object responsible for building outgoing messages from internal
		message objects into the raw format required by the source.

	Methods
	-------
	connect()
		Establish the underlying connection (usually asynchronous).
	disconnect()
		Tear down the connection and free resources (usually asynchronous).
	on_message(raw)
		Handle a raw incoming message (usually asynchronous).
	"""

	def __init__(self, source: str = "", parser: Any = None, builder: Any = None) -> None:
		self.source: str = source
		self.parser: Any = parser
		self.builder: Any = builder

	@abstractmethod
	async def connect(self) -> None:
		"""Establish the low-level connection. Implementations should override
		this method and perform asynchronous connection setup.
		"""
		raise NotImplementedError

	@abstractmethod
	async def disconnect(self) -> None:
		"""Tear down the low-level connection and release resources.
		"""
		raise NotImplementedError

	@abstractmethod
	async def send_message(self, message: Any) -> None:
		"""Send a message through the connector.
		
		Parameters
		----------
		message: Any
			The message to be sent. Implementations should use self.builder
			to transform the message if needed before sending.
		"""
		raise NotImplementedError

	@abstractmethod
	async def on_message(self, raw: Any) -> None:
		"""Called when a raw message is received.

		Typical responsibilities:
		- Use self.parser to convert `raw` into an internal message object.
		- Dispatch the parsed message to upper-layer handlers.

		Parameters
		----------
		raw: Any
			The raw data received from `source`.
		"""
		raise NotImplementedError
