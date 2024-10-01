from typing import Type

from bevy import Repository
from pytest_asyncio import fixture

import schism.controllers
import schism.entry_points
from schism.configs import ServicesConfig
from schism.services import Service


class ServiceA(Service):
    ...


class ServiceB(Service):
    ...


class Bridge:
    def __init__(self, acting_as):
        self.acting_as = acting_as

    @classmethod
    def create_client(cls, service: Type[Service]):
        return Bridge("client")

    @classmethod
    def create_server(cls, service: Type[Service]):
        schism.entry_points.create_entry_point("test_service", Bridge("server"))


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
                        "service": "conftest.ServiceA",
                        "bridge": "conftest.Bridge",
                    },
                    {
                        "name": "service-b",
                        "service": "conftest.ServiceB",
                        "bridge": "conftest.Bridge",
                    },
                ],
            }
        )
    )
    Repository.set_repository(repo)

    controller = schism.controllers.get_controller()
    controller.ACTIVE_SERVICES = {"service-a"}
