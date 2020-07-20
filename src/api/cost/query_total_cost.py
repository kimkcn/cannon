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
table_name = 'cost_cycle_cost'
cost_item_table = 'cost_item'


def get_month_total_cost_web(request):
    from src.lib import django_api
    django_api.DjangoApi().os_environ_update()
    result_dict = {}
    body_dict = {}
    code = 500
    success = False

    status, result = query_total_cost()
    if status:
        success = True
        code = 0

    body_dict['data'] = result
    result_dict['code'] = code
    result_dict['success'] = success
    result_dict['message'] = ''
    result_dict['body'] = body_dict
    result_json = json.dumps(result_dict, ensure_ascii=False)
    print(result_json)
    return HttpResponse(result_json, content_type="application/json,charset=utf-8")


def get_month_cost_range_list(request):
    from src.lib import django_api
    django_api.DjangoApi().os_environ_update()
    code = 500
    success = False
    result_dict = {}
    body_dict = {}
    month_list = []
    month_cost_list = []

    status, result = query_total_cost()
    if status:
        success = True
        code = 0
    if result:
        for record in result:
            month_list.append(record['month'])
            month_cost_list.append(record['month_cost'])

    body_dict['month_list'] = month_list
    body_dict['month_cost_list'] = month_cost_list
    result_dict['code'] = code
    result_dict['success'] = success
    result_dict['message'] = ''
    result_dict['body'] = body_dict
    result_json = json.dumps(result_dict, ensure_ascii=False)
    print(result_json)
    return HttpResponse(result_json, content_type="application/json,charset=utf-8")


def query_total_cost():
    from src.lib import django_api
    django_api.DjangoApi().os_environ_update()
    mysql_conn = db_mysql.MyPymysqlPool()
    month_total_list = []
    status = False
    try:
        sql = "select month, sum(total_cost) from %s group by month order by month desc limit 12;" % table_name
        tmp_db_result = mysql_conn.select(sql)
    except Exception as e:
        print('except, reason: %s' % e)
    else:
        status = True
        if tmp_db_result:
            for db_record in tmp_db_result:
                month = db_record[0]
                total_cost = db_record[1]
                month_dict = {}
                month_dict['month'] = month
                month_dict['month_cost'] = total_cost
                month_total_list.append(month_dict)
    finally:
        mysql_conn.dispose()
    return status, month_total_list


def query_item_cost(request):
    from src.lib import django_api
    django_api.DjangoApi().os_environ_update()
    mysql_conn = db_mysql.MyPymysqlPool()
    result_dict = {}
    body_dict = {}
    data_list = []
    code = 500
    success = False

    cost_item_id = str(request.GET['cost_item_id'])
    month = str(request.GET['month'])

    sql = "select cost.cost_item_id,item.item_remark,cost.month,cost.total_cost from cost_cycle_cost cost, " \
          "cost_item item where item.id = cost.cost_item_id and cost.cost_item_id like '%%%s%%' " \
          "and cost.month like '%%%s%%' order by month desc" % (cost_item_id, month)
    print(sql)
    try:
        tmp_db_result = mysql_conn.select(sql)
        print(tmp_db_result)
    except Exception as e:
        print('except, reason: %s' % e)
    else:
        if tmp_db_result:
            for db_record in tmp_db_result:
                item_dict = {'item_id': db_record[0], 'item_remark': db_record[1], 'month': db_record[2],
                             'total_cost': db_record[3]}
                data_list.append(item_dict)
        success = True
        code = 0
    finally:
        mysql_conn.dispose()
    body_dict['data'] = data_list
    result_dict['code'] = code
    result_dict['success'] = success
    result_dict['message'] = ''
    result_dict['body'] = body_dict
    result_json = json.dumps(result_dict, ensure_ascii=False)
    return HttpResponse(result_json, content_type="application/json,charset=utf-8")


if __name__ == "__main__":
    #query_item_cost('xxx')
    query_total_cost()