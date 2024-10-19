"""The Simple TCP Bridge provides a somewhat secure TCP client and server implementation for calling methods of a
service. Parameters, return values, and exceptions are passed using pickles and are secured by signing each payload
using a SHA256 hash salted with a secret key.

The secret key can be changed by setting the SCHISM_TCP_BRIDGE_SECRET environment variable. This should provide some
assurance that the pickles being passed are safe.

In the schism.config file it is possible to set the host and port that a service's TCP bridge server should be exposed
on and that the client should connect to.

Here's an example yaml config:

    services:
      - name: example
        service: example:Example
        bridge:
          type: schism.bridges.simple_tcp_bridge:SimpleTCPBridge
          serve_on: 0.0.0.0:1234

It is also possible to configure the client separately:

    services:
      - name: example
        service: example:Example
        bridge:
          type: schism.bridges.simple_tcp_bridge:SimpleTCPBridge
          serve_on: 0.0.0.0:1234
          client: example.com:4321
"""
import asyncio
import contextlib
import hashlib
import os
import pickle
from asyncio import StreamReader, StreamWriter
from functools import lru_cache, partial
from typing import Any, Type, TYPE_CHECKING

from bevy import get_repository
from pydantic import BaseModel

from .base import BaseBridge, BridgeClient, BridgeServer, RemoteError
from .bridge_helpers import ResponseBuilder
from schism.configs import SchismConfigModel
from schism.controllers import get_controller

if TYPE_CHECKING:
    from schism.services import Service


def _generate_signature(data: bytes) -> bytes:
    return hashlib.sha256(data + SimpleTCPBridge.SECRET_KEY).hexdigest().encode()


class RequestPayload(BaseModel):
    method: str
    args: tuple
    kwargs: dict


class SimpleTCPConfig(SchismConfigModel, lax=True):
    serve_on: str
    client: str


async def connect(host: str, port: int) -> tuple[StreamReader, StreamWriter]:
    try:
        return await asyncio.open_connection(host, port)
    except OSError as e:
        raise RuntimeError(f"Unable to connect to service on {host}:{port}") from e


async def read[TResponse: (dict[str, Any], RequestPayload)](reader: StreamReader) -> TResponse:
    """When reading from a TCP connection first read 4 bytes to get the content length. Next read the 64 byte signature.
    Next read the content and validate the signature matches. If it does then it is safe to load the payload pickle.
    """
    length_bytes = await reader.read(4)
    signature = await reader.read(64)

    length = int.from_bytes(length_bytes)
    payload = await reader.read(length)
    if signature != _generate_signature(payload):
        raise ValueError(f"Received an invalid signature")

    return pickle.loads(payload)


async def send(data: Any, writer: StreamWriter):
    """When writing to a TCP connection first write the 4 byte content length of the pickled data, then the 64 byte
    signature, and finally write the pickle."""
    payload = pickle.dumps(data)
    writer.write(len(payload).to_bytes(4))
    writer.write(_generate_signature(payload))
    writer.write(payload)
    await writer.drain()


class SimpleTCPClient(BridgeClient):
    config: SimpleTCPConfig

    @property
    @lru_cache
    def host(self) -> str:
        return (
            self.config.client
            if self.config.client
            else self.config.serve_on
        ).split(":")[0]

    @property
    def port(self) -> int:
        return int(
            (
                self.config.client
                if self.config.client
                else self.config.serve_on
            ).split(":")[1]
        )

    def __getattr__(self, item):
        return partial(self.__make_request, item)

    async def __make_request(self, method, *args, **kwargs):
        reader, writer = await connect(self.host, self.port)
        with contextlib.closing(writer):
            await send(
                RequestPayload(method=method, args=args, kwargs=kwargs),
                writer,
            )
            match await read(reader):
                case {"status": "error", "data": data}:
                    raise data["error"] from RemoteError(
                        f"\n"
                        f"{''.join(data['traceback'])}\n"
                        f"---------------------------------------------\n"
                        f"The above stacktrace is from a remote service\n"
                        f"---------------------------------------------"
                    )

                case {"data": data}:
                    return data

                case _:
                    raise RuntimeError("Impossible State, server response must be malformed.")


class SimpleTCPServer(BridgeServer):
    config: SimpleTCPConfig

    @property
    @lru_cache
    def host(self) -> str:
        return self.config.serve_on.split(":")[0]

    @property
    @lru_cache
    def port(self) -> int:
        return int(self.config.serve_on.split(":")[1])

    async def launch(self):
        server = await asyncio.start_server(self._handle_request, self.host, self.port)

        async with server:
            await server.serve_forever()

    async def _handle_request(self, reader, writer):
        with contextlib.closing(writer):
            with ResponseBuilder() as result:
                request: RequestPayload = await read(reader)

                service = get_repository().get(self.service)
                method = getattr(service, request.method)

                result.set(await method(*request.args, **request.kwargs))

            await send(result.to_dict(), writer)


class SimpleTCPBridge(BaseBridge):
    SECRET_KEY = os.environ.get("SCHISM_TCP_BRIDGE_SECRET", "").encode()

    @classmethod
    def create_client(cls, service_type: "Type[Service]", config: SimpleTCPConfig):
        return SimpleTCPClient(service_type, config)

    @classmethod
    def create_server(cls, service_type: "Type[Service]", config: SimpleTCPConfig):
        server = SimpleTCPServer(service_type, config)
        get_controller().add_launch_task(server.launch())
        return server

    @classmethod
    def config_factory(cls, bridge_config: str | dict[str, str | int]) -> SimpleTCPConfig:
        match bridge_config:
            case str() as serve_on:
                return SimpleTCPConfig(serve_on=serve_on, client=serve_on)

            case {"serve_on": str() as serve_on, "client": str() as client}:
                return SimpleTCPConfig(serve_on=serve_on, client=client)

            case {"serve_on": str() as serve_on}:
                return SimpleTCPConfig(serve_on=serve_on, client=serve_on)

            case _:
                raise ValueError(f"Invalid bridge configuration for {cls.__name__}: {bridge_config}")
