"""Bridges are how Schism services communicate with each other in a distributed context. They are never used when the
application is running in a monolithic mode. They are made of three parts:
- Bridge class: referenced in the schism.config, used to create instances of the bridge server and bridge client
- Server class: stands in front of the service class and accepts method call requests from clients
- Client class: used in place of the service class to proxy method calls as requests to the server

The client and server should be "dumb" in that they just pass payloads of dictionaries back and forth. There should be
no evaluation of how the results are handled. The active Schism controller handles everything including determining
where exceptions should be handled.

The bridge class should provide three different class methods:
- create_client: should return an instance of the bridge client
- create_server: should return an instance of the bridge server and register any launch tasks or endpoints that are
needed to make it accessible
- config_factory: should process any settings that can be passed to the bridge from a service config in the
schism.config file, this return in passed through to the create_client and create_server methods

The client class only has to implement a single method call_async_method which should pass the method call payload to
the bridge server. It should then return the result payload that the server responds with.

The server class's implementation is much less strict. It only needs to pass the method call payload it receives to the
call_async_method method of the server instance and then pass that method's return payload back to the client.

The client and server classes are instantiated with the bridge config, the server class is also instantiated with a
service facade that method call payloads can be passed to for handling."""
import traceback
from abc import ABC, abstractmethod
from functools import partial
from typing import Awaitable, Type, TYPE_CHECKING, Any, TypedDict

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
    """Bridge clients proxy method calls from the service facade to the service server."""
    def __init__(self, config: Any):
        self.config = config

    @abstractmethod
    async def call_async_method(self, payload: MethodCallPayload) -> ResultPayload:
        """Should pass the method call payload up to the running bridge server and return the result payload it responds
        with."""
        ...


class BridgeServer:
    """Bridge servers take method call payloads and propagate them to the service itself, responding to the client with
    the result payload return from call_service."""
    def __init__(self, config: Any, service_facade: "BridgeServiceFacade"):
        self.config = config
        self.service_facade = service_facade

    def call_async_method(self, payload: MethodCallPayload) -> Awaitable[ResultPayload]:
        return self.service_facade.call_async_method(payload)



class BaseBridge(ABC):
    """Bridges provide methods for creating the corresponding configs, clients, and servers."""
    @classmethod
    @abstractmethod
    def create_client(cls, config: Any) -> BridgeClient:
        ...

    @classmethod
    @abstractmethod
    def create_server(cls, config: Any, service_facade: "BridgeServiceFacade") -> BridgeServer:
        ...

    @classmethod
    def config_factory(cls, bridge_config: Any) -> Any:
        return bridge_config


class BridgeClientFacade:
    """The client facade is injected in place of a service and passes off method calls to the bridge client. The facade
    handles propagation of exceptions from the bridge server to the client code. The facade also handles running
    middleware on the client side."""
    def __init__(
        self,
        bridge_type: Type[BaseBridge],
        service_type: "Type[Service]",
        config: Any,
        middleware_stack: "middleware.MiddlewareStackBuilder"
    ):
        self.client = bridge_type.create_client(config)
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


class BridgeServiceFacade:
    """The service facade gets the method call payload from the bridge server and handles calling the method on the
    service, capturing the return value and any exceptions to pass back to the bridge server as a result payload which
    is then sent to the client."""
    def __init__(self, service_type: "Type[Service]", middleware_stack: "middleware.MiddlewareStackBuilder"):
        self.service_type = service_type
        self.middleware = middleware_stack

    async def call_async_method(self, payload: MethodCallPayload) -> ResultPayload:
        middleware_stack = self.middleware.get_middleware(
            middleware.FilterEvent.SERVER_CALL, middleware.FilterEvent.SERVER_RESULT
        )
        with ResponseBuilder() as result:
            filtered_payload = await middleware_stack.filter(middleware.FilterEvent.SERVER_CALL, payload)

            if payload["service"] != self.service_type:
                raise RuntimeError(f"Service types do not match: {self.service_type} != {payload['service']}")

            service = get_repository().get(self.service_type)
            method = getattr(service, filtered_payload["method"])
            return_value = await method(*filtered_payload["args"], **filtered_payload["kwargs"])

            filtered_return = await middleware_stack.filter(middleware.FilterEvent.SERVER_RESULT, return_value)

            result.set(filtered_return)

        return result.payload
