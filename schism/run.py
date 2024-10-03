import os
import sys
from importlib import import_module

from schism.controllers import activate, SchismController, start


def launch_entry_point(services: set[str]):
    controller = setup_controller(services)
    setup_entry_points(controller)
    controller.launch()


def setup_controller(services: set[str]) -> SchismController:
    controller = activate(services)
    controller.bootstrap()
    return controller


def setup_entry_points(controller: SchismController):
    for name, entry_point in controller.entry_points.items():
        globals()[name] = entry_point


def start_application():
    module_path, entry_point_name = sys.argv[1].rsplit(".", 1)
    module = import_module(module_path)
    entry_point = getattr(module, entry_point_name)

    start(entry_point())


if len(sys.argv) > 1 and sys.argv[1] in {"--services", "-s"}:
    launch_entry_point(
        {
            service.strip()
            for service in sys.argv[2:]
            if service.strip()
        }
    )

elif "SCHISM_ACTIVE_SERVICES" in os.environ:
    launch_entry_point(
        {
            service.strip()
            for service in os.environ["SCHISM_ACTIVE_SERVICES"].split(",")
            if service.strip()
        }
    )

else:
    start_application()
