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


class MiddlewareStackRuntime:
    def __init__(self, middleware: list[Middleware]):
        self.middleware = middleware

    async def filter[T: MethodCallPayload | ReturnPayload](self, event: FilterEvent, payload: T) -> T:
        for middleware in self.middleware:
            if event in middleware.__handlers__:
                payload = await getattr(middleware, f"filter_{event.value}")(payload)

        return payload


class MiddlewareStack:
    def __init__(self, middleware: dict[Type[Middleware], dict[str, Any]]):
        self.middleware = middleware

    def get_middleware(self, *events: FilterEvent) -> MiddlewareStackRuntime:
        return MiddlewareStackRuntime(
            [
                middleware_type(**settings)
                for middleware_type, settings in self.middleware.items()
                if middleware_type.__handlers__.intersection(events)
            ]
        )
