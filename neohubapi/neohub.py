# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: LGPL-3.0-or-later

import asyncio
import datetime
import json
import logging
from async_property import async_property, async_cached_property
from types import SimpleNamespace

from neohubapi.enums import ScheduleFormat
from neohubapi.enums import schedule_format_int_to_enum
from neohubapi.neostat import NeoStat


class NeoHub:
    def __init__(self):
        self._logger = logging.getLogger('neohub')
        pass

    async def connect(self, host='Neo-Hub', port='4242'):
        self._host = host
        self._port = port

    async def _send(self, message, expected_reply=None):
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
            reply = json.loads(json_string, object_hook=lambda d: SimpleNamespace(**d))
        except json.decoder.JSONDecodeError as e:
            if expected_reply is None:
                raise(e)
            else:
                return False

        if expected_reply is None:
            return reply
        else:
            if reply.__dict__ == expected_reply:
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
        firmware_version = int(getattr(result, 'firmware version'))
        return firmware_version

    async def get_system(self):
        """
        Get system wide variables
        """
        message = {"GET_SYSTEM": 0}

        data = await self._send(message)
        data.FORMAT = schedule_format_int_to_enum(data.FORMAT)
        data.ALT_TIMER_FORMAT = schedule_format_int_to_enum(data.ALT_TIMER_FORMAT)
        return data

    @async_cached_property
    async def target_temperature_step(self):
        """
        Returns Neohub's target temperature step
        """

        firmware_version = await self.firmware()
        if firmware_version >= 2135:
            return 0.5
        else:
            return 1

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
        Instead of this function it is recommended to use frost on/off commands

        List of affected devices can be restricted using GLOBAL_DEV_LIST command
        """

        message = {"AWAY_ON" if state else "AWAY_OFF": 0}
        reply = {"result": "away on" if state else "away off"}

        result = await self._send(message, reply)
        return result

    async def set_holiday(self, start: datetime.datetime, end: datetime.datetime):
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

        start end end times are converted to datetimes
        """
        message = {"GET_HOLIDAY": 0}

        result = await self._send(message)
        result.start = datetime.datetime.strptime(result.start.strip(), "%a %b %d %H:%M:%S %Y") if result.start else None
        result.end = datetime.datetime.strptime(result.end.strip(), "%a %b %d %H:%M:%S %Y")  if result.end else None
        return result

    async def cancel_holiday(self):
        """
        Cancels holidays and returns to normal schedule
        """

        message = {"CANCEL_HOLIDAY": 0}
        reply = {"result": "holiday cancelled"}

        result = await self._send(message, reply)
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

    async def set_ntp(self, state: bool):
        """
        Enables NTP client on Neohub
        """

        message = {"NTP_ON" if state else "NTP_OFF": 0}
        reply = {"result": "ntp client started" if state else "ntp client stopped"}

        result = await self._send(message, reply)
        return result

    async def set_date(self, date=None):
        """
        Sets current date

        By default, set to current date. Can be optionally passed datetime.datetime object
        """

        if date is None:
            date = datetime.datetime.today()

        message = {"SET_DATE": [date.year, date.month, date.day]}
        reply = {"result": "Date is set"}

        result = await self._send(message, reply)
        return result

    async def set_time(self, time=None):
        """
        Sets current time

        By default, set to current time. Can be optionally passed datetime.datetime object
        """

        if time is None:
            time = datetime.datetime.now()

        message = {"SET_TIME": [time.hour, time.minute]}
        reply = {"result": "time set"}

        result = await self._send(message, reply)
        return result

    async def set_datetime(self, date_time=None):
        """
        Convenience method to set both date and time
        """

        result = await self.set_date(date_time)
        if result:
            result = await self.set_time(date_time)
        return result

    async def manual_dst(self, state: bool):
        """
        Manually enables/disables daylight saving time
        """

        message = {"MANUAL_DST": int(state)}
        reply = {"result": "Updated time"}

        result = await self._send(message, reply)
        return result

    async def set_dst(self, state: bool, region=None):
        """
        Enables/disables automatic DST handling.

        By default it uses UK dates for turning DST on/off.
        Available options for region are UK, EU, NZ.
        """

        message = {"DST_ON" if state else "DST_OFF": 0 if region is None else region}
        reply = {"result": "dst on" if state else "dst off"}

        valid_timezones = ["UK", "EU", "NZ"]
        if region not in valid_timezones:
            return False

        result = await self._send(message, reply)
        return result

    async def identify(self):
        """
        Flashes red LED light
        """

        message = {"IDENTIFY": 0}
        reply = {"result": "flashing led"}

        result = await self._send(message, reply)
        return result

    async def get_live_data(self):
        """
        Returns live data from hub and all devices
        """

        message = {"GET_LIVE_DATA": 0}

        hub_data = await self._send(message)
        devices = hub_data.devices
        delattr(hub_data, "devices")

        thermostat_list = list(filter(lambda device: device.THERMOSTAT, devices))
        thermostats = []
        for thermostat in thermostat_list:
            thermostats.append(NeoStat(self, thermostat))

        return hub_data, thermostats

    async def permit_join(self, name, timeout_s=120):
        """
        Permit new thermostat to join network

        name: new zone will be added with this name
        timeout: duration of discovery mode in seconds

        To actually join network you need to select 01
        from the thermostat's setup menu.
        """

        message = {"PERMIT_JOIN": [timeout_s, name]}
        reply = {"result": "network allows joining"}

        result = await self._send(message)
        return result

    async def set_lock(self, pin: int, devices: [NeoStat]):
        """
        PIN locks thermostats

        PIN is a four digit number
        """

        if pin < 0 or pin > 9999:
            return False

        pins = []
        for x in range(4):
            pins.append(pin % 10)
            pin = pin // 10
        pins.reverse()

        names = [x.name for x in devices]
        message = {"LOCK": [pins, names]}
        reply = {"result": "locked"}

        result = await self._send(message, reply)
        return result

    async def unlock(self, devices: [NeoStat]):
        """
        Unlocks PIN locked thermostats
        """

        names = [x.name for x in devices]
        message = {"UNLOCK": names}
        reply = {"result": "unlocked"}

        result = await self._send(message, reply)
        return result

    async def set_frost(self, state: bool, devices: [NeoStat]):
        """
        Enables or disables Frost mode
        """

        names = [x.name for x in devices]
        message = {"FROST_ON" if state else "FROST_OFF": names}
        reply = {"result": "frost on" if state else "frost off"}

        result = await self._send(message, reply)
        return result

    async def set_temp(self, temperature: int, devices: [NeoStat]):
        """
        Sets the thermostat's temperature

        The temperature will be reset once next comfort level is reached
        """

        names = [x.name for x in devices]
        message = {"SET_TEMP": [temperature, names]}
        reply = {"result": "temperature was set"}

        result = await self._send(message, reply)
        return result

    async def set_diff(self, switching_differential: int, devices: [NeoStat]):
        """
        Sets the thermostat's switching differential

       -1: Undocumented option. Seems to set differential to 204.
        0: 0.5 degrees
        1: 1 degree
        2: 2 degrees
        3: 3 degrees
        """

        names = [x.name for x in devices]
        message = {"SET_DIFF": [switching_differential, names]}
        reply = {"result": "switching differential was set"}

        result = await self._send(message, reply)
        return result

    async def rate_of_change(self, devices: [NeoStat]):
        """
        Returns time in minutes required to change temperature by 1 degree
        """

        names = [x.name for x in devices]
        message = {"VIEW_ROC": names}

        result = await self._send(message)
        return result.__dict__
