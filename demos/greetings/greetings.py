"""
Greeting Demo

When running this script directly it will run as a single, monolithic, application in a single process.

If it is run using the schism command it must be run as two separate processes: the greeting service and the "user"
facing application. To run the greeting service use the command: `schism run service greeting`. Then you can use the
`schism run` command to launch the application. You can run that second command any number of times and each time it
directs calls to the greeting service running in the other process.

The demo can also be run in a single process by running it as a normal python script using either the
`python greetings.py` or `python -m greetings` command. This keeps everything running in the same process with no
changes made in the runtime.

This demo also contains a simple middleware that logs out values at each filter event and filters the final result in
the client.
"""
from bevy import inject, dependency
from schism import Service, start_app
from schism.bridges import MethodCallPayload, ResultPayload
from schism.middleware import ContextualMiddleware

remote = True


class MiddlewareExample(ContextualMiddleware):
    async def run_on_client(self, payload: MethodCallPayload) -> ResultPayload:
        print("[MIDDLEWARE] Client call")
        result = await self.next(payload)
        print("[MIDDLEWARE] Client result")
        match result:
            case {"result": value}:
                return {"result": f"Received From Service: {value!r}"}
            case _:
                return result

    async def run_on_server(self, payload: MethodCallPayload) -> ResultPayload:
        print("[MIDDLEWARE] Server call")
        result = await self.next(payload)
        print("[MIDDLEWARE] Server result")
        return result


class GreetingService(Service):
    def __init__(self):
        super().__init__()
        self.running = "REMOTE" if remote else "LOCAL"
        print(f"[{self.running}] Greeting service created")

    async def greet(self, name: str) -> str:
        print(f"[{self.running}] Handling request...")
        return f"Hello, {name}!"


@inject
async def greet(greeting_service: GreetingService = dependency()):
    print(await greeting_service.greet("World"))


async def main():
    await greet()


if __name__ == "__main__":
    remote = False
    start_app(main())
