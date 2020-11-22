#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: LGPL-3.0-or-later


class NeoStat:
    """
    Class representing NeoStat theormostat
    """

    def __init__(self, hub, name: str, zone_id: int):
        self._hub = hub
        self._name = name
        self._zone_id = zone_id

    @property
    def name(self):
        """ Zone name. """
        return self._name

    @property
    def zone_id(self):
        """ End of holiday. """
        return self._zone_id

    async def identify(self):
        """
        Flashes red LED light
        """

        message = {"IDENTIFY_DEV": self.zone_id}
        reply = {"result": "Device identifying"}

        result = await self._hub._send(message, reply)
        return result

    async def rename(self, new_name):
        """
        Renames this zone
        """

        message = {"ZONE_TITLE": [self.name, new_name]}
        reply = {"result": "flashing led"}

        result = await self._hub._send(message, reply)
        if result:
            self.name = new_name
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
