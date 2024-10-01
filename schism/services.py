import schism.controllers


class Service:
    @classmethod
    def __bevy_constructor__(cls):
        controller = schism.controllers.get_controller()

        # Direct injection for service that exist in the running process
        if controller.is_service_active(cls):
            return cls()

        # Inject a bridge client to remotely access a service that doesn't exist in the running process
        else:
            config = controller.get_service_config(cls)
            return config.get_bridge_type().create_client(cls)
