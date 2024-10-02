from abc import ABC, abstractmethod
from typing import Type, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from schism.services import Service


class BridgeClient:
    def __init__(self, service: "Type[Service]", config: Any):
        self.service = service
        self.config = config


class BridgeServer(ABC):
    def __init__(self, service: "Type[Service]", config: Any):
        self.service = service
        self.config = config

    @abstractmethod
    async def launch(self):
        ...


class BaseBridge(ABC):
    @classmethod
    @abstractmethod
    def create_client(cls, service_type: "Type[Service]", config: Any) -> BridgeClient:
        ...

    @classmethod
    @abstractmethod
    def create_server(cls, service_type: "Type[Service]", config: Any) -> BridgeServer:
        ...

    @classmethod
    def config_factory(cls, bridge_config: Any) -> Any:
        return bridge_config