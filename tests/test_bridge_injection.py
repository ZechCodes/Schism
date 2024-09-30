from pytest import fixture
from bevy import Repository, inject, dependency

from schism.configs import ServicesConfig
from schism.entry_points import create_entry_point
from schism.services import Service
from schism.wiring_strategies import BridgeWiringStrategy
import schism.controllers
import schism.entry_points


@fixture(scope="session", autouse=True)
def setup_runtime():
    schism.entry_points.clear_all_entry_points()

    repo = Repository.factory()
    repo.set(
        ServicesConfig,
        ServicesConfig(
            **{
                "services": [
                    {
                        "name": "service-a",
                        "service": "test_bridge_injection.ServiceA",
                        "bridge": "test_bridge_injection.Bridge",
                    },
                ],
            }
        )
    )
    Repository.set_repository(repo)

    controller = schism.controllers.get_controller()
    controller.wiring_strategy = BridgeWiringStrategy()


class ServiceA(Service):
    ...


class Bridge:
    def __init__(self, acting_as):
        self.acting_as = acting_as

    @classmethod
    def create_client(cls):
        return Bridge("client")

    @classmethod
    def create_server(cls):
        create_entry_point("test_service", Bridge("server"))


def test_client_injection():
    @inject
    def test(s: ServiceA = dependency()):
        return s

    service = test()
    assert isinstance(service, Bridge)
    assert service.acting_as == "client"


def test_server_creation():
    Bridge.create_server()
    assert isinstance(schism.entry_points.test_service, Bridge)
    assert schism.entry_points.test_service.acting_as == "server"
