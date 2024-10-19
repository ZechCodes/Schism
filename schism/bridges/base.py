from abc import ABC, abstractmethod
from typing import Type, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from schism.services import Service


class RemoteError(Exception):
    """RemoteError is used to wrap a stacktrace passed from a service to a client. This error type is never raised on
    its own, instead it is given as the cause for an exception that is raised by the client to propagate an error that
    occurred on the server."""


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