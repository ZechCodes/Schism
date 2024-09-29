from typing import TypeVar, Type

from bevy import inject, dependency

from schism.configs import ServicesConfig, ServiceConfig
from schism.services import Service
from schism.wiring_strategies import BaseWiringStrategy


T = TypeVar("T")


class ServiceData:
    def __init__(self, service: Service, config: ServiceConfig):
        self.service = service
        self.config = config
        self._client = None
        self._server = None

    @property
    def client(self):
        if self._client is None:
            self._client = self.config.get_bridge_type().create_client()

        return self._client

    @property
    def server(self):
        if self._server is None:
            self._server = self.config.get_bridge_type().create_server()

        return self._server


class BridgeWiringStrategy(BaseWiringStrategy):
    def __init__(self):
        self._service_cache: dict[Type[Service], ServiceData] = {}

    def get_facade(self, target: Type[T]) -> T:
        if target not in self._service_cache:
            self._initialize_service(target)

        return self._service_cache[target].client

    def _initialize_service(self, target: Type[Service]):
        service_config = self._find_service_config(target)
        service = service_config.get_service_type()()
        self._service_cache[target] = ServiceData(service, service_config)

    @inject
    def _find_service_config(self, target: Type[T], config: ServicesConfig = dependency()) -> ServiceConfig:
        for service in config.services:
            if issubclass(target, service.get_service_type()):
                return service

        raise RuntimeError(f"Service config not found for {target.__module__}.{target.__qualname__}")