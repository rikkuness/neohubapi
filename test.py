#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: LGPL-3.0-or-later


import asyncio
import neohub
import logging


async def run():
    hub = neohub.NeoHub()
    await hub.connect()
    firmware_version = await hub.firmware()
    print(firmware_version)
    result = await hub.set_channel(14)
    print(result)


logging.basicConfig(level=logging.DEBUG)
asyncio.run(run())
