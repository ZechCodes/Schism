import schism.controllers
from schism.bridges import BridgeClientFacade
from schism.middleware import MiddlewareStackBuilder


class Service:
    @classmethod
    def __bevy_constructor__(cls):
        controller = schism.controllers.get_controller()

        # Direct injection for service that exist in the running process
        if controller.is_service_active(cls):
            return cls()

        # Inject a bridge client to remotely access a service that doesn't exist in the running process
        else:
            service_config = controller.get_service_config(cls)
            bridge = service_config.get_bridge_type()
            return BridgeClientFacade(
                bridge_type=bridge,
                service_type=cls,
                config=bridge.config_factory(service_config.bridge),
                middleware_stack=MiddlewareStackBuilder(service_config.get_bridge_middleware()),
            )
