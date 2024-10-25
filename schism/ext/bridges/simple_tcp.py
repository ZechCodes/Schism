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
          type: schism.ext.bridges.simple_tcp:SimpleTCP
          serve_on: 0.0.0.0:1234

It is also possible to configure the client separately:

    services:
      - name: example
        service: example:Example
        bridge:
          type: schism.ext.bridges.simple_tcp:SimpleTCP
          serve_on: 0.0.0.0:1234
          client: example.com:4321


The Simple TCP Bridge uses a custom protocol on top of TCP. The version 0 protocol uses the following structure:

Usage          | Size (Bytes)   | Data Type
---------------|----------------|--------------------
Version        |              2 | int (big endian)
Content Length |              4 | int (big endian)
Signature      |             64 | bytes (sha256 hash)
Content        |      Arbitrary | pickle
---------------|----------------|--------------------
"""
import asyncio
import contextlib
import hashlib
import os
import pickle
from asyncio import StreamReader, StreamWriter
from functools import lru_cache

from schism.bridges import BaseBridge, BridgeClient, BridgeServer, BridgeServiceFacade, MethodCallPayload, ResultPayload
from schism.configs import SchismConfigModel
from schism.controllers import get_controller
from schism.middleware import MiddlewareStackBuilder


SIMPLE_TCP_VERSION_SUPPORTED = 0


def _generate_signature(data: bytes) -> bytes:
    return hashlib.sha256(data + SimpleTCP.SECRET_KEY).hexdigest().encode()


class SimpleTCPConfig(SchismConfigModel, lax=True):
    serve_on: str
    client: str


async def connect(host: str, port: int) -> tuple[StreamReader, StreamWriter]:
    try:
        return await asyncio.open_connection(host, port)
    except OSError as e:
        raise RuntimeError(f"Unable to connect to service on {host}:{port}") from e


async def read_version(reader: StreamReader) -> int:
    """Reads 2 bytes and converts them to a big endian int."""
    version = await reader.read(2)
    return int.from_bytes(version, byteorder="big")


async def read(reader: StreamReader) -> ResultPayload | MethodCallPayload:
    """When reading from a TCP connection first read 2 bytes to get the version, then 4 bytes to get the content length.
    Next read the 64 byte signature. Next read the content and validate the signature matches. If it does then it is
    safe to load the payload pickle.
    """
    version = await read_version(reader)
    if version != SIMPLE_TCP_VERSION_SUPPORTED:
        raise RuntimeError(
            f"Only SimpleTCP protocol version {SIMPLE_TCP_VERSION_SUPPORTED} is supported, detected "
            f"version {version}."
        )

    length_bytes = await reader.read(4)
    signature = await reader.read(64)

    length = int.from_bytes(length_bytes, byteorder="big")
    payload = await reader.read(length)
    if signature != _generate_signature(payload):
        raise ValueError(f"Received an invalid signature")

    return pickle.loads(payload)


async def send(data: ResultPayload | MethodCallPayload, writer: StreamWriter):
    """When writing to a TCP connection first write the 2 byte protocol version then the 4 byte content length of the
    pickled data, then the 64 byte signature, and finally write the pickle."""
    payload = pickle.dumps(data)
    writer.write(SIMPLE_TCP_VERSION_SUPPORTED.to_bytes(2, byteorder="big"))
    writer.write(len(payload).to_bytes(4, byteorder="big"))
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

    async def call_async_method(self, payload: MethodCallPayload):
        reader, writer = await connect(self.host, self.port)
        with contextlib.closing(writer):
            await send(payload, writer)
            return await read(reader)


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
            call_payload: MethodCallPayload = await read(reader)
            result = await self.call_async_method(call_payload)
            await send(result, writer)


class SimpleTCP(BaseBridge):
    SECRET_KEY = os.environ.get("SCHISM_TCP_BRIDGE_SECRET", "").encode()

    @classmethod
    def create_client(cls, config: SimpleTCPConfig) -> SimpleTCPClient:
        return SimpleTCPClient(config)

    @classmethod
    def create_server(cls, config: SimpleTCPConfig, service_facade: BridgeServiceFacade) -> SimpleTCPServer:
        server = SimpleTCPServer(config, service_facade)
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
