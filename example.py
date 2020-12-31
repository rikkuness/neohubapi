#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: MIT


import asyncio
import datetime
import logging
import neohubapi.neohub as neohub

from neohubapi.enums import ScheduleFormat


async def run():
    hub = neohub.NeoHub()
    system = await hub.get_system()
    hub_data, thermostats = await hub.get_live_data()
    for device in thermostats:
        print(f"Target temperature of {device.name}: {device.target_temperature}")
        await device.identify()

    print(await hub.target_temperature_step)


#logging.basicConfig(level=logging.DEBUG)
asyncio.run(run())
