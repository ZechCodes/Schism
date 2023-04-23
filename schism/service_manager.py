from bevy import get_repository
from schism.services import Service
from schism.service_providers import ServiceProvider
from schism.utils.options import Value
from inspect import isawaitable
from asyncio import get_event_loop, AbstractEventLoop


class ServiceManager:
    def __init__(self, active_service_name: str, services: dict[str, Service]):
        self.active_service = services.pop(active_service_name)
        self.services = services
        self.repo = get_repository()

    def launch(self):
        loop = get_event_loop()
        self.setup_repository(loop)
        self.launch_bridge_host(loop)

    def launch_bridge_host(self, loop: AbstractEventLoop):
        loop = get_event_loop()
        match self.repo.get(self.active_service.bridge_host):
            case self.active_service.bridge_host() as bridge:
                host_task = bridge.launch()
                if isawaitable(host_task):
                    loop.create_task(host_task)

        loop.run_until_complete(self.active_service.entry_point())

    def setup_repository(self, loop: AbstractEventLoop):
        self.repo.add_providers(ServiceProvider)
        self.repo.set(AbstractEventLoop, loop)
        self.repo.set(ServiceManager, self)
