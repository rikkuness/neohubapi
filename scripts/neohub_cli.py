#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020-2021 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-FileCopyrightText: 2021 Dave O'Connor <daveoc@google.com>
# SPDX-License-Identifier: MIT

import asyncio
import argparse
from inspect import ismethod, signature
from neohubapi import neohub


class Error(Exception):
    pass


class NeohubCLIUsageError(Error):
    pass


class NeohubCLI(object):
    """A runner for neohub_cli operations."""

    def __init__(self, command, args, hub_ip=None, hub_port=4242):
        self._hub = neohub.NeoHub(host=hub_ip, port=hub_port)
        self._command = command
        self._args = args

        if command == 'help':
            return

        if command not in self._hub_command_methods():
            raise NeohubCLIUsageError(f'Uknown command {command}')

    def _hub_command_methods(self):
        """Return a list of NeoHub functions.

            Right now this is just all callables not starting with _

        """
        all_methods = [
                m for m in dir(self._hub) if ismethod(getattr(self._hub, m))]

        return [m for m in all_methods if not m.startswith('_')]

    def callable(self):
        """Return a bound callable for the method we want, or None."""
        if self._command == 'help':
            print(self.get_help(self._args))
            return None

        # TODO(daveoc): Set special cases datetime, etc.
        hubmethod = getattr(self._hub, self._command)
        sig = signature(hubmethod)
        if len(sig.parameters) == 0:
            # No arguments
            return hubmethod

        # TODO(daveoc): populate parameters and bind to methods that need them.
        print(f'Cannot do {self._command} yet')
        return None

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
        sig = signature(getattr(self._hub, args[0]))

        ret = f'{args[0]}:\n'

        if len(sig.parameters) == 0:
            ret += ' - No Arguments\n'
        else:
            for s in sig.parameters:
                ret += f' - {sig.parameters[s]}\n'

        return f'{ret}\n{docstr}\n'


async def main():
    argp = argparse.ArgumentParser(description='CLI to neohub devices')
    argp.add_argument('--hub_ip', help='IP address of Neohub', default=None)
    argp.add_argument(
        '--hub_port', help='Port number of Neohub to talk to', default=4242)
    argp.add_argument('command', help='Command to issue')
    argp.add_argument('arg', help='Arguments to command', nargs='*')
    args = argp.parse_args()

    try:
        nhc = NeohubCLI(
                args.command,
                args.arg,
                hub_ip=args.hub_ip,
                hub_port=args.hub_port)
        m = nhc.callable()
        if m:
            result = await m()
            # TODO(daveoc): Make delightful.
            print(result)
    except Error as e:
        print(e)
        argp.print_help()


if __name__ == '__main__':
    asyncio.run(main())
