import os
import threading
from typing import Generator, Type, TypeAlias, Callable

from bevy import inject, dependency
from tramp.optionals import Optional

import schism.services as services
import schism.configs as configs

ServicesConfigMapping: TypeAlias = "dict[Type[services.Service], configs.ServiceConfig]"

_global_controller = None
_controller_write_lock = threading.Lock()


class SchismController:
    ACTIVE_SERVICES = set(os.environ.get("SCHISM_ACTIVE_SERVICES", "").split(","))

    def __init__(self):
        self._service_configs: "dict[str, configs.ServiceConfig]" = dict(self._load_services_configs())
        self._active_services: Optional[ServicesConfigMapping] = Optional.Nothing()
        self._remote_services: Optional[ServicesConfigMapping] = Optional.Nothing()

    @property
    def active_services(self) -> ServicesConfigMapping:
        with _controller_write_lock:
            match self._active_services:
                case Optional.Some(active_services):
                    return active_services

                case Optional.Nothing():
                    self._active_services = Optional.Some(
                        dict(
                            self.filter_services(lambda s: s.service in self.ACTIVE_SERVICES)
                        )
                    )
                    return self.active_services

    @property
    def remote_services(self) -> ServicesConfigMapping:
        with _controller_write_lock:
            match self._remote_services:
                case Optional.Some(remote_services):
                    return remote_services

                case Optional.Nothing():
                    self._remote_services = Optional.Some(
                        dict(
                            self.filter_services(lambda s: s.service not in self.ACTIVE_SERVICES)
                        )
                    )
                    return self.remote_services

    def filter_services(
        self, condition: "Callable[[configs.ServiceConfig], bool]"
    ) -> "Generator[tuple[Type[services.Service], configs.ServiceConfig], None, None]":
        for service, service_config in self._service_configs.items():
            if condition(service_config):
                yield service, service_config

    def find_service_matching(self, service: Type[services.Service]) -> Optional[configs.ServiceConfig]:
        for s in self._service_configs.values():
            if issubclass(service, s.get_service_type()):
                return Optional.Some(s)

        return Optional.Nothing()

    def get_service_config(self, service: Type[services.Service]) -> configs.ServiceConfig:
        match self.find_service_matching(service):
            case Optional.Some(service_config):
                return service_config

            case Optional.Nothing():
                raise ValueError(f"No service matching {service} is configured.")

    def is_service_active(self, service: Type[services.Service]) -> bool:
        match self.find_service_matching(service):
            case Optional.Some(service_config):
                return service_config.service in self.ACTIVE_SERVICES

            case Optional.Nothing():
                raise ValueError(f"No service matching {service} is configured.")

    @inject
    def _load_services_configs(
            self, config: "configs.ServicesConfig" = dependency()
    ) -> "Generator[tuple[str, configs.ServiceConfig], None, None]":
        for service_config in config.services:
            yield service_config.service, service_config


def get_controller() -> SchismController:
    global _global_controller

    with _controller_write_lock:
        if _global_controller is None:
            _global_controller = SchismController()

        return _global_controller


def has_controller() -> bool:
    with _controller_write_lock:
        return _global_controller is not None


def set_controller(controller: SchismController):
    global _global_controller

    with _controller_write_lock:
        _global_controller = controller
