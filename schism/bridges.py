import traceback
from abc import ABC, abstractmethod
from functools import partial
from typing import Type, TYPE_CHECKING, Any, TypedDict

from bevy import get_repository

import schism.middleware as middleware

if TYPE_CHECKING:
    from schism.services import Service


class ResponseBuilder:
    """A helper context that captures all exceptions that are raised on the server while attempting to respond to a
    client request.

    In a standard single process application, errors raised by a method are handled by the caller. So it is necessary to
    capture all exceptions raised by a service and propagate them to the client so that the calling code can handle
    those exceptions as normal."""
    def __init__(self):
        self.payload: ResultPayload = ReturnPayload(result=None)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.payload = ExceptionPayload(
                error=exc_val,
                traceback=traceback.format_exception(exc_type, exc_val, exc_tb),
            )

        return True

    def set(self, data):
        """Set the response payload. This payload is overwritten by any exceptions that are raised."""
        self.payload = ReturnPayload(result=data)


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
    def __init__(self, config: Any, middleware_stack: "middleware.MiddlewareStackBuilder"):
        self.config = config
        self.middleware = middleware_stack

    @abstractmethod
    async def call_async_method(self, payload: MethodCallPayload) -> ResultPayload:
        ...


class BridgeServer(ABC):
    """Bridge servers provide a publicly accessible API for calling a service type.

    It is important that bridge servers capture exceptions raised while calling the service and pass them to the client
    so that they can be properly propagated and handled by the client code."""
    def __init__(self, config: Any, middleware_stack: "middleware.MiddlewareStackBuilder"):
        self.config = config
        self.middleware = middleware_stack

    @abstractmethod
    async def launch(self):
        ...

    async def call_service(self, payload: MethodCallPayload) -> ResultPayload:
        middleware_stack = self.middleware.get_middleware(
            middleware.FilterEvent.SERVER_CALL, middleware.FilterEvent.SERVER_RESULT
        )
        with ResponseBuilder() as result:
            filtered_payload = await middleware_stack.filter(middleware.FilterEvent.SERVER_CALL, payload)

            service = get_repository().get(filtered_payload["service"])
            method = getattr(service, filtered_payload["method"])
            return_value = await method(*filtered_payload["args"], **filtered_payload["kwargs"])

            filtered_return = await middleware_stack.filter(middleware.FilterEvent.SERVER_RESULT, return_value)

            result.set(filtered_return)

        return result.payload


class BaseBridge(ABC):
    """Bridges provide methods for creating the corresponding configs, clients, and servers."""
    @classmethod
    @abstractmethod
    def create_client(cls, config: Any, middleware_stack: "middleware.MiddlewareStackBuilder") -> BridgeClient:
        ...

    @classmethod
    @abstractmethod
    def create_server(cls, config: Any, middleware_stack: "middleware.MiddlewareStackBuilder") -> BridgeServer:
        ...

    @classmethod
    def config_factory(cls, bridge_config: Any) -> Any:
        return bridge_config


class BridgeClientFacade:
    def __init__(
        self,
        bridge_type: Type[BaseBridge],
        service_type: "Type[Service]",
        config: Any,
        middleware_stack: "middleware.MiddlewareStackBuilder"
    ):
        self.client = bridge_type.create_client(config, middleware_stack)
        self.service_type = service_type
        self.middleware = middleware_stack

    def __getattr__(self, item):
        return partial(self._call, item)

    async def _call(self, method: str, *args, **kwargs):
        middleware_stack = self.middleware.get_middleware(
            middleware.FilterEvent.CLIENT_CALL, middleware.FilterEvent.CLIENT_RESULT
        )

        payload = MethodCallPayload(
            service=self.service_type,
            method=method,
            args=args,
            kwargs=kwargs,
        )
        filtered_payload = await middleware_stack.filter(middleware.FilterEvent.CLIENT_CALL, payload)
        result = await self.client.call_async_method(filtered_payload)
        filtered_result = await middleware_stack.filter(middleware.FilterEvent.CLIENT_RESULT, result)
        return await self._process_result(filtered_result)

    async def _process_result(self, result: ResultPayload):
        match result:
            case {"error": error, "traceback": traceback}:
                raise error from RemoteError(
                    f"\n"
                    f"{''.join(traceback)}\n"
                    f"---------------------------------------------\n"
                    f"The above stacktrace is from a remote service\n"
                    f"---------------------------------------------"
                )

            case {"result": result}:
                return result

            case payload:
                raise RuntimeError(f"Impossible State, server response must be malformed: {payload!r}")
