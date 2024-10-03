# Schism

Schism is a service framework designed to simplify the process of splitting a single application into multiple services.
It provides autowiring capabilities that make modularity straightforward in monolithic applications and facilitates code
sharing in microservices architectures.

## Installation

```bash
pip install schism
```

## Usage

Schism is designed to have the smallest possible API surface area. You just need to create a service type that inherits
from `schism.Service`. You can use [Bevy's](https://github.com/ZechCodes/Bevy) dependency injection to inject services
into any function.

Creating a `schism.config.yaml` file in the root of your project will allow you to define the services that should be
available in your application and how they should be exposed. Bevy then handles injecting the correct client facades
into your functions so you can interact with the services as if they are still part of the same application.

To launch individual services you just need to set the `SCHISM_ACTIVE_SERVICES` environment variable to a
comma-separated list of the qualified names of the services you want to run. Schism will then start the appropriate
bridge servers using the configuration in the `schism.config.yaml` file when you run the `schism.entry_points` module.
Typically, you should only run a single service per process.

Here's a basic example of a service that provides a simple greeting.

```python
# greetings.py
from bevy import inject, dependency
from schism import Service

class GreetingService(Service):
    async def greet(self, name: str) -> str:
        print("Handling request...")
        return f"Hello, {name}!"


@inject
async def greet(greeting_service: GreetingService = dependency()):
    print(await greeting_service.greet("World"))


async def main():
    await greet()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```
Here is the corresponding `schism.config.yaml` file:

```yaml
services:
  - bridge:
      type: schism.bridges.simple_tcp_bridge.SimpleTCPBridge
      host: localhost
      port: 1234
    name: greeting-service
    service: greetings.GreetingService
```

To run you must first start the greetings service with this command:

```bash
SCHISM_ACTIVE_SERVICES=greeting-service schism
```

Then you can run the script and that accesses the service by passing `schism.run` the entry point coroutine:

```bash
schism greetings.main
```

Alternatively you can run it like a normal Python script and no client facades will be injected and everything will run
in a single process.

```bash
python greetings.py
```
