from bevy.providers.base import Provider
from schism.services import Service
from typing import Type


class ServiceProvider(Provider):
    def supports(self, key: Type[Service]) -> bool:
        match key:
            case type() if issubclass(key, Service):
                return True

            case _:
                return False
