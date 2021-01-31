<!--
    SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
    SPDX-License-Identifier: CC-BY-4.0
-->

# NeoHubAPI

This is a simple python wrapper around Heatmiser's Neohub API.

It's primary purpose is to be used via Home Assistant integration but
it can also be used as a standalone library.

## Usage example

```python
import asyncio
import neohubapi.neohub as neohub


async def run():
    hub = neohub.NeoHub()
    system = await hub.get_system()
    hub_data, devices = await hub.get_live_data()
    for device in devices['thermostats']:
        print(f"Temperature in zone {device.name}: {device.temperature}")
        await device.identify()


asyncio.run(run())
```

## NeoHub API documentation

API documentation can be found from various places online or
you can request the latest version from support@heatmiser.com

## neohub_cli.py

This package includes a CLI for performing common tasks.

```
$ neohub_cli.py help  # Shows all commands
$ neohub_cli.py help set_time  # Displays help for the set_time function
$ neohub_cli.py --hub_ip=myneohub set_time "2021-01-31 15:43:00"  # Specify times like this
$ neohub_cli.py --hub_ip=myneohub set_lock 1234 "Living Room"  # Name NeoStats like this.
```

