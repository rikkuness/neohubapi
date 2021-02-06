# SPDX-FileCopyrightText: 2020-2021 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-FileCopyrightText: 2021 Dave O'Connor <daveoc@google.com>
# SPDX-License-Identifier: LGPL-3.0-or-later

import asyncio
import datetime
import json
import logging
import socket
from async_property import async_cached_property
from types import SimpleNamespace

from neohubapi.enums import ScheduleFormat
from neohubapi.enums import schedule_format_int_to_enum
from neohubapi.neostat import NeoStat


class Error(Exception):
    pass


class NeoHubUsageError(Error):
    pass


class NeoHubConnectionError(Error):
    pass


class NeoHub:
    def __init__(self, host='Neo-Hub', port=4242, request_timeout=5, request_attempts=1):
        self._logger = logging.getLogger('neohub')
        self._host = host
        self._port = port
        self._request_timeout = request_timeout
        self._request_attempts = request_attempts

    async def _send_message(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, message: str):
        encoded_message = bytearray(json.dumps(message) + "\0\r", "utf-8")
        self._logger.debug(f"Sending message: {encoded_message}")
        writer.write(encoded_message)
        await writer.drain()

        data = await reader.readuntil(b'\0')

        writer.close()
        await writer.wait_closed()

        data = data.strip(b'\0')
        return data

    async def _send(self, message, expected_reply=None):
        last_exception = None
        for attempt in range(1, self._request_attempts+1):
            try:
                reader, writer = await asyncio.open_connection(self._host, self._port)
                data = await asyncio.wait_for(
                        self._send_message(reader, writer, message), timeout=self._request_timeout)
                json_string = data.decode('utf-8')
                self._logger.debug(f"Received message: {json_string}")
                reply = json.loads(json_string, object_hook=lambda d: SimpleNamespace(**d))

                if expected_reply is None:
                    return reply
                if reply.__dict__ == expected_reply:
                    return True
                self._logger.error(f"[{attempt}] Unexpected reply: {reply}")
            except (socket.gaierror, ConnectionRefusedError) as e:
                last_exception = NeoHubConnectionError(e)
                self._logger.error(f"[{attempt}] Could not connect to NeoHub at {self._host}: {e}")
            except asyncio.TimeoutError as e:
                last_exception = e
                self._logger.error(f"[{attempt}] Timed out while sending a message to {self._host}")
                if writer is not None:
                    writer.close()
            except json.decoder.JSONDecodeError as e:
                last_exception = e
                self._logger.error(f"[{attempt}] Could not decode JSON: {e}")
            # Wait for 1/2 of the timeout value before retrying.
            if self._request_attempts > 1 and attempt < self._request_attempts:
                await asyncio.sleep(self._request_timeout / 2)

        if expected_reply is None and last_exception is not None:
            raise(last_exception)
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

        try:
            message = {"SET_CHANNEL": int(channel)}
        except ValueError:
            raise NeoHubUsageError('channel must be a number')

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

    async def set_format(self, sched_format: ScheduleFormat):
        """
        Sets schedule format

        Format is specified using ScheduleFormat enum:
        """
        if not isinstance(sched_format, ScheduleFormat):
            raise NeoHubUsageError('sched_format must be a ScheduleFormat')

        message = {"SET_FORMAT": sched_format.value}
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
        for datetime_arg in (start, end):
            if not isinstance(datetime_arg, datetime.datetime):
                raise NeoHubUsageError('start and end must be datetime.datetime objects')

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
        result.start = datetime.datetime.strptime(
                result.start.strip(), "%a %b %d %H:%M:%S %Y") if result.start else None
        result.end = datetime.datetime.strptime(
                result.end.strip(), "%a %b %d %H:%M:%S %Y") if result.end else None
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

    async def set_date(self, date: datetime.datetime = datetime.datetime.today()):
        """
        Sets current date

        By default, set to current date. Can be optionally passed datetime.datetime object
        """

        message = {"SET_DATE": [date.year, date.month, date.day]}
        reply = {"result": "Date is set"}

        result = await self._send(message, reply)
        return result

    async def set_time(self, time: datetime.datetime = datetime.datetime.now()):
        """
        Sets current time

        By default, set to current time. Can be optionally passed datetime.datetime object
        """
        message = {"SET_TIME": [time.hour, time.minute]}
        reply = {"result": "time set"}

        result = await self._send(message, reply)
        return result

    async def set_datetime(self, date_time: datetime.datetime = datetime.datetime.now()):
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

    async def set_dst(self, state: bool, region: str = None):
        """
        Enables/disables automatic DST handling.

        By default it uses UK dates for turning DST on/off.
        Available options for region are UK, EU, NZ.
        """

        message = {"DST_ON" if state else "DST_OFF": 0 if region is None else region}
        reply = {"result": "dst on" if state else "dst off"}

        valid_timezones = ["UK", "EU", "NZ"]
        if region not in valid_timezones:
            raise NeoHubUsageError(f'region must be in {valid_timezones}')

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

        thermostat_list = list(filter(lambda device: hasattr(device, 'THERMOSTAT') and device.THERMOSTAT, devices))
        timeclock_list = list(filter(lambda device: hasattr(device, 'TIMECLOCK') and device.TIMECLOCK, devices))

        thermostats = []
        timeclocks = []
        for thermostat in thermostat_list:
            thermostats.append(NeoStat(self, thermostat))

        for timeclock in timeclock_list:
            timeclocks.append(NeoStat(self, timeclock))

        devices = {}
        devices['thermostats'] = thermostats
        devices['timeclocks'] = timeclocks

        return hub_data, devices

    async def permit_join(self, name, timeout_s: int = 120):
        """
        Permit new thermostat to join network

        name: new zone will be added with this name
        timeout: duration of discovery mode in seconds

        To actually join network you need to select 01
        from the thermostat's setup menu.
        """

        message = {"PERMIT_JOIN": [timeout_s, name]}
        reply = {"result": "network allows joining"}

        result = await self._send(message, reply)
        return result

    async def set_lock(self, pin: int, devices: [NeoStat]):
        """
        PIN locks thermostats

        PIN is a four digit number
        """

        try:
            if pin < 0 or pin > 9999:
                return False
        except TypeError:
            raise NeoHubUsageError('pin must be a number')

        pins = []
        for x in range(4):
            pins.append(pin % 10)
            pin = pin // 10
        pins.reverse()

        try:
            names = [x.name for x in devices]
        except (TypeError, AttributeError):
            raise NeoHubUsageError('devices must be a list of NeoStat objects')

        message = {"LOCK": [pins, names]}
        reply = {"result": "locked"}

        result = await self._send(message, reply)
        return result

    async def unlock(self, devices: [NeoStat]):
        """
        Unlocks PIN locked thermostats
        """

        try:
            names = [x.name for x in devices]
        except (TypeError, AttributeError):
            raise NeoHubUsageError('devices must be a list of NeoStat objects')

        message = {"UNLOCK": names}
        reply = {"result": "unlocked"}

        result = await self._send(message, reply)
        return result

    async def set_frost(self, state: bool, devices: [NeoStat]):
        """
        Enables or disables Frost mode
        """

        try:
            names = [x.name for x in devices]
        except (TypeError, AttributeError):
            raise NeoHubUsageError('devices must be a list of NeoStat objects')

        message = {"FROST_ON" if state else "FROST_OFF": names}
        reply = {"result": "frost on" if state else "frost off"}

        result = await self._send(message, reply)
        return result

    async def set_target_temperature(self, temperature: int, devices: [NeoStat]):
        """
        Sets the thermostat's temperature

        The temperature will be reset once next comfort level is reached
        """

        try:
            names = [x.name for x in devices]
        except (TypeError, AttributeError):
            raise NeoHubUsageError('devices must be a list of NeoStat objects')

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

        try:
            names = [x.name for x in devices]
        except (TypeError, AttributeError):
            raise NeoHubUsageError('devices must be a list of NeoStat objects')

        message = {"SET_DIFF": [switching_differential, names]}
        reply = {"result": "switching differential was set"}

        result = await self._send(message, reply)
        return result

    async def rate_of_change(self, devices: [NeoStat]):
        """
        Returns time in minutes required to change temperature by 1 degree
        """

        try:
            names = [x.name for x in devices]
        except (TypeError, AttributeError):
            raise NeoHubUsageError('devices must be a list of NeoStat objects')

        message = {"VIEW_ROC": names}

        result = await self._send(message)
        return result.__dict__

    async def set_timer(self, state: bool, devices: [NeoStat]):
        """
        Turns the output of timeclock on or off

        This function works only with NeoPlugs and does not work on
        NeoStats that are in timeclock mode.
        """

        try:
            names = [x.name for x in devices]
        except (TypeError, AttributeError):
            raise NeoHubUsageError('devices must be a list of NeoStat objects')

        message = {"TIMER_ON" if state else "TIMER_OFF": names}
        reply = {"result": "timers on" if state else "timers off"}

        result = await self._send(message, reply)
        return result

    async def set_timer_hold(self, state: bool, minutes: int, devices: [NeoStat]):
        """
        Turns the output of timeclock on or off for certain duration

        This function works with NeoStats in timeclock mode
        """

        try:
            names = [x.name for x in devices]
        except (TypeError, AttributeError):
            raise NeoHubUsageError('devices must be a list of NeoStat objects')

        message = {"TIMER_HOLD_ON" if state else "TIMER_HOLD_OFF": [minutes, names]}
        reply = {"result": "timer hold on" if state else "timer hold off"}

        result = await self._send(message, reply)
        return result
