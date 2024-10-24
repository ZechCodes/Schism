from abc import ABC, abstractmethod
from functools import partial
from typing import Type, TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    from schism.services import Service


class RemoteError(Exception):
    """RemoteError is used to wrap a stacktrace passed from a service to a client. This error type is never raised on
    its own, instead it is given as the cause for an exception that is raised by the client to propagate an error that
    occurred on the server."""


class MethodCallPayload(TypedDict):
    service: "Type[Service]"
    method: str
    args: tuple
    kwargs: dict


class ReturnPayload(TypedDict):
    result: Any


class ExceptionPayload(TypedDict):
    error: Exception
    traceback: list[str]


type ResultPayload = ReturnPayload | ExceptionPayload


class BridgeClient(ABC):
    """Bridge clients are facades for service types. These client facades are injected in place of the services when
    using the DistributedController.

    It is important that bridge clients raise exceptions raised on the service server so that they can be properly
    propagated and handled by the client code."""
    def __init__(self, config: Any):
        self.config = config

    @abstractmethod
    async def call_async_method(self, payload: MethodCallPayload) -> ResultPayload:
        ...


class BridgeServer(ABC):
    """Bridge servers provide a publicly accessible API for calling a service type.

    It is important that bridge servers capture exceptions raised while calling the service and pass them to the client
    so that they can be properly propagated and handled by the client code."""
    def __init__(self, config: Any):
        self.config = config

    @abstractmethod
    async def launch(self):
        ...


class BaseBridge(ABC):
    """Bridges provide methods for creating the corresponding configs, clients, and servers."""
    @classmethod
    @abstractmethod
    def create_client(cls, config: Any) -> BridgeClient:
        ...

    @classmethod
    @abstractmethod
    def create_server(cls, config: Any) -> BridgeServer:
        ...

    @classmethod
    def config_factory(cls, bridge_config: Any) -> Any:
        return bridge_config


class BridgeClientFacade:
    def __init__(self, bridge_type: Type[BaseBridge], service_type: "Type[Service]", config: Any):
        self.client = bridge_type.create_client(config)
        self.service_type = service_type

    def __getattr__(self, item):
        return partial(self._call, item)

    def _call(self, method: str, *args, **kwargs):
        return self.client.call_async_method(
            MethodCallPayload(
                service=self.service_type,
                method=method,
                args=args,
                kwargs=kwargs,
            )
        )
