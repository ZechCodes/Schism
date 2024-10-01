from bevy import inject, dependency

from schism.entry_points import create_entry_point
import schism.controllers
import schism.entry_points

from conftest import ServiceA, Bridge


def test_client_injection():
    @inject
    def test(s: ServiceA = dependency()):
        return s

    service = test()
    assert isinstance(service, Bridge)
    assert service.acting_as == "client"


def test_server_creation():
    Bridge.create_server(ServiceA)
    assert isinstance(schism.entry_points.test_service, Bridge)
    assert schism.entry_points.test_service.acting_as == "server"
