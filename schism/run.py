import os
import sys
from importlib import import_module

from schism.controllers import activate, SchismController, start


def launch_services(service: str):
    controller = setup_controller(service)
    setup_entry_points(controller)
    controller.launch()


def setup_controller(service: str) -> SchismController:
    controller = activate(service)
    controller.bootstrap()
    return controller


def setup_entry_points(controller: SchismController):
    for name, entry_point in controller.entry_points.items():
        globals()[name] = entry_point


def start_application(module_path: str, entry_point_name: str):
    try:
        module = import_module(module_path)
    except ModuleNotFoundError as e:
        raise RuntimeError(f"The specified entrypoint module {module_path!r} could not be found.") from e

    try:
        entry_point_callback = getattr(module, entry_point_name)
    except AttributeError as e:
        raise RuntimeError(f"The specified entrypoint callback {entry_point_name!r} could not be found in the {module_path!r} module.") from e

    start(entry_point_callback())


def main():
    match sys.argv[1:]:
        case ("run", "service", str() as service):
            launch_services(service)

        case ("run", entry_point) if ":" in entry_point:
            start_application(*entry_point.rsplit(":", 1))

        case _ if "SCHISM_ACTIVE_SERVICE" in os.environ:
            launch_services(os.environ["SCHISM_ACTIVE_SERVICE"].strip())

        case _:
            print("""Welcome to Schism!

Schism is a simple service autowiring framework for Python. It allows you to write service oriented applications that
can also be easily be run as monoliths.

Usage:
    schism run service <service>        - Run the given service
    schism run <module>:<entry_point>   - Run the given application""")


main()
