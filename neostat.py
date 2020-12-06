#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: LGPL-3.0-or-later

from types import SimpleNamespace


class NeoStat(SimpleNamespace):
    """
    Class representing NeoStat theormostat
    """

    def __init__(self, hub, thermostat):
        self._data_ = thermostat
        self._hub = hub

    @property
    def name(self):
        """ Zone name. """

        return self._data_.ZONE_NAME

    @property
    def temperature(self):
        """ Actual zone temperature. """

        return self._data_.ACTUAL_TEMP

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

    async def lock(self, pin: int):
        result = await self._hub.lock(pin, [self])
        return result

    async def unlock(self):
        result = await self._hub.unlock([self])
        return result

    async def frost(self, state: bool):
        result = await self._hub.frost(state, [self])
        return result

    async def set_temp(self, temperature: int):
        result = await self._hub.set_temp(temperature, [self])
        return result

    async def set_diff(self, switching_differential: int):
        result = await self._hub.set_diff(switching_differential, [self])
        return result

    async def rate_of_change(self):
        result = await self._hub.rate_of_change([self])
        return result
