import sys
import pathlib
from functools import lru_cache
from importlib import import_module
from typing import Type, TYPE_CHECKING, Any, TypedDict

from nubby import ConfigModel
from pydantic import BaseModel


MAIN_MODULE_NAME = pathlib.Path(getattr(sys.modules["__main__"], "__file__", "")).stem or None

if TYPE_CHECKING:
    import schism.bridges as bridges
    import schism.services as services


class BridgeSettings(TypedDict):
    type: str


class SchismConfigModel(BaseModel, ConfigModel, lax=True):
    """Base model config that implements the correct interface for serialization."""
    def to_dict(self):
        return self.model_dump()


class LaunchConfig(SchismConfigModel, lax=True):
    """Config model for settings related to launching an app with the "schism run" command. "app" should be a module
    import path and attribute name separated by a colon. "settings" is an optional dictionary of string keys that are
    valid Python identifiers with any kind of value, these are passed as keyword arguments to the callable attribute.

    Example:

        config = LaunchConfig(app="example:example_function", settings={"example": 1234})
    """
    app: str
    settings: dict[str, Any] | None = None


class ServiceConfig(SchismConfigModel, lax=True):
    """Config model for a service.
    - "name" is used for referencing the service in commands
    - "service" is the module import path and class name, separated by a colon, for the service class
    - "bridge" is either the module import path and class name, separated by a colon, for the bridge class, or a
    dictionary with a "type" key that is the bridge class string. All other keys in the dictionary are passed to the
    bridge types "config_factory" class method to generate teh config that is passed to the bridge client and server."""
    name: str
    service: str
    bridge: str | BridgeSettings

    def get_bridge_type(self) -> "Type[bridges.BaseBridge]":
        """Finds the module for the bridge type and gets the bridge type from the module."""
        return self._load_object(self._get_bridge_locator())

    def get_service_type(self) -> "Type[services.Service]":
        """Finds the module for the service type and gets the service type from the module."""
        return self._load_object(self.service)

    def get_bridge_config(self) -> Any:
        """Passes the bridge config to the bridge type's config factory method and passes back its return."""
        return self.get_bridge_type().config_factory(self.bridge)

    def _get_bridge_locator(self) -> str:
        match self.bridge:
            case str() as bridge:
                return bridge

            case {"type": str() as bridge}:
                return bridge

            case _:
                raise ValueError(f"Invalid bridge configuration for service {self.name}")

    @staticmethod
    @lru_cache
    def _load_object(import_path: str):
        module_path, attr = import_path.rsplit(":", 1)
        module = sys.modules["__main__"] if module_path == MAIN_MODULE_NAME else import_module(module_path)
        return getattr(module, attr)


class ApplicationConfig(SchismConfigModel, filename="schism.config"):
    """Config model for an application stored in the schism.config file. By default, this file can be a JSON, TOML, or
    YAML file. Schism only checks the working directory for this file."""
    services: list[ServiceConfig]
    launch: LaunchConfig | None = None
