from bevy import dependency, inject

from schism.ext.bridges.simple_tcp import SimpleTCPClient
from schism.services import Service


class ServiceA(Service):
    def __init__(self):
        self.value = 0

    async def increment(self):
        self.value += 1

    async def get_value(self):
        return self.value


class ServiceB(Service):
    def __init__(self):
        self.value = 0

    async def increment(self):
        self.value += 1

    async def get_value(self):
        return self.value


class ServiceC(Service):
    @inject
    async def udpate_a(self, a: ServiceA = dependency()):
        await a.increment()

    @inject
    async def udpate_b(self, b: ServiceB = dependency()):
        await b.increment()

    @inject
    async def get_a(self, a: ServiceA = dependency()):
        return await a.get_value()

    @inject
    async def get_b(self, b: ServiceB = dependency()):
        return await b.get_value()

    @inject
    def a_is_remote(self, a: ServiceA = dependency()):
        return isinstance(a, SimpleTCPClient)

    @inject
    def b_is_remote(self, b: ServiceB = dependency()):
        return isinstance(b, SimpleTCPClient)
