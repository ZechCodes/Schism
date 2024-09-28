from abc import ABC, abstractmethod
from typing import TypeVar, Type

T = TypeVar("T")


class WiringStrategy(ABC):
    @abstractmethod
    def get_facade(self, target: Type[T]) -> T:
        ...


class DirectWiringStrategy(WiringStrategy):
    def get_facade(self, target: Type[T]) -> T:
        return target()
