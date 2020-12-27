#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: LGPL-3.0-or-later

from datetime import datetime, timedelta
from types import SimpleNamespace

from async_property import async_property

from neohubapi.enums import Weekday


class NeoStat(SimpleNamespace):
    """
    Class representing NeoStat theormostat
    """

    def __init__(self, hub, thermostat):
        self._data_ = thermostat
        self._hub = hub

        self.active_level = self._data_.ACTIVE_LEVEL
        self.active_profile = self._data_.ACTIVE_PROFILE
        self.available_modes = self._data_.AVAILABLE_MODES
        self.away = self._data_.AWAY
        self.cool_on = self._data_.COOL_ON
        self.cool_temp = self._data_.COOL_TEMP
        self.current_floor_temperature = self._data_.CURRENT_FLOOR_TEMPERATURE
        self.weekday = Weekday(self._data_.DATE)
        self.device_id = self._data_.DEVICE_ID
        self.fan_control = self._data_.FAN_CONTROL
        self.fan_speed = self._data_.FAN_SPEED
        self.floor_limit = self._data_.ZONE_NAME
        self.hc_mode = self._data_.HC_MODE
        self.heat_mode = self._data_.HEAT_MODE
        self.heat_on = self._data_.HEAT_ON
        self.hold_cool = self._data_.HOLD_COOL
        self.hold_off = self._data_.HOLD_OFF
        self.hold_on = self._data_.HOLD_ON
        self.hold_temp = self._data_.HOLD_TEMP
        _hold_time = datetime.strptime(self._data_.HOLD_TIME, "%H:%M")
        self.hold_time = timedelta(hours=_hold_time.hour, minutes=_hold_time.minute)
        self.holiday = self._data_.HOLIDAY
        self.lock = self._data_.LOCK
        self.low_battery = self._data_.LOW_BATTERY
        self.manual_off = self._data_.MANUAL_OFF
        self.modelock = self._data_.MODELOCK
        self.modulation_level = self._data_.MODULATION_LEVEL
        self.name = self._data_.ZONE_NAME
        self.offline = self._data_.OFFLINE
        self.pin_number = int(self._data_.PIN_NUMBER)
        self.preheat_active = int(self._data_.PREHEAT_ACTIVE)
        self.prg_temp = self._data_.PRG_TEMP
        self.prg_timer = self._data_.PRG_TIMER
        self.set_temp = self._data_.SET_TEMP  # target temperature
        self.standby = self._data_.STANDBY
        _switch_delay_left = datetime.strptime(self._data_.SWITCH_DELAY_LEFT, "%H:%M")
        self.switch_delay_left = timedelta(hours=_switch_delay_left.hour, minutes=_switch_delay_left.minute)
        self.temporary_set_flag = self._data_.TEMPORARY_SET_FLAG
        self.temperature = self._data_.ACTUAL_TEMP
        _time = datetime.strptime(self._data_.TIME, "%H:%M")
        self.time = timedelta(hours=_time.hour, minutes=_time.minute)
        self.timer_on = self._data_.TIMER_ON
        self.window_open = self._data_.WINDOW_OPEN
        self.write_count = self._data_.WRITE_COUNT

    async def identify(self):
        """
        Flashes red LED light
        """

        message = {"IDENTIFY_DEV": self.name}
        reply = {"result": "Device identifying"}

        result = await self._hub._send(message, reply)
        return result

    async def rename(self, new_name):
        """
        Renames this zone
        """

        message = {"ZONE_TITLE": [self.name, new_name]}
        reply = {"result": "zone renamed"}

        result = await self._hub._send(message, reply)
        return result

    async def remove(self):
        """
        Removes this zone

        If successful, thermostat will be disconnected from the hub
        Note that it takes a few seconds to remove thermostat
        New get_zones call will still return the original list
        during that period.
        """

        message = {"REMOVE_ZONE": self.name}
        reply = {"result": "zone removed"}

        result = await self._hub._send(message, reply)
        return result

    async def set_lock(self, pin: int):
        result = await self._hub.set_lock(pin, [self])
        return result

    async def unlock(self):
        result = await self._hub.unlock([self])
        return result

    async def set_frost(self, state: bool):
        result = await self._hub.frost(state, [self])
        return result

    async def set_temp(self, temperature: int):
        result = await self._hub.set_temp(temperature, [self])
        return result

    async def set_diff(self, switching_differential: int):
        result = await self._hub.set_diff(switching_differential, [self])
        return result

    @async_property
    async def rate_of_change(self):
        result = await self._hub.rate_of_change([self])
        roc = result[self.name]
        return roc
