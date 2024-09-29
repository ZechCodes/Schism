from typing import Type, TypeVar

from schism.wiring_strategies import BaseWiringStrategy


T = TypeVar("T")


class DirectWiringStrategy(BaseWiringStrategy):
    def get_facade(self, target: Type[T]) -> T:
        return target()
