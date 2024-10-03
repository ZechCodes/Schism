from functools import lru_cache
from importlib import import_module
from typing import Type, TYPE_CHECKING, Any

from nubby import ConfigModel
from pydantic import BaseModel

if TYPE_CHECKING:
    import schism.bridges as bridges
    import schism.services as services


class SchismConfigModel(BaseModel, ConfigModel, lax=True):
    def to_dict(self):
        return self.model_dump()


class ServiceConfig(SchismConfigModel, lax=True):
    name: str
    service: str
    bridge: str | dict[str, Any]

    def get_bridge_type(self) -> "Type[bridges.BaseBridge]":
        match self.bridge:
            case str() as bridge:
                pass

            case {"bridge": str() as bridge}:
                pass

            case _:
                raise ValueError(f"Invalid bridge configuration for service {self.name}")

        return self._load_object(bridge)

    def get_service_type(self) -> "Type[services.Service]":
        return self._load_object(self.service)

    def get_bridge_config(self) -> Any:
        return self.get_bridge_type().config_factory(self.bridge)

    @staticmethod
    @lru_cache
    def _load_object(import_path: str):
        module, cls = import_path.rsplit(".", 1)
        return getattr(import_module(module), cls)


class ServicesConfig(SchismConfigModel, filename="schism.config"):
    services: list[ServiceConfig]
