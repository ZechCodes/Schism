from bevy import Repository
from pytest_asyncio import fixture

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


@fixture(autouse=True)
def setup_runtime():
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

    controllers.SchismController.ACTIVE_SERVICES = {"service-a"}
    controllers.set_controller(controllers.EntryPointController())
