#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def datetime_to_timestamp(date_time):
    import datetime

    timestamp = datetime.datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S').timestamp()
    return time_stamp


def timestamp_to_datetime(time_stamp):
    import time

    date_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time_stamp))
    return date_time


def isotime_to_timestamp(iso_time):
    import re
    import datetime
    part_a = re.split('[TZ]', iso_time)[0]
    part_b = re.split('[TZ]', iso_time)[1]

    date_time = "%s %s" % (part_a, part_b)

    time_stamp = int(datetime.datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S").timestamp())
    #print(time_stamp)

    return time_stamp