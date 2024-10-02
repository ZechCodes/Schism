from abc import ABC, abstractmethod
from typing import Type, TYPE_CHECKING
from typing import Type, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from schism.services import Service


class BridgeClient:
    ...


class BridgeServer:
    ...

    @abstractmethod
    async def launch(self):
        ...


class BaseBridge(ABC):
    @classmethod
    @abstractmethod
    def create_client(cls, service_type: "Type[Service]") -> BridgeClient:
        ...

    @classmethod
    @abstractmethod
    def create_server(cls, service_type: "Type[Service]") -> BridgeServer:
        ...

    @classmethod
    def config_factory(cls, bridge_config: Any) -> Any:
        return bridge_config