#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: LGPL-3.0-or-later


import asyncio
import neohub
import logging


async def run():
    hub = neohub.NeoHub()
    await hub.connect()
    system = await hub.get_system()
    print(vars(system))
    result = await hub.set_format("NONPROGRAMMABLE")
    print(result)


logging.basicConfig(level=logging.DEBUG)
asyncio.run(run())
