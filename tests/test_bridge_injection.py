from pytest import fixture
from bevy import Repository, inject, dependency

from schism.configs import ServicesConfig
from schism.services import Service
from schism.wiring_strategies import BridgeWiringStrategy
import schism.controllers


@fixture(scope="session", autouse=True)
def setup_runtime():
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


def test_client_injection():
    @inject
    def test(s: ServiceA = dependency()):
        return s

    service = test()
    assert isinstance(service, Bridge)
    assert service.acting_as == "client"
