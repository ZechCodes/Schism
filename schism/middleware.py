from abc import ABC, abstractmethod
from enum import Enum
from functools import cache
from typing import Awaitable, Callable

from schism.bridges import MethodCallPayload, ResultPayload


type MiddlewareConstructor = Callable[[MiddlewareContext, NextCallable], Middleware]
type NextCallable = Callable[[MethodCallPayload], Awaitable[ResultPayload]]


class MiddlewareContext(Enum):
    CLIENT = "client"
    SERVER = "server"


class Middleware(ABC):
    def __init__(self, context: MiddlewareContext, next_call: NextCallable):
        self.context = context
        self.next = next_call

    @abstractmethod
    def run(self, payload: MethodCallPayload) -> Awaitable[ResultPayload]:
        ...


class ContextualMiddleware(Middleware):
    def run(self, payload: MethodCallPayload) -> Awaitable[ResultPayload]:
        match self.context:
            case MiddlewareContext.CLIENT:
                return self.run_on_client(payload)
            case MiddlewareContext.SERVER:
                return self.run_on_server(payload)
            case _:
                raise ValueError(f"Invalid context: {self.context}")

    @abstractmethod
    def run_on_client(self, payload: MethodCallPayload) -> Awaitable[ResultPayload]:
        ...

    @abstractmethod
    def run_on_server(self, payload: MethodCallPayload) -> Awaitable[ResultPayload]:
        ...


class MiddlewareStack:
    def __init__(self, *middleware: MiddlewareConstructor):
        self.middleware = middleware

    def run(
        self,
        context: MiddlewareContext,
        payload: MethodCallPayload,
        action: NextCallable,
    ) -> Awaitable[ResultPayload]:
        return self._get_stack(context, action)(payload)

    @cache
    def _get_stack(self, context: MiddlewareContext, action: NextCallable) -> NextCallable:
        stack = action
        for middleware in self.middleware[::-1]:
            stack = middleware(context, stack).run

        return stack


