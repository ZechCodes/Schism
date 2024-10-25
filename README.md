# Schism

Schism is a service framework designed to simplify the process of splitting a single application into multiple services. It provides autowiring capabilities that make modularity straightforward in monolithic applications and facilitates code sharing in microservices architectures.

## Installation

```bash
pip install schism
```

## Usage

Schism is designed to have the smallest possible API surface area. You just need to create a service type that inherits from `schism.Service`. You can use [Bevy's](https://github.com/ZechCodes/Bevy) dependency injection to inject services into any function.

Creating a `schism.config.yaml` file in the root of your project will allow you to define the services that should be available in your application and how they should be exposed. Bevy then handles injecting the correct client facades into your functions so you can interact with the services as if they are still part of the same application. 

To launch a service either set the `SCHISM_ACTIVE_SERVICE` environment variable to the name of the service to run using the `schism run` command. Alternatively pass the name to the `schism run service` command. Schism then starts the  appropriate bridge servers using the configuration in the `schism.config.yaml`.

To run a client application that understands the running services use the `schism run` command. Pass it the desired  module and callback (ex. `module.path:callback`) that you want to run (alternatively set up a launch config). Schism handles injecting the appropriate service client facades into the runtime before running the callback.

### Example

Here's a basic example of a service that provides a simple greeting.

```python
# greetings.py
from bevy import inject, dependency
from schism import Service, start_app

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
    start_app(main())  # Activate a Schism controller and launch the app
```
Here is the corresponding `schism.config.yaml` file:

```yaml
launch:
  app: greetings:main
services:
  - name: greeting
    service: greetings:GreetingService
    bridge:
      type: schism.ext.bridges.simple_tcp:SimpleTCP
      serve_on: localhost:1234
```

To run you must first start the greetings service with this command:

```bash
schism run service greeting
```

Then you can run the script and that accesses the service by passing `schism.run` the entry point coroutine:

```bash
schism run
```

Alternatively you can run it as a normal Python script with no client facades where everything runs in a single process.

```bash
python greetings.py
```
or
```bash
python -m greetings
```
