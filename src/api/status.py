#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author by 闪马, @20200407

""" 状态检查的接口，仅用于状态展示
"""

from django.http import HttpResponse
try:
    import simplejson as json
except ImportError:
    import json
from src.lib import django_api
django_api.DjangoApi().os_environ_update()


def query_status(request):
    code = 200
    success = True
    message = 'ok'
    data_list = {}

    result_dict = {'code': code, 'success': success, 'message': message, 'data': data_list}
    result_json = json.dumps(result_dict, ensure_ascii=False)
    print(result_json)
    return HttpResponse(result_json, content_type="application/json,charset=utf-8")


if __name__ == "__main__":
    query_status('xxx')