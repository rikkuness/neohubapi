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
