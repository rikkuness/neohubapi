# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: LGPL-3.0-or-later

import asyncio
import datetime
import json
import logging

from enums import ScheduleFormat
from system import System
from holiday import Holiday


class NeoHub:
    def __init__(self):
        self._logger = logging.getLogger('neohub')
        pass


    async def connect(self, host='Neo-Hub', port='4242'):
        self._host = host
        self._port = port


    async def _send(self, message, expected_reply = None):
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

        try:
            reply = json.loads(json_string)
        except json.decoder.JSONDecodeError:
            if expected_reply is None:
                raise(e)
            else:
                return False

        if expected_reply is None:
            return reply
        else:
            if reply == expected_reply:
                return True
            else:
                self._logger.error(f"Unexpected reply: {reply}")
                return False


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
        reply = {"Restarting": 1}

        firmware_version = await self.firmware()
        result = ""
        if firmware_version >= 2027:
            result = await self._send(message, reply)
            return result
        else:
            return False


    async def set_channel(self, channel: int):
        """
        Set ZigBee channel.

        Only channels 11, 14, 15, 19, 20, 24, 25 are allowed.
        """

        message = {"SET_CHANNEL": channel}
        reply = {"result": "Trying to change channel"}

        result = await self._send(message, reply)
        return result


    async def set_temp_format(self, temp_format: str):
        """
        Set temperature format to C or F
        """

        message = {"SET_TEMP_FORMAT": temp_format}
        reply = {"result": f"Temperature format set to {temp_format}"}

        result = await self._send(message, reply)
        return result


    async def set_format(self, format: ScheduleFormat):
        """
        Sets schedule format

        Format is specified using ScheduleFormat enum:
        """

        message = {"SET_FORMAT": format}
        reply = {"result": "Format was set"}

        result = await self._send(message, reply)
        return result


    async def set_away(self, state: bool):
        """
        Enables away mode for all devices.

        Puts thermostats into frost mode and timeclocks are set to off.
        Instead of this function it is recommended to use frost on/off commands.
        """

        message = {"AWAY_ON" if state else "AWAY_OFF": 0}
        reply = {"result": "away on" if state else "away off"}

        result = await self._send(message, reply)
        return result


    async def holiday(self, start: datetime.datetime, end: datetime.datetime):
        """
        Sets holiday mode.

        start: beginning of holiday
        end: end of holiday
        """

        message = {"HOLIDAY": [start.strftime("%H%M%S%d%m%Y"), end.strftime("%H%M%S%d%m%Y")]}

        result = await self._send(message)
        return result

    async def get_holiday(self):
        """
        Get list of holidays

        Returns Holiday object
        """
        message = {"GET_HOLIDAY": 0}

        result = await self._send(message)
        return Holiday(result)


    async def cancel_holiday(self):
        """
        Cancels holidays and returns to normal schedule
        """

        message = {"CANCEL_HOLIDAY": 0}
        reply = {"result": "holiday cancelled"}

        result = await self._send(message, reply)
        return result


    async def get_zones(self):
        """
        Returns list of zones and their ids

        {"zone1": 1}
        """

        message = {"GET_ZONES": 0}

        result = await self._send(message)
        return result


    async def get_devices(self):
        """
        Returns list of devices

        {"result": ["device1"]}
        """

        message = {"GET_DEVICES": 0}

        result = await self._send(message)
        return result


    async def get_device_list(self, zone: str):
        """
        Returns list of devices associated with zone
        """

        message = {"GET_DEVICE_LIST": zone}

        result = await self._send(message)
        if 'error' in result:
            return False
        else:
            return result[zone]


    async def devices_sn(self):
        """
        Returns serial numbers of attached devices

        {'name': [id, 'serial', 1], ...}
        """

        message = {"DEVICES_SN": 0}

        result = await self._send(message)
        return result
