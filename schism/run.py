import os
import sys
from importlib import import_module
from typing import Any

from bevy import inject, dependency

from schism.configs import ApplicationConfig
from schism.controllers import SchismController, DistributedController


def start_services(service: str):
    controller = setup_controller(service)
    setup_entry_points(controller)
    controller.launch()


def setup_controller(service: str) -> SchismController:
    controller = DistributedController.activate(service)
    controller.bootstrap()
    return controller


def setup_entry_points(controller: SchismController):
    for name, entry_point in controller.entry_points.items():
        globals()[name] = entry_point


def start_application(module_path: str, application_callback_name: str, settings: dict[str, Any] | None = None):
    try:
        module = import_module(module_path)
    except ModuleNotFoundError as e:
        raise RuntimeError(f"The specified application module {module_path!r} could not be found.") from e

    try:
        application_callback = getattr(module, application_callback_name)
    except AttributeError as e:
        raise RuntimeError(
            f"The specified application callback {application_callback_name!r} could not be found in the "
            f"{module_path!r} module."
        ) from e

    DistributedController.start_application(application_callback(**settings or {}))


@inject
def start_application_using_config(config: ApplicationConfig = dependency()):
    if config.launch is None:
        raise RuntimeError("No launch config exists in schism.config")

    start_application(*config.launch.app.split(":"), settings=config.launch.settings)

def main(argv: list[str]):
    match argv:
        case ["run", "service", str() as service]:
            start_services(service)

        case ["run", str() as application_import] if ":" in application_import:
            start_application(*application_import.split(":"))

        case ["run"]:
            start_application_using_config()

        case _ if "SCHISM_ACTIVE_SERVICE" in os.environ:
            start_services(os.environ["SCHISM_ACTIVE_SERVICE"].strip())

        case _:
            print("""Welcome to Schism!

Schism is a simple service autowiring framework for Python. It allows you to write service oriented applications that
can also be easily be run as monoliths.

Usage:
    schism run service <service>        - Run the given service
    schism run <module>:<entry_point>   - Run the given application""")


if __name__ == "__main__":
    main(["run"] + sys.argv[1:])
