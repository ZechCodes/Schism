from bevy import inject, dependency
from schism import Service

remote = True


class GreetingService(Service):
    def __init__(self):
        super().__init__()
        print(f"{'[REMOTE]' if remote else '[LOCAL]'} Greeting service started")

    async def greet(self, name: str) -> str:
        print(f"{'[REMOTE]' if remote else '[LOCAL]'} Handling request...")
        return f"Hello, {name}!"


@inject
async def greet(greeting_service: GreetingService = dependency()):
    print(await greeting_service.greet("World"))


async def main():
    await greet()


if __name__ == "__main__":
    import asyncio

    remote = False
    asyncio.run(main())