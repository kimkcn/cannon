#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, datetime, os
from django.http import HttpResponse
from conf import alert_conf
from django.views.decorators.clickjacking import xframe_options_sameorigin
try:
    import simplejson as json
except ImportError:
    import json


def query_task_scheduler_status(request):
    pass


if __name__ == "__main__":
    query_task_scheduler_status('xxx')
