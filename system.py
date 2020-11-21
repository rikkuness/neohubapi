#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: LGPL-3.0-or-later

from enums import ScheduleFormat


def schedule_format(int_format):
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


class System:
    def __init__(self, system_info):
        self.dst_auto = system_info['DST_AUTO']
        self.dst_on = system_info['DST_ON']
        self.timer_format = schedule_format(system_info['FORMAT'])
        # If system timer format is set to non programmable, then any time clock remain
        # in the previous setting which is stored in ALT_TIMER_FORMAT.
        self.alt_timer_format = schedule_format(system_info['ALT_TIMER_FORMAT'])
        self.ntp = system_info['NTP_ON'] == "Running"
        self.hub_type = system_info['HUB_TYPE']
        self.hub_version = system_info['HUB_VERSION']
        self.temperature_unit = system_info["CORF"]
        self.timezone = system_info['TIME_ZONE']
        self.time = system_info['UTC']
