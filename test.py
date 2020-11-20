#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: LGPL-3.0-or-later


import asyncio
import neohub
import logging


async def run():
    hub = neohub.NeoHub()
    connection = await hub.connect()
    result = await hub.firmware()
    print(f"Firmware: {result}")


logging.basicConfig(level=logging.DEBUG)
asyncio.run(run())
