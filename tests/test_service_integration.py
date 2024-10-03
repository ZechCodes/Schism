import asyncio

import pytest
from bevy import Repository

from schism import controllers

from service_test import ServiceC


@pytest.fixture(autouse=True)
def setup_service_runtime():
    repo = Repository.factory()
    Repository.set_repository(repo)

    controller = controllers.EntryPointController()
    controller._env_active_services = {"services_test.ServiceC"}
    controllers.set_controller(controller)


@pytest.mark.asyncio
async def test_service_integration():
    service_a = await asyncio.create_subprocess_shell(
        'SCHISM_ACTIVE_SERVICES="service_test.ServiceA" python -m schism.entry_points',
    )
    service_b = await asyncio.create_subprocess_shell(
        'SCHISM_ACTIVE_SERVICES="service_test.ServiceB" python -m schism.entry_points',
    )
    await asyncio.sleep(1)

    try:
        service = ServiceC()
        assert service.a_is_remote()
        assert service.b_is_remote()

        await service.udpate_a()
        await service.udpate_b()
        assert await service.get_a() == 1
        assert await service.get_b() == 1

        await service.udpate_a()
        await service.udpate_b()
        assert await service.get_a() == 2
        assert await service.get_b() == 2

    finally:
        service_a.terminate()
        service_b.terminate()
        await service_a.wait()
        await service_b.wait()
