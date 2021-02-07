import asyncio
import json
import pytest
from types import SimpleNamespace

import neohubapi

HOST = 'localhost'


class FakeProtocol(asyncio.Protocol):
    """A simple asyncio protocol that returns a given message."""
    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        input = data.decode()
        # self.handler() is set by create_protocol below.
        output = self.handler(input).encode() + b'\0'
        self.transport.write(output)
        self.transport.close()


class FakeServer:
    def __init__(self, loop, port):
        self.port = port
        self.loop = loop

    async def start(self, handler):
        def create_protocol():
            fake_protocol = FakeProtocol()
            fake_protocol.handler = handler
            return fake_protocol
        self.server = await self.loop.create_server(create_protocol, HOST, self.port)

    async def close(self):
        server, self.server = self.server, None
        server.close()
        await server.wait_closed()


@pytest.fixture()
async def fakeserver(event_loop, unused_tcp_port):
    """Create a fakeserver pytest fixture."""
    server = FakeServer(event_loop, unused_tcp_port)
    yield server
    await server.close()


@pytest.mark.asyncio
async def test_send_valid(fakeserver):
    def handler(input):
        return '{"message": "ok"}'
    await fakeserver.start(handler)

    hub = neohubapi.neohub.NeoHub(host=HOST, port=fakeserver.port)

    # expected_reply is not set: function returns the message.
    assert SimpleNamespace(message='ok') == await hub._send('test')

    # Response equals to expected_reply: function returns True.
    assert await hub._send('test', {'message': 'ok'}) is True

    # Response not equal to expected_reply: function returns False.
    assert await hub._send('test', {'message': 'not ok'}) is False


@pytest.mark.asyncio
async def test_send_invalid_json(fakeserver):
    def handler(input):
        return '{"message": not valid json"}'
    await fakeserver.start(handler)

    hub = neohubapi.neohub.NeoHub(host=HOST, port=fakeserver.port)

    # expected_reply is set, function returns False.
    assert await hub._send('test', {'message': 'ok'}) is False

    # expected_reply is not set, function raises exception.
    with pytest.raises(json.decoder.JSONDecodeError):
        await hub._send('test')
