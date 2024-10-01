from bevy import inject, dependency

import schism.controllers

from conftest import ServiceA, Bridge
from pytest_asyncio import fixture
from schism.controllers import get_controller, set_controller, EntryPointController

@fixture(autouse=True)
def setup_entry_point_runtime(setup_runtime):
    set_controller(EntryPointController())


def test_client_injection():
    @inject
    def test(s: ServiceA = dependency()):
        return s

    service = test()
    assert isinstance(service, Bridge)
    assert service.acting_as == "client"


def test_server_creation():
    Bridge.create_server(ServiceA)
    assert isinstance(get_controller().entry_points["test_service"], Bridge)
    assert get_controller().entry_points["test_service"].acting_as == "server"
