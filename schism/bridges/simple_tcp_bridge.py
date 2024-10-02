import asyncio
import hashlib
import os
import pickle
from importlib import import_module
from typing import Type, TYPE_CHECKING

from bevy import get_repository
from pydantic import BaseModel

from .base import BaseBridge, BridgeClient, BridgeServer
from schism.configs import SchismConfigModel

if TYPE_CHECKING:
    from schism.services import Service


def _generate_signature(data: bytes) -> bytes:
    return hashlib.sha256(data + SimpleTCPBridge.SECRET_KEY).hexdigest().encode()


class RequestPayload(BaseModel):
    method: str
    args: tuple
    kwargs: dict


class ResponseBuilder:
    def __init__(self):
        self.status = "success"
        self.data = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.status = "error"
            self.data = {
                "error": exc_val,
                "traceback": exc_tb,
            }

    def set(self, data):
        self.data = data

    def to_dict(self):
        return {
            "status": self.status,
            "data": self.data,
        }


class SimpleTCPConfig(SchismConfigModel):
    host: str
    port: int


class SimpleTCPClient(BridgeClient):
    config: SimpleTCPConfig


class SimpleTCPServer(BridgeServer):
    config: SimpleTCPConfig

    async def launch(self):
        server = await asyncio.start_server(self._handle_request, self.config.host, self.config.port)

        async with server:
            await server.serve_forever()

    async def _handle_request(self, reader, writer):
        with ResponseBuilder() as result:
            length_bytes = await reader.read(4)
            length = int.from_bytes(length_bytes)

            payload = await reader.read(length)
            signature, data = payload[:64], payload[64:]
            if signature != _generate_signature(data):
                raise ValueError("Invalid signature")

            else:
                request: RequestPayload = pickle.loads(data)
                service = get_repository().get(self.service)
                method = getattr(service, request.method)
                result.set(await method(*request.args, **request.kwargs))

        response = pickle.dumps(result.to_dict())
        signature = _generate_signature(response)
        length = len(response) + len(signature)
        writer.write(length.to_bytes(4) + signature + response)

        await writer.drain()
        writer.close()


class SimpleTCPBridge(BaseBridge):
    SECRET_KEY = os.environ.get("SCHISM_SECRET_KEY", "").encode()

    @classmethod
    def create_client(cls, service_type: "Type[Service]", config: SimpleTCPConfig):
        return BridgeClient(service_type, config)

    @classmethod
    def create_server(cls, service_type: "Type[Service]", config: SimpleTCPConfig):
        return SimpleTCPServer(service_type, config)

    @classmethod
    def config_factory(cls, bridge_config: str | dict[str, str | int]) -> SimpleTCPConfig:
        match bridge_config:
            case str() as host_port:
                host, port = host_port.split(":")
                return SimpleTCPConfig(host=host, port=int(port))

            case {"host": str() as host, "port": int() as port}:
                return SimpleTCPConfig(host=host, port=port)

            case _:
                raise ValueError(f"Invalid bridge configuration: {bridge_config!r}")
