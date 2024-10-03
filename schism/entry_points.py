from schism.controllers import activate, SchismController


def setup_controller() -> SchismController:
    controller = activate()
    controller.bootstrap()
    return controller


def setup_entry_points(controller: SchismController):
    for name, entry_point in controller.entry_points.items():
        globals()[name] = entry_point


def launch():
    controller = setup_controller()
    setup_entry_points(controller)
    controller.launch()


launch()
