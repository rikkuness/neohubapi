#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: LGPL-3.0-or-later

import enum


class ScheduleFormat(str, enum.Enum):
    """
    Enum to specify Schedule Format

    ZERO  - non programmable (time clocks cannot be non programmable)
    ONE   - same format every day of the week
    TWO   - 5 day / 2 day
    SEVEN - 7 day (every day different)
    """

    ZERO = "NONPROGRAMMABLE"
    ONE = "24HOURSFIXED"
    TWO = "5DAY/2DAY"
    SEVEN = "7DAY"
