import asyncio
import json
import pytest
import time
from types import SimpleNamespace

import neohubapi

HOST = 'localhost'


class FakeProtocol(asyncio.Protocol):
    """A simple asyncio protocol that returns a given message."""
    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        input = data.decode()
        # self.server and self.handler are set by create_protocol below.
        self.server.inputs.append(input)
        output = self.handler(input).encode() + b'\0'
        self.transport.write(output)
        self.transport.close()


class FakeServer:
    def __init__(self, loop, port):
        self.port = port
        self.loop = loop
        self.inputs = []

    async def start(self, handler):
        def create_protocol():
            fake_protocol = FakeProtocol()
            fake_protocol.handler = handler
            fake_protocol.server = self
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
    assert len(fakeserver.inputs) == 1  # by default there are no retries.

    # expected_reply is not set, function raises exception.
    with pytest.raises(json.decoder.JSONDecodeError):
        await hub._send('test')


@pytest.mark.asyncio
async def test_send_timeout(fakeserver):
    def handler(input):
        time.sleep(0.2)
        return '{"message": "ok"}'
    await fakeserver.start(handler)

    hub = neohubapi.neohub.NeoHub(host=HOST, port=fakeserver.port, request_timeout=0.1)

    with pytest.raises(asyncio.TimeoutError):
        await hub._send('test')


@pytest.mark.asyncio
async def test_send_retries(fakeserver):
    def handler(input):
        return '{"message": "error"}'
    await fakeserver.start(handler)

    hub = neohubapi.neohub.NeoHub(
        host=HOST, port=fakeserver.port, request_attempts=3, request_timeout=0.1)

    # after 3 attempts the result is still incorrect.
    assert await hub._send('test', {'message': 'ok'}) is False
    assert len(fakeserver.inputs) == 3
