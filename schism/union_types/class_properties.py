from typing import Any, Callable, Type, TypeVar
from types import FunctionType


_T = TypeVar("_T")


class ClassProperty:
    def __init__(self, func):
        self._getter = func
        self._setter = None

    def setter(self, func: Callable[[Any], None]):
        self._setter = func
        return self

    def __get__(self, instance: _T, owner: Type[_T] | None = ...) -> Callable[..., Any]:
        return self._getter(owner)

    def __set__(self, instance: _T, value: Any):
        match self._setter:
            case FunctionType() as setter:
                setter(type(instance), value)
            case _:
                return
