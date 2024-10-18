"""
Greeting Demo

When running this script directly it will run as a single, monolithic, application in a single process.

If it is run using the schism command it must be run as two separate processes: the greeting service and the "user"
facing application. To run the greeting service use the command: `schism run services greeting-service`. Then you can
run the application using the command: `schism run greetings.main`. You can run that any number of times and it will
always direct calls to the greeting service class to the service running in the other running process.

The demo can also be run in a single process by running it as a normal python script using either the
`python greetings.py` or `python -m greetings` command. This will not direct calls to an external service, everything
runs in the same process as normal.
"""
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