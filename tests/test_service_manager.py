from schism.service_manager import ServiceManager
from schism.services import Service


class HostBridge:
    def __init__(self):
        self.launched = False

    async def launch(self):
        self.launched = True


def test_service_manager_entry_point():
    entered = False

    async def entry():
        nonlocal entered
        entered = True

    services = {
        "test-service": Service(
            "test-service",
            entry,
            None,
            {},
            HostBridge,
            {},
        )
    }

    manager = ServiceManager("test-service", services)
    manager.launch()
    assert entered


def test_service_manager_host_bridge():
    async def entry():
        ...

    services = {
        "test-service": Service(
            "test-service",
            entry,
            None,
            {},
            HostBridge,
            {},
        )
    }

    manager = ServiceManager("test-service", services)
    manager.launch()
    assert manager.repo.get(manager.active_service.bridge_host).launched
