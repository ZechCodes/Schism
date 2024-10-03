import asyncio
import os
from abc import ABC, abstractmethod
from typing import Any, Generator, Type, TypeAlias, Callable, Awaitable

from bevy import inject, dependency
from tramp.optionals import Optional

import schism.services as services
import schism.configs as configs

ServicesConfigMapping: TypeAlias = "dict[Type[services.Service], configs.ServiceConfig]"

_global_controller = None


def _validate_entry_point_name(name: str):
    if not name.isidentifier():
        raise RuntimeError(f"Entry point names must be valid Python identifiers: {name!r} (invalid)")

    if name.startswith("_"):
        raise RuntimeError(f"Entry point names cannot start with '_': {name!r} (invalid)")


class SchismController(ABC):
    def __init__(self):
        self._service_configs: "Optional[dict[str, configs.ServiceConfig]]" = Optional.Nothing()
        self._active_services: Optional[ServicesConfigMapping] = Optional.Nothing()
        self._remote_services: Optional[ServicesConfigMapping] = Optional.Nothing()
        self._entry_points: dict[str, Any] = {}
        self._launch_tasks: list[Awaitable[None]] = []

    @property
    @abstractmethod
    def active_services(self) -> ServicesConfigMapping:
        """Returns a mapping of services that are running in the current process."""

    @property
    @abstractmethod
    def remote_services(self) -> ServicesConfigMapping:
        """Returns a mapping of services that are not running in the current process."""

    @abstractmethod
    def bootstrap(self):
        """Bootstraps the running process to make services available."""

    @abstractmethod
    def launch(self):
        """Creates an event loop and runs all launch tasks."""

    @property
    def entry_points(self) -> dict[str, Any]:
        return self._entry_points

    @property
    def service_configs(self) -> dict[str, configs.ServiceConfig]:
        match self._service_configs:
            case Optional.Some(service_configs):
                return service_configs

            case Optional.Nothing():
                self._service_configs = Optional.Some(
                    dict(self._load_services_configs())
                )
                return self.service_configs

    def add_launch_task(self, task: Awaitable[None]):
        self._launch_tasks.append(task)

    def create_entry_point(self, name: str, entry_point: Any):
        _validate_entry_point_name(name)
        self._entry_points[name] = entry_point

    def filter_services(
        self, condition: "Callable[[configs.ServiceConfig], bool]"
    ) -> "Generator[tuple[Type[services.Service], configs.ServiceConfig], None, None]":
        for service, service_config in self.service_configs.items():
            if condition(service_config):
                yield service_config.get_service_type(), service_config

    def find_service_matching(self, service: "Type[services.Service]") -> "Optional[configs.ServiceConfig]":
        for s in self.service_configs.values():
            if issubclass(service, s.get_service_type()):
                return Optional.Some(s)

        return Optional.Nothing()

    def get_service_config(self, service: "Type[services.Service]") -> "configs.ServiceConfig":
        match self.find_service_matching(service):
            case Optional.Some(service_config):
                return service_config

            case Optional.Nothing():
                raise ValueError(f"No service matching {service} is configured.")

    def is_service_active(self, service: "Type[services.Service]") -> bool:
        return self.get_service_config(service).get_service_type() in self.active_services

    @inject
    def _load_services_configs(
            self, config: "configs.ServicesConfig" = dependency()
    ) -> "Generator[tuple[str, configs.ServiceConfig], None, None]":
        for service_config in config.services:
            yield service_config.service, service_config


class MonolithicController(SchismController):
    @property
    def active_services(self) -> ServicesConfigMapping:
        match self._active_services:
            case Optional.Some(active_services):
                return active_services

            case Optional.Nothing():
                self._active_services = Optional.Some(
                    {
                        service.get_service_type(): service
                        for service in self.service_configs.values()
                    }
                )
                return self.active_services

    @property
    def remote_services(self) -> ServicesConfigMapping:
        return {}

    def bootstrap(self):
        """Monolithic processes don't have services that need to be bootstrapped."""
        return

    def launch(self):
        """Monoithic processes don't have services that need to be launched."""
        return


class EntryPointController(SchismController):
    def __init__(self, active_services: set[str]):
        super().__init__()
        self._env_active_services = active_services
        self._servers = {}

    @property
    def active_services(self) -> ServicesConfigMapping:
        match self._active_services:
            case Optional.Some(active_services):
                return active_services

            case Optional.Nothing():
                self._active_services = Optional.Some(
                    dict(self.filter_services(lambda s: s.name in self._env_active_services))
                )
                return self.active_services

            case invalid_state:
                raise ValueError(f"Invalid state: {invalid_state}")

    @property
    def remote_services(self) -> ServicesConfigMapping:
        match self._remote_services:
            case Optional.Some(remote_services):
                return remote_services

            case Optional.Nothing():
                self._remote_services = Optional.Some(
                    dict(
                        self.filter_services(lambda s: s.service not in self._env_active_services)
                    )
                )
                return self.remote_services

    def bootstrap(self):
        """Entry point processes need to bootstrap services that are active."""
        for service_config in self.active_services.values():
            self._launch_server(service_config)

    def launch(self):
        if not self._launch_tasks:
            return

        asyncio.run(self._run_tasks())

    def _launch_server(self, service_config: configs.ServiceConfig):
        bridge = service_config.get_bridge_type()
        self._servers[service_config.service] = bridge.create_server(
            service_config.get_service_type(),
            bridge.config_factory(service_config.bridge),
        )

    async def _run_tasks(self):
        async with asyncio.TaskGroup() as group:
            for task in self._launch_tasks:
                await group.create_task(task)


def get_controller() -> SchismController:
    global _global_controller

    if _global_controller is None:
        _global_controller = MonolithicController()

    return _global_controller


def has_controller() -> bool:
    return _global_controller is not None


def set_controller(controller: SchismController):
    global _global_controller

    _global_controller = controller


def activate(services: set[str] | None = None) -> SchismController:
    """Activates the entry point controller."""
    services = services or set()
    controller = EntryPointController(services)
    set_controller(controller)
    return controller


def start(app: Awaitable[None]):
    """Activates Schism's entry point controller and starts the application."""
    controller = activate()
    controller.add_launch_task(app)
    controller.launch()
