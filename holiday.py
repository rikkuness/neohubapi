#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: LGPL-3.0-or-later

import datetime
import enum

class Holiday:
    """
    Class representing Holidays

    start, end: holiday datetime objects or None
    ids
    """

    def __init__(self, reply: str):
        start = reply["start"]
        if start:
            self._start = datetime.datetime.strptime(start.strip(), "%a %b %d %H:%M:%S %Y")
        else:
            self._start = None

        end = reply["end"]
        if end:
            self.end = datetime.datetime.strptime(end.strip(), "%a %b %d %H:%M:%S %Y")
        else:
            self._end = None

        self._ids = reply["ids"]


    @property
    def start(self):
        """ Beginning of holiday. """
        return self._start


    @property
    def end(self):
        """ End of holiday. """
        return self._end


    @property
    def ids(self):
        """ Devices that have holiday set up. """
        return self._ids
