"""Schism controllers manage the state and life cycle of the application, storing the list of configured services,
active & remote services, entry points for active services, and tasks that need to be launched at runtime.

Schism app's have two basic life cycles: service and application.
- Service life cycle: Create distributed controller, bootstrap service types by instantiating their types, set up the
service entry points by loading them into the "schism.run" module namespace, and finally launching the service tasks in
the event loop.
- Application life cycle: Import the application module & access the application callback, create the distributed
controller with the application callback, and finally run the application callback as a launch task in the event loop.

Included are the MonolithicController and DistributedController.

The MonolithicController is intended to run the application entirely standalone, in a singular process. To ensure
everything runs consistent with the life cycle of the DistributedController, it is important to launch your application
using the "start_app" function. Here's a stripped down example:

    from schism import start_app
    ...
    async def main():
        ...

    if __name__ == '__main__':
        start_app(main())

This starts the "main" app function in an event loop that exits when the "main" function returns, and it handles
bootstrapping all service types so they start in the correct order following the correct life cycle.

The DistributedController handles bootstrapping standalone services and running the application callback as its own
process that is autowired to access distributed services. This is typically done by running services and applications
using the "schism run" CLI."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Generator, Type, Callable, Awaitable

import bevy
from bevy import inject, dependency
from tramp.optionals import Optional

import schism.services as services
import schism.configs as configs
from schism.bridges import BridgeServiceFacade
from schism.middleware import MiddlewareStackBuilder

type ServicesConfigMapping = dict[Type[services.Service], configs.ServiceConfig]

_global_controller = None


def _validate_entry_point_name(name: str):
    if not name.isidentifier():
        raise RuntimeError(f"Entry point names must be valid Python identifiers: {name!r} (invalid)")

    if name.startswith("_"):
        raise RuntimeError(f"Entry point names cannot start with '_': {name!r} (invalid)")


class SchismController(ABC):
    def __init__(self, service: str = ""):
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

    def launch(self):
        if not self._launch_tasks:
            return

        asyncio.run(self._run_tasks())

    @inject
    def _load_services_configs(
       self, config: "configs.ApplicationConfig" = dependency()
    ) -> "Generator[tuple[str, configs.ServiceConfig], None, None]":
        for service_config in config.services:
            yield service_config.service, service_config

    async def _run_tasks(self):
        async with asyncio.TaskGroup() as group:
            for task in self._launch_tasks:
                await group.create_task(task)

    @classmethod
    def activate[Controller: SchismController](cls: Type[Controller], service: str = "") -> Controller:
        controller = cls(service)
        set_controller(controller)
        return controller

    @classmethod
    def start_application(cls, app: Awaitable[None]):
        """Activates the controller and starts the application."""
        controller = cls.activate()
        controller.add_launch_task(app)
        controller.launch()


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
        """Create all services."""
        for service_config in self.active_services.values():
            bevy.get_repository().get(service_config.get_service_type())  # Create the service instance

    def launch(self):
        self.bootstrap()
        super().launch()


class DistributedController(SchismController):
    def __init__(self, active_service: str):
        super().__init__()
        self._active_service_name = active_service
        self._servers = {}

    @property
    def active_services(self) -> ServicesConfigMapping:
        match self._active_services:
            case Optional.Some(active_services):
                return active_services

            case Optional.Nothing():
                self._active_services = Optional.Some(
                    dict(self.filter_services(lambda s: s.name == self._active_service_name))
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
                        self.filter_services(lambda s: s.service != self._active_service_name)
                    )
                )
                return self.remote_services

    def bootstrap(self):
        """Entry point processes need to bootstrap services that are active."""
        if not next(self.filter_services(lambda s: s.name == self._active_service_name), False):
            raise RuntimeError(
                f"Unknown service: {self._active_service_name}\n\nAll services must be configured in the "
                f"schism.config file."
            )

        for service_config in self.active_services.values():
            bevy.get_repository().get(service_config.get_service_type())  # Create the service instance
            self._launch_server(service_config)

    def _launch_server(self, service_config: configs.ServiceConfig):
        bridge = service_config.get_bridge_type()
        service_facade = BridgeServiceFacade(
            service_config.get_service_type(),
            MiddlewareStackBuilder(service_config.get_bridge_middleware()),
        )
        self._servers[service_config.service] = bridge.create_server(
            bridge.config_factory(service_config.bridge),
            service_facade,
        )


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


def start_app(app_callback: Awaitable[None]):
    MonolithicController.start_application(app_callback)
