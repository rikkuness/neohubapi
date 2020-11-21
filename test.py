#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: LGPL-3.0-or-later


import asyncio
import datetime
import logging
import neohub

from enums import ScheduleFormat

async def run():
    hub = neohub.NeoHub()
    await hub.connect()
    system = await hub.get_system()
    result = await hub.get_devices()
    print(result)


logging.basicConfig(level=logging.DEBUG)
asyncio.run(run())
