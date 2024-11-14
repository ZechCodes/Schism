from typing import Awaitable

import pytest
from bevy import inject, dependency

from conftest import ServiceA, Bridge
from schism.bridges import BridgeClientFacade, MethodCallPayload, ResultPayload
from schism.controllers import get_controller
from schism.middleware import ContextualMiddleware, Middleware, MiddlewareContext, MiddlewareStack


def test_client_injection(simple_entry_point_runtime):
    @inject
    def test(s: ServiceA = dependency()):
        return s

    service = test()
    assert isinstance(service, BridgeClientFacade)
    assert isinstance(service.client, Bridge)
    assert service.client.acting_as == "client"


def test_server_creation(simple_entry_point_runtime):
    Bridge.create_server(ServiceA)
    assert isinstance(get_controller().entry_points["test_service"], Bridge)
    assert get_controller().entry_points["test_service"].acting_as == "server"


@pytest.mark.asyncio
async def test_middleware():
    visited = set()
    class DummyMiddlewareA(Middleware):
        def run(self, payload):
            visited.add(f"{self.context.value}_a")
            return self.next(reversed(payload))

    class DummyMiddlewareB(DummyMiddlewareA):
        def run(self, payload):
            visited.add(f"{self.context.value}_b")
            return self.next("".join(payload))

    class DummyMiddlewareC(ContextualMiddleware):
        def run_on_client(self, payload):
            visited.add(f"{self.context.value}_c")
            return self.next(payload.center(11, "*"))

        def run_on_server(self, payload):
            visited.add(f"{self.context.value}_c")
            return self.next(payload.center(11, "-"))

    async def dummy_action(payload):
        return payload.lower()

    stack = MiddlewareStack(DummyMiddlewareA, DummyMiddlewareB, DummyMiddlewareC)
    result = await stack.run(MiddlewareContext.CLIENT, "EULAV", dummy_action)
    assert result == "***value***"
    assert visited == {"client_a", "client_b", "client_c"}

    visited.clear()

    result = await stack.run(MiddlewareContext.SERVER, "EULAV", dummy_action)
    assert result == "---value---"
    assert visited == {"server_a", "server_b", "server_c"}
