import threading

from schism.wiring_strategies import BaseWiringStrategy, DirectWiringStrategy


_global_controller = None
_global_controller_write_lock = threading.Lock()


class SchismController:
    def __init__(self):
        self._wiring_strategy = DirectWiringStrategy()
        self._wiring_strategy_write_lock = threading.Lock()

    @property
    def wiring_strategy(self) -> BaseWiringStrategy:
        with self._wiring_strategy_write_lock:
            return self._wiring_strategy

    @wiring_strategy.setter
    def wiring_strategy(self, value: BaseWiringStrategy):
        with self._wiring_strategy_write_lock:
            self._wiring_strategy = value


def get_controller() -> SchismController:
    global _global_controller

    with _global_controller_write_lock:
        if _global_controller is None:
            _global_controller = SchismController()

        return _global_controller


def set_controller(controller: SchismController):
    global _global_controller

    with _global_controller_write_lock:
        _global_controller = controller
