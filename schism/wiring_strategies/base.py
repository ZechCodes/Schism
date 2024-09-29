from abc import ABC, abstractmethod
from typing import Type, TypeVar

T = TypeVar("T")


class BaseWiringStrategy(ABC):
    @abstractmethod
    def get_facade(self, target: Type[T]) -> T:
        ...
