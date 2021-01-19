#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: LGPL-3.0-or-later

import enum


class ScheduleFormat(enum.Enum):
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


def schedule_format_int_to_enum(int_format):
    if int_format is None:
        return None
    if int_format == 0:
        return ScheduleFormat.ZERO
    elif int_format == 1:
        return ScheduleFormat.ONE
    elif int_format == 2:
        return ScheduleFormat.TWO
    elif int_format == 4:
        return ScheduleFormat.SEVEN
    else:
        raise ValueError('Unrecognized ScheduleFormat')


class Weekday(enum.Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"
