from dataclasses import dataclass
from schism.bridges import BridgeClientProtocol, BridgeHostProtocol
from typing import Any, Awaitable, Callable, Protocol, Type, runtime_checkable


@runtime_checkable
class ServiceProtocol(Protocol):
    async def launch(self):
        ...


@dataclass
class Service:
    name: str
    type: Type[ServiceProtocol]
    entry_point: Callable[[], Awaitable]
    bridge_client: BridgeClientProtocol
    bridge_client_config: dict[str, Any]
    bridge_host: BridgeHostProtocol
    bridge_host_config: dict[str, Any]
