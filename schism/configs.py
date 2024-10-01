from functools import lru_cache
from importlib import import_module
from typing import Type, TYPE_CHECKING

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
    bridge: str

    def get_bridge_type(self) -> "Type[bridges.BaseBridge]":
        return self._load_object(self.bridge)

    def get_service_type(self) -> "Type[services.Service]":
        return self._load_object(self.service)

    @staticmethod
    @lru_cache
    def _load_object(import_path: str):
        module, cls = import_path.rsplit(".", 1)
        return getattr(import_module(module), cls)


class ServicesConfig(SchismConfigModel, filename="schism.config"):
    services: list[ServiceConfig]
