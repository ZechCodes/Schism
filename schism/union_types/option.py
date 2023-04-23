from typing import Any, Generic, Type, TypeVar


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


class Null(Value[_T]):
    def __init__(self):
        super().__init__(None)

    def __instancecheck__(self, instance):
        return instance is self

    @property
    def value(self) -> _T:
        raise NullOptionException("Null value")

    @value.setter
    def value(self, _):
        return

    def get(self, default: _T) -> _T:
        return default

    def __bool__(self):
        return False

    def __call__(self, *_):
        return self

    def __repr__(self):
        return f"{type(self).__name__}()"


Option.Value = Value
Option.Null = Null()
