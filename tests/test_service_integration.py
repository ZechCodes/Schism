import asyncio
from contextlib import AsyncExitStack

import pytest
from bevy import Repository

from schism.controllers import DistributedController

from service_test import ServiceC


@pytest.fixture(autouse=True)
def setup_service_runtime():
    repo = Repository.factory()
    Repository.set_repository(repo)

    DistributedController.activate()


@pytest.mark.asyncio
async def test_service_integration():
    async with AsyncExitStack() as stack:
        service_a = await asyncio.create_subprocess_shell(
            "python -m schism.run service service-a",
        )
        stack.push_async_callback(_kill, service_a)

        service_b = await asyncio.create_subprocess_shell(
            "SCHISM_ACTIVE_SERVICE=service-b python -m schism.run service",
        )
        stack.push_async_callback(_kill, service_b)

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


async def _kill(process):
    process.terminate()
    await process.wait()
