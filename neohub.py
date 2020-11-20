# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: LGPL-3.0-or-later

import asyncio
import json
import logging

class NeoHub:
    def __init__(self):
        self._logger = logging.getLogger('neohub')
        self._firmware_version = 0
        pass


    async def connect(self, host='Neo-Hub', port='4242'):
        self._reader, self._writer = await asyncio.open_connection(host, port)
        self._firmware_version = await self._firmware()


    async def send(self, message):
        encoded_message = bytearray(json.dumps(message) + "\0\r", "utf-8")
        self._writer.write(encoded_message)
        await self._writer.drain()

        data = await self._reader.read(4096)
        json_string = data.decode('utf-8')
        self._logger.debug(f"Received message: {json_string}")
        return json.loads(json_string)

    def firmware(self):
        return self._firmware_version

    async def firmware(self):
        return self._firmware_version

    async def _firmware(self):
        '''
        NeoHub firmware version
        '''

        message = {"FIRMWARE": 0}
        result = await self.send(message)
        firmware_version = int(result['firmware version'])
        return firmware_version
