from bevy import inject, dependency

from conftest import ServiceA, Bridge
from schism.bridges.bases import BridgeClientFacade
from schism.controllers import get_controller


def test_client_injection(simple_entry_point_runtime):
    @inject
    def test(s: ServiceA = dependency()):
        return s

    service = test()
    assert isinstance(service, BridgeClientFacade)
    assert isinstance(service.client, Bridge)
    assert service.client.acting_as == "client"


def test_server_creation(simple_entry_point_runtime):
    Bridge.create_server(ServiceA)
    assert isinstance(get_controller().entry_points["test_service"], Bridge)
    assert get_controller().entry_points["test_service"].acting_as == "server"
