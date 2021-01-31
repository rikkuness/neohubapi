#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020-2021 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-FileCopyrightText: 2021 Dave O'Connor <daveoc@google.com>
# SPDX-License-Identifier: MIT

import types
import asyncio
import inspect
import argparse
import datetime
from functools import partial
from neohubapi.neohub import NeoHub
from neohubapi.neohub import NeoHubUsageError
from neohubapi.neostat import NeoStat
from neohubapi.enums import ScheduleFormat, Weekday


class Error(Exception):
    pass


class NeoHubCLIUsageError(Error):
    pass


class NeoHubCLIInternalError(Error):
    pass


class NeoHubCLIArgumentError(Error):
    pass


class NeoHubCLI(object):
    """A runner for neohub_cli operations."""

    def __init__(self, command, args, hub_ip=None, hub_port=4242):
        self._hub = NeoHub(host=hub_ip, port=hub_port)
        self._command = command
        self._args = args
        # live data cached from the neohub. We assume this data will remain current
        # throughout the execution of the script.
        self._live_data = None

        if command == 'help':
            return

        if command not in self._hub_command_methods():
            raise NeoHubCLIUsageError(f'Unknown command {command}')

    def _hub_command_methods(self):
        """Return a list of NeoHub functions.

           Right now this is just all methods not starting with _

        """
        all_methods = [
                m for m in dir(self._hub) if inspect.ismethod(getattr(self._hub, m))]

        return [m for m in all_methods if not m.startswith('_')]

    async def callable(self):
        """Return a bound callable for the method we want, or None."""
        if self._command == 'help':
            print(self.get_help(self._args))
            return None

        # Firstly, see if we have a separately-implemented exception below.
        special_method = getattr(self, f'_callable_{self._command}', None)
        if special_method:
            return await special_method()

        hubmethod = getattr(self._hub, self._command)
        sig = inspect.signature(hubmethod)
        if len(sig.parameters) == 0:
            # No arguments
            return hubmethod

        # See if we have the right numer of command line arguments.
        if len(sig.parameters) != len(self._args):
            print(f'Expecting {len(sig.parameters)} args for {self._command}, got {len(self._args)}')
            print(self.get_help([self._command]))
            return None

        # Next, see if all our arguments are annotated correctly.
        # Several methods ask for [NeoStat] (i.e. a list of NeoStat objects).
        # Cover for this case, without getting into expanding lists of other things.
        # (Yes, this means we only support passing one neostat name per CLI command, for now).
        arg_types = []
        for p in sig.parameters:
            a = sig.parameters[p].annotation
            if type(a) == type:
                arg_types.append(a)
            elif type(a) == list:
                if a[0] == NeoStat:
                    arg_types.append(a[0])
                else:
                    raise NeoHubCLIInternalError(f'Command {self._command} argument not bindable: {a[0]}')
            else:
                raise NeoHubCLIInternalError(f'Unexpected para annotation in {self._command}: {a}')

        if inspect._empty not in arg_types:
            # build a list comprising the 'real' objects represented.
            real_args = []
            for i in range(len(self._args)):
                try:
                    real_args.append(await self._parse_arg(self._args[i], arg_types[i]))
                except NeoHubCLIArgumentError:
                    raise
                except NeoHubCLIInternalError:
                    print('Internal Error:')
                    raise
            return partial(getattr(self._hub, self._command), *real_args)

        # No special method and un-annotated params.
        print(f'Cannot do {self._command} (yet)')
        return None

    async def _parse_arg(self, arg, argtype):
        """Return the desired type, given the string version of arg.

           This also does things liks parsing dates, etc.
        """
        if argtype == int:
            if not arg.isnumeric():
                raise NeoHubCLIArgumentError(f'argument to {self._command} must be numeric')
            return int(arg)
        elif argtype == str:
            return str(arg)
        elif argtype == bool:
            if arg in ('1', 'True', 'true', 'on', 'y'):
                away = True
            elif arg in ('0', 'False', 'false', 'off', 'n'):
                away = False
            else:
                raise NeoHubCLIArgumentError(f'\'{arg}\' not recognised as boolean')
            return away
        elif argtype == ScheduleFormat:
            sf = getattr(ScheduleFormat, arg, None)
            if not sf:
                raise NeoHubCLIArgumentError(
                        f'argument must be in {[x.name for x in ScheduleFormat]}')
            return sf
        elif argtype == datetime.datetime:
            try:
                dt = datetime.datetime.strptime(arg, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                raise NeoHubCLIArgumentError('dates must be in format "YYYY-MM-DD HH:MM:SS"')
            return dt
        elif argtype == NeoStat:
            # We assume the cmdline argument is the thermostat name.
            if not self._live_data:
                # (hub_data, devices)
                self._live_data = await self._hub.get_live_data()
            found = [x for x in self._live_data[1]['thermostats'] if x.name == arg]
            if found:
                # methods always expect a list of these.
                return [found[0]]
            else:
                raise NeoHubCLIArgumentError(f'No such thermostat: {arg}')
        else:
            raise NeoHubCLIInternalError(f'Unknown type {type(argtype)} {argtype} for {self._command}')

    async def _optional_datetime(self):
        # If we got an arg, assume it's a date, otherwise use today.
        if len(self._args) > 1:
            print(f'{self._command} takes zero or one argument')
            return None
        elif len(self._args) == 1:
            real_arg = await self._parse_arg(self._args[0], datetime.datetime)
            return partial(getattr(self._hub, self._command), *[real_arg])
        else:
            return getattr(self._hub, self._command)

    # These take a single datetime (optional) argument.
    _callable_set_date = _optional_datetime
    _callable_set_time = _optional_datetime
    _callable_set_datetime = _optional_datetime

    async def _callable_permit_join(self):
        if len(self._args) > 2 or len(self._args) == 0:
            print(f'{self._command} takes either 1 or 2 arguments')
            return None

        real_name = self._args[0]
        args = [real_name]

        if len(self._args) == 2:
            timeout_s = await self._parse_arg(self._args[1], int)
            args.append(timeout_s)

        return partial(getattr(self._hub, 'permit_join'), *args)

    def output(self, raw_result, output_format='json'):
        """Produce output in a desired format."""
        if output_format == 'raw':
            return raw_result

        # Right now, everything just returns hub data or a single outcome
        # except get_live_data. Handle special cases.
        special_case = getattr(self, f'_output_{self._command}', None)
        if special_case:
            return special_case(raw_result, output_format)

        if type(raw_result) == bool:
            return 'Command Succeeded' if raw_result else 'Command Failed'

        if type(raw_result) in (int, str):
            return f'{raw_result}'

        if type(raw_result) != types.SimpleNamespace:
            if type(raw_result) == dict:
                raw_result = types.SimpleNamespace(**raw_result)
            else:
                raise NeoHubCLIInternalError(
                        f'Unexpected type {type(raw_result)} in output()')

        return self._output_simplenamespace(raw_result, output_format)

    def _resolve_output_val(self, val):
        """Return a readable str version of a value.
           This is mainly so our own enums and objects look readable.
        """
        if type(val) in (ScheduleFormat, Weekday):
            return val.value
        elif type(val) == NeoStat:
            return f'[NeoStat: {val.name}]'
        else:
            return val

    def _output_simplenamespace(self, obj, output_format):
        """Output a types.Simplenamespace object."""
        if output_format == 'list':
            attrs = dict(
                [(a, getattr(obj, a)) for a in dir(obj)
                    if not a.startswith('_')])
            return '\n'.join([f'{a}: {self._resolve_output_val(attrs[a])}' for a in attrs])
        else:
            raise NeoHubCLIUsageError(f'Unknown output format {output_format}')

    def _output_get_live_data(self, raw_result, output_format):
        """Return special case output for get_live_data."""
        out = self._output_simplenamespace(raw_result[0], output_format)
        out += '\n\n'
        for device_type in raw_result[1]:
            out += f'{device_type}:\n'
            devices = raw_result[1][device_type]
            for d in devices:
                out += str(d) + '\n'
        return out

    def get_help(self, args):
        """Print help on what commands do"""
        if len(args) == 0:
            ret = 'Valid commands:\n\n'
            for cmd in self._hub_command_methods():
                ret += f' - {cmd}\n'
            return ret

        # handle 'help <blah>'
        if args[0] not in self._hub_command_methods():
            return f'Command {args[0]} not known'

        docstr = getattr(self._hub, args[0]).__doc__ or 'No help for {args[0]}'
        sig = inspect.signature(getattr(self._hub, args[0]))

        ret = f'{args[0]}:\n'

        if len(sig.parameters) == 0:
            ret += ' - No Arguments\n'
        else:
            for s in sig.parameters:
                ret += f' - {sig.parameters[s]}\n'

        return f'{ret}\n{docstr}\n'


async def main():
    argp = argparse.ArgumentParser(description='CLI to neohub devices')
    argp.add_argument('--hub_ip', help='IP address of NeoHub', default=None)
    argp.add_argument(
        '--hub_port', help='Port number of NeoHub to talk to', default=4242)
    argp.add_argument('--format', help='Output format', default='list')
    argp.add_argument('command', help='Command to issue')
    argp.add_argument('arg', help='Arguments to command', nargs='*')
    args = argp.parse_args()

    try:
        nhc = NeoHubCLI(
                args.command,
                args.arg,
                hub_ip=args.hub_ip,
                hub_port=args.hub_port)
        m = await nhc.callable()
        if m:
            result = await m()
            print(nhc.output(result, output_format=args.format))
    except NeoHubUsageError as e:
        print(f'Invalid API usage: {e}')
    except Error as e:
        print(e)


if __name__ == '__main__':
    asyncio.run(main())
