import os
import sys
from importlib import import_module

from schism.controllers import activate, SchismController, start


def launch_entry_point():
    controller = setup_controller()
    setup_entry_points(controller)
    controller.launch()


def setup_controller() -> SchismController:
    controller = activate()
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


if "SCHISM_ACTIVE_SERVICES" in os.environ:
    launch_entry_point()

else:
    start_application()
