from typing import Type

from bevy import Repository

import schism.controllers
from schism.bridges import BridgeClientFacade
from schism.middleware import MiddlewareContext


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
                middleware_stack=service_config.get_bridge_middleware(),
            )


async def wait_for(service: Type[Service], *, timeout: float = 5.0):
    """Waits for a service to be ready to accept requests. This returns immediately if the service is not remote."""
    match Repository.get_repository().get(service):
        case BridgeClientFacade() as client:
            await client.wait_for_server(timeout=timeout)

        case _:
            pass
