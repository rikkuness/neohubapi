# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: LGPL-3.0-or-later

import asyncio
import json

class NeoHub:
    def __init__(self):
        pass


    async def connect(self, host='Neo-Hub', port='4242'):
        self._reader, self._writer = await asyncio.open_connection(host, port)


    async def send(self, message):
        encoded_message = bytearray(json.dumps(message) + "\0\r", "utf-8")
        self._writer.write(encoded_message)
        await self._writer.drain()

        data = await self._reader.read(4096)
        json_string = data.decode('utf-8')
        return json.loads(json_string)


    async def firmware(self):
        message = {"FIRMWARE": 0}
        result = await self.send(message)
        return result['firmware version']
