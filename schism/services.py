from dataclasses import dataclass
from schism.bridges import BridgeClientProtocol, BridgeHostProtocol
from typing import Any, Awaitable, Callable


@dataclass
class Service:
    name: str
    entry_point: Callable[[], Awaitable]
    bridge_client: BridgeClientProtocol
    bridge_client_config: dict[str, Any]
    bridge_host: BridgeHostProtocol
    bridge_host_config: dict[str, Any]
