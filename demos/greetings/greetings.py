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
"""
from bevy import inject, dependency
from schism import Service, start_app
from schism.bridges import MethodCallPayload, ResultPayload
from schism.middleware import Middleware

remote = True


class MiddlewareExample(Middleware):
    async def filter_client_call(self, payload: MethodCallPayload) -> MethodCallPayload:
        print("[MIDDLEWARE] Client call filter")
        return payload

    async def filter_client_result(self, payload: ResultPayload) -> ResultPayload:
        print(f"[MIDDLEWARE] Client result filter")
        match payload:
            case {"result": result}:
                return {"result": f"Received From Service: {result!r}"}

            case _:
                return payload

    async def filter_server_call(self, payload: MethodCallPayload) -> MethodCallPayload:
        print("[MIDDLEWARE] Server call filter")
        return payload

    async def filter_server_result(self, payload: MethodCallPayload) -> MethodCallPayload:
        print("[MIDDLEWARE] Server result filter")
        return payload


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
