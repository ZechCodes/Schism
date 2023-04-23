from typing import Generic, Type, TypeVar
from schism.utils.class_properties import ClassProperty
from schism.utils.singleton_classes import SingletonClass


_T = TypeVar("_T")


class NullOptionException(Exception):
    ...


class Option(Generic[_T]):
    Value: "Type[Value[_T]]"
    Null: "Type[Null[_T]]"


class Value(Option[_T]):
    __match_args__ = ("value",)

    def __init__(self, value: _T):
        self.value = value

    def get(self, default: _T) -> _T:
        return self.value

    def __bool__(self):
        return True

    def __repr__(self):
        return f"{type(self).__name__}({self.value!r})"


class Null(SingletonClass, Value[_T]):
    @ClassProperty
    def value(cls) -> _T:
        raise NullOptionException("Null value")

    @value.setter
    def value(self, _):
        return

    @classmethod
    def get(cls, default: _T) -> _T:
        return default

    def __bool__(self):
        return False

    def __call__(self, *_):
        return self

    def __repr__(self):
        return f"{type(self).__name__}()"


Option.Value = Value
Option.Null = Null
