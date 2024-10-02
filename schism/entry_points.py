from schism.controllers import EntryPointController, set_controller


controller = EntryPointController()
set_controller(controller)
controller.bootstrap()


for  name, entry_point in controller.entry_points.items():
    globals()[name] = entry_point
