#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, time
sys.path.append("..")
from django.http import HttpResponse
from src.lib import db_mysql
try:
    import simplejson as json
except ImportError:
    import json


def query_product_renew(request):
    from src.lib import django_api
    from src.lib import time_api
    django_api.DjangoApi().os_environ_update()
    result_dict = {'code': 500, 'success': False, 'message': 'fail', 'body': {}}
    table_name = 'cost_product_renew'
    tmp_result = {}

    cost_item_id = str(request.GET['cost_item_id'])
    instance_id = str(request.GET['instance_id'])
    product_code = str(request.GET['product_code'])
    status = str(request.GET['status'])
    page = int(request.GET['page'])
    limit = int(request.GET['limit'])

    print(cost_item_id, instance_id, product_code, status)
    mysql_conn = db_mysql.MyPymysqlPoolDict()
    offset = (page-1)*limit     # （当前页数-1）*每页数量 = 每页的开始位置

    # 获取总条数，用于返回的json里面输出
    try:
        sql = "select count(id) as count from %s where cost_item_id like '%%%s%%' and instance_id like '%%%s%%' and " \
              "product_code like '%%%s%%' and status like '%%%s%%'" % \
              (table_name, cost_item_id, instance_id, product_code, status)
        print(sql)
        total_count = int(mysql_conn.select(sql)[0]['count'])
    except Exception as e:
        print("except: %s" % e)
        total_count = -1

    try:
        sql = "select cost_item_id, instance_id, instance_name, product_code, product_type, status, " \
              "subscription_type, end_time, create_time, sub_status, renew_status from %s where " \
              "cost_item_id like '%%%s%%' and instance_id like '%%%s%%' and product_code " \
              "like '%%%s%%' and status like '%%%s%%' order by end_time limit %s,%s;" % \
              (table_name, cost_item_id, instance_id, product_code, status, offset, limit)
        print(sql)
        tmp_result = mysql_conn.select(sql)
    except Exception as e:
        print('except: %s' % e)
    else:
        result_dict['code'] = 0
        if tmp_result:
            for record in tmp_result:
                record['count_down'] = int((record['end_time'] - time.time())/86400)
                record['end_time'] = time_api.timestamp_to_datetime(record['end_time'])
                record['create_time'] = time_api.timestamp_to_datetime(record['create_time'])

            print(tmp_result)
            result_dict['success'] = True
            result_dict['message'] = 'success'

    result_dict['body']['data'] = tmp_result
    result_dict['body']['count'] = total_count
    mysql_conn.dispose()
    result_json = json.dumps(result_dict, ensure_ascii=False)
    return HttpResponse(result_json, content_type="application/json,charset=utf-8")


if __name__ == "__main__":
    query_product_renew('xxx')
