from functools import lru_cache
from importlib import import_module
from typing import Type

from nubby import ConfigModel
from pydantic import BaseModel

from schism.bridges import BaseBridge
from schism.services import Service


class SchismConfigModel(BaseModel, ConfigModel, lax=True):
    def to_dict(self):
        return self.model_dump()


class ServiceConfig(SchismConfigModel, filename="schism.config"):
    name: str
    service: str
    bridge: str

    def get_bridge_type(self) -> Type[BaseBridge]:
        return self._load_object(self.bridge)

    def get_service_type(self) -> Type[Service]:
        return self._load_object(self.service)

    @lru_cache
    def _load_object(self, import_path: str):
        module, cls = import_path.rsplit(".", 1)
        return getattr(import_module(module), cls)


class ServicesConfig(SchismConfigModel, lax=True):
    services: list[ServiceConfig]