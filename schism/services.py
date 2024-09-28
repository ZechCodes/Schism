from schism.controllers import get_controller


class Service:
    @classmethod
    def __bevy_constructor__(cls):
        return get_controller().wiring_strategy.get_facade(cls)
