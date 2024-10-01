from typing import Any

from schism.controllers import has_controller, EntryPointController, set_controller

__runtime_entry_points = {}


def __validate_name(name: str):
     if not name.isidentifier():
         raise RuntimeError(f"Entry point names must be valid Python identifiers: {name!r} (invalid)")

     if name.startswith("_"):
         raise RuntimeError(f"Entry point names cannot start with '_': {name!r} (invalid)")

     if name in vars():
         raise RuntimeError(f"Entry point name is not available: {name!r} (not available)")


def create_entry_point(name: str, value: Any):
    __validate_name(name)
    __runtime_entry_points[name] = value
    globals()[name] = value


def delete_entry_point(name: str):
    __validate_name(name)
    del __runtime_entry_points[name]
    del globals()[name]


def clear_all_entry_points():
    for name in __runtime_entry_points:
        del globals()[name]

    __runtime_entry_points.clear()


## Bootstrap if the application is being launched through an entry point
if not has_controller():
    controller = EntryPointController()
    set_controller(controller)
    controller.launch()
