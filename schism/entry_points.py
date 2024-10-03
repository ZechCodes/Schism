from schism.controllers import EntryPointController, set_controller, SchismController


def setup_controller() -> SchismController:
    controller = EntryPointController()
    set_controller(controller)
    controller.bootstrap()
    return controller


def setup_entry_points(controller: SchismController):
    for name, entry_point in controller.entry_points.items():
        globals()[name] = entry_point


def launch():
    controller = setup_controller()
    setup_entry_points(controller)


launch()
