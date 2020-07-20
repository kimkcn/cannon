#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os
sys.path.append("..")
from django.http import HttpResponse
from src.lib import db_mysql
try:
    import simplejson as json
except ImportError:
    import json


def query_resource_package(request):
    from src.lib import django_api
    django_api.DjangoApi().os_environ_update()
    mysql_conn = db_mysql.MyPymysqlPoolDict()
    result_dict = {'code': 500, 'success': False, 'message': 'fail', 'body': {}}
    table_name = 'cost_resource_package'

    package_name = str(request.GET['package_name'])
    package_id = str(request.GET['package_id'])
    status = str(request.GET['status'])
    deduct_type = str(request.GET['deduct_type'])
    support_product = str(request.GET['support_product'])

    try:
        sql = "select * from %s where package_name like '%%%s%%' and package_id like '%%%s%%' and status like " \
              "'%%%s%%' and deduct_type like '%%%s%%' and support_product like '%%%s%%' order by remaining_amount;" % \
              (table_name, package_name, package_id, status, deduct_type, support_product)
        print(sql)
        tmp_result = mysql_conn.select(sql)
    except Exception as e:
        print('except, reason: %s' % e)
    else:
        result_dict['code'] = 0
        if tmp_result:
            for record in tmp_result:
                record['total_amount'] = '%s %s' % (record['total_amount'], record['total_amount_unit'])
                record['remaining_amount'] = '%s %s' % (record['remaining_amount'], record['remaining_amount_unit'])
                record['effective_time'] = record['effective_time'].strftime("%Y-%m-%d %H:%M:%S")
                record['expiry_time'] = record['expiry_time'].strftime("%Y-%m-%d %H:%M:%S")
                record['update_time'] = record['update_time'].strftime("%Y-%m-%d %H:%M:%S")
            result_dict['success'] = True
            result_dict['message'] = 'success'
    finally:
        mysql_conn.dispose()

    result_dict['body']['data'] = tmp_result
    result_json = json.dumps(result_dict, ensure_ascii=False)
    return HttpResponse(result_json, content_type="application/json,charset=utf-8")


if __name__ == "__main__":
    query_resource_package('xxx')
