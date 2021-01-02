#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020-2021 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: MIT


import asyncio
import datetime
import logging
import neohubapi.neohub as neohub

from neohubapi.enums import ScheduleFormat


async def run():
    hub = neohub.NeoHub()
    system = await hub.get_system()
    hub_data, devices = await hub.get_live_data()
    print("Thermostats:")
    for device in devices['thermostats']:
        print(f"Target temperature of {device.name}: {device.target_temperature}")
        await device.identify()

    print("Timeclocks:")
    for device in devices['timeclocks']:
        print(f"Timeclock {device.name}: {device.target_temperature}")
        print(await hub.set_timer_hold(False, 1, [device]))

    print(await hub.target_temperature_step)


def main():
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(run())

if (__name__ == '__main__'):
    main()
