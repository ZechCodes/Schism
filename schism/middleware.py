"""Schism provides a middleware API that can be used to filter values going into and out of the client and server. There
are four filter events:
- client_call: Run when a call is made to a service method but before a request is made to the service server
- client_result: Run when the service server responds to a call request, right before the result is processed and passed
to the client code
- server_call: Run when the service server receives a call request, right before the service method is called
- server_result: Run when the service method returns, right before sending the response to the client

These middleware filters are only run on bridges and are never run when the application is being run in a monolithic
mode. They are solely intended to allow changes to be made to the payloads passing between services in a distributed
application.

To implement a middleware create a class inheriting from schism.middleware.Middleware and override the desired filter
methods.

    from schism.middleware import Middleware
    from schism.bridges import MethodCallPayload, ResultPayload, ReturnPayload

    class ExampleMiddleware(Middleware):
        async def filter_client_call(self, payload: MethodCallPayload) -> MethodCallPayload:
            ...

        async def filter_client_result(self, payload: ResultPayload) -> ResultPayload:
            ...

        def filter_server_call(self, payload: MethodCallPayload) -> MethodCallPayload:
            ...

        def filter_server_result(self, payload: ResultPayload) -> ResultPayload:
            ...

To apply a middleware to a bridge it must be added to the bridge config for a service in the schism.config file. Here's
an example YAML config:

    services:
      - name: example
        service: example:Example
        bridge:
          type: schism.ext.bridges.simple_tcp:SimpleTCP
          middleware:
            - example_middleware:ExampleMiddleware

It's possible to pass config settings into the middleware as keyword arguments:

    middleware:
      - type: example_middleware:ExampleMiddleware
        value: Example Value

The server and client lookup relevant middleware before running any filter events. They then instantiate the appropriate
middleware and run the necessary filters. This allows middleware instances to exist for the life span of each method
call. So a middleware with both server_call and server_result filters is instantiated before the server_call filter is
run and that same instance is used for both the server_call and server_result filter events.
"""
from enum import Enum
from typing import Awaitable, ClassVar, Type, Any

from schism.bridges import MethodCallPayload, ResultPayload, ReturnPayload


class FilterEvent(Enum):
    CLIENT_CALL = "client_call"  # Runs before the client sends a method call request
    CLIENT_RESULT = "client_result"  # Runs before the client processes the response
    SERVER_CALL = "server_call"  # Runs before the server processes the method call request
    SERVER_RESULT = "server_result"  # Runs before the server sends the response


class Middleware:
    __handlers__: ClassVar[set[FilterEvent]]

    def __init_subclass__(cls):
        # Find all filters provided by a middleware type
        cls.__handlers__ = {event for event in FilterEvent if f"filter_{event.value}" in vars(cls)}

    def __init__(self, **kwargs: Any):
        self.settings = kwargs

    def filter_client_call(self, payload: MethodCallPayload) -> Awaitable[MethodCallPayload]:
        """This filter is called before the client sends a method call request to a service."""
        raise NotImplementedError

    def filter_client_result(self, payload: ResultPayload) -> Awaitable[ResultPayload]:
        """This filter is called before the client processes the response from a service."""
        raise NotImplementedError

    def filter_server_call(self, payload: MethodCallPayload) -> Awaitable[MethodCallPayload]:
        """This filter is called before the server processes a method call request from a client."""
        raise NotImplementedError

    def filter_server_result(self, payload: ResultPayload) -> Awaitable[ResultPayload]:
        """This filter is called before the server sends a response to a client."""
        raise NotImplementedError


class MiddlewareStack:
    def __init__(self, middleware: list[Middleware]):
        self.middleware = middleware

    async def filter[T: MethodCallPayload | ReturnPayload](self, event: FilterEvent, payload: T) -> T:
        for middleware in self.middleware:
            if event in middleware.__handlers__:
                payload = await getattr(middleware, f"filter_{event.value}")(payload)

        return payload


class MiddlewareStackBuilder:
    def __init__(self, middleware: dict[Type[Middleware], dict[str, Any]]):
        self.middleware = middleware

    def get_middleware(self, *events: FilterEvent) -> MiddlewareStack:
        return MiddlewareStack(
            [
                middleware_type(**settings)
                for middleware_type, settings in self.middleware.items()
                if middleware_type.__handlers__.intersection(events)
            ]
        )
