# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: LGPL-3.0-or-later

import asyncio
import json
import logging

from system import System

class NeoHub:
    def __init__(self):
        self._logger = logging.getLogger('neohub')
        pass


    async def connect(self, host='Neo-Hub', port='4242'):
        self._host = host
        self._port = port


    async def _send(self, message):
        reader, writer = await asyncio.open_connection(self._host, self._port)
        encoded_message = bytearray(json.dumps(message) + "\0\r", "utf-8")
        self._logger.debug(f"Sending message: {encoded_message}")
        writer.write(encoded_message)
        await writer.drain()

        data = await reader.readuntil(b'\0')
        data = data.strip(b'\0')
        json_string = data.decode('utf-8')
        self._logger.debug(f"Received message: {json_string}")

        writer.close()
        await writer.wait_closed()

        return json.loads(json_string)


    async def firmware(self):
        """
        NeoHub firmware version
        """
        message = {"FIRMWARE": 0}

        result = await self._send(message)
        firmware_version = int(result['firmware version'])
        return firmware_version



    async def get_system(self):
        """
        Get system wide variables

        Returns System object
        """
        message = {"GET_SYSTEM": 0}

        data = await self._send(message)
        system_data = System(data)
        return system_data


    async def reset(self):
        """
        Reboot neohub

        Returns True if Restart is initiated
        """
        message = {"RESET": 0}

        firmware_version = await self.firmware()
        result = ""
        if firmware_version >= 2027:
            result = await self._send(message)
            return result['Restarting'] == 1
        else:
            return False

    async def set_channel(self, channel: int):
        """
        Set ZigBee channel.

        Only channels 11, 14, 15, 19, 20, 24, 25 are allowed.
        """

        message = {"SET_CHANNEL": channel}

        result = await self._send(message)
