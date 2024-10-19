from bevy import Repository
from pytest_asyncio import fixture

from schism.controllers import DistributedController
from schism.configs import ServicesConfig
from schism.services import Service
import schism.controllers as controllers


class ServiceA(Service):
    ...


class ServiceB(Service):
    ...


class Bridge:
    def __init__(self, acting_as):
        self.acting_as = acting_as

    @classmethod
    def create_client(cls, *_):
        return Bridge("client")

    @classmethod
    def create_server(cls, *_):
        controllers.get_controller().create_entry_point("test_service", Bridge("server"))

    @classmethod
    def config_factory(cls, bridge_config):
        return bridge_config


@fixture
def simple_entry_point_runtime():
    repo = Repository.factory()
    repo.set(
        ServicesConfig,
        ServicesConfig(
            services = [
                {
                    "name": "service-a",
                    "service": "conftest.ServiceA",
                    "bridge": "conftest.Bridge",
                },
                {
                    "name": "service-b",
                    "service": "conftest.ServiceB",
                    "bridge": "conftest.Bridge",
                },
            ],
        )
    )
    Repository.set_repository(repo)

    DistributedController.activate()
