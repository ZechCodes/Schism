import asyncio
import os
from contextlib import AsyncExitStack
from pathlib import Path

import pytest
from bevy import get_registry
from bevy.containers import global_container

from schism.configs import ApplicationConfig
from schism.controllers import DistributedController
from schism.services import wait_for

from service_test import ServiceA, ServiceB, ServiceC

import schism  # ensure bevy hooks are registered

TESTS_DIR = Path(__file__).parent
PROJECT_ROOT = TESTS_DIR.parent


@pytest.fixture(autouse=True)
def setup_service_runtime():
    container = get_registry().create_container()
    container.instances[ApplicationConfig] = ApplicationConfig(
        services=[
            {
                "name": "service-a",
                "service": "service_test:ServiceA",
                "bridge": {
                    "type": "schism.ext.bridges.simple_tcp:SimpleTCP",
                    "serve_on": "localhost:1234",
                },
            },
            {
                "name": "service-b",
                "service": "service_test:ServiceB",
                "bridge": {
                    "type": "schism.ext.bridges.simple_tcp:SimpleTCP",
                    "serve_on": "localhost:4321",
                },
            },
        ],
    )
    global_container.set(container)

    DistributedController.activate()


@pytest.mark.asyncio
async def test_service_integration():
    env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}

    async with AsyncExitStack() as stack:
        service_a = await asyncio.create_subprocess_shell(
            "python -m schism.run service service-a",
            cwd=str(TESTS_DIR),
            env=env,
        )
        stack.push_async_callback(_kill, service_a)

        service_b = await asyncio.create_subprocess_shell(
            "SCHISM_ACTIVE_SERVICE=service-b python -m schism.run service",
            cwd=str(TESTS_DIR),
            env=env,
        )
        stack.push_async_callback(_kill, service_b)

        await wait_for(ServiceA)
        await wait_for(ServiceB)

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
