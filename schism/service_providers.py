from bevy.providers.base import Provider
from schism.services import Service, ServiceProtocol
from typing import Callable, Type
from bevy.options import Option, Value


class ServiceProvider(Provider[Type[ServiceProtocol], ServiceProtocol]):
    def __init__(self, repository, service_manager):
        super().__init__(repository)
        self.bridged_services = {service.type: service for service in service_manager.services.values()}

    def factory(self, key: Type[ServiceProtocol]) -> Option[Callable[[], ServiceProtocol]]:
        match self.bridged_services.get(key, None):
            case Service() as service:
                return Value(service.bridge_client)

            case None:
                return Value(key)

    def supports(self, key: Type[ServiceProtocol]) -> bool:
        match key:
            case type() if issubclass(key, ServiceProtocol):
                return True

            case _:
                return False
