<!--
    SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
    SPDX-License-Identifier: CC-BY-4.0
-->

# Neohubapi

This is a simple python wrapper around Heatmiser's Neohub API.

## Usage example

```python
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
        print(f"Temperature in zone {device.name}: {device.temperature}")
        await device.identify()


asyncio.run(run())
```

## NeoHub API documentation

API documentation can be found from various places online or
you can request the latest version from support@heatmiser.com
