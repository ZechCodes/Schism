from schism.service_manager import ServiceManager
from schism.services import Service
from typing import Annotated


class ClientBridge:
    def __init__(self):
        self.created = True


class HostBridge:
    def __init__(self):
        self.launched = False

    async def launch(self):
        self.launched = True


class TestService:
    def __init__(self):
        self.launched = False

    async def launch(self):
        self.launched = True


def test_service_manager_entry_point():
    services = {
        "test-service": Service(
            "test-service",
            TestService,
            TestService.launch,
            None,
            {},
            HostBridge,
            {},
        )
    }

    manager = ServiceManager("test-service", services)
    manager.launch()
    assert manager.repo.get(Annotated[TestService, f"service[{manager.active_service.name}]"]).launched


def test_service_manager_host_bridge():
    services = {
        "test-service": Service(
            "test-service",
            TestService,
            TestService.launch,
            None,
            {},
            HostBridge,
            {},
        )
    }

    manager = ServiceManager("test-service", services)
    manager.launch()
    assert manager.repo.get(manager.active_service.bridge_host).launched


def test_service_manager_client_bridge():
    class Dep:
        def __init__(self):
            self.created = True
            self.launched = False

        def launch(self):
            self.launched = True

    services = {
        "test-service": Service(
            "test-service",
            TestService,
            TestService.launch,
            None,
            {},
            HostBridge,
            {},
        ),
        "dep-service": Service(
            "dep-service",
            Dep,
            Dep.launch,
            ClientBridge,
            {},
            None,
            {},
        )
    }

    manager = ServiceManager("test-service", services)
    manager.launch()
    assert isinstance(manager.repo.get(Dep), ClientBridge)
