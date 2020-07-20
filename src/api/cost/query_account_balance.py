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


def query_account_balance(request):
    from src.lib import django_api
    django_api.DjangoApi().os_environ_update()
    mysql_conn = db_mysql.MyPymysqlPool()
    data_list = []
    body_dict = {}
    result_dict = {'code': 500, 'success': False, 'message': 'fail', 'body': body_dict}
    table_name = 'cost_account_balance'

    # 获取总条数，用于返回的json里面输出
    try:
        sql = "select count(id) from %s;" % table_name
        total_count = int(mysql_conn.select(sql)[0][0])
    except Exception as e:
        total_count = 0

    if total_count > 0:
        try:
            sql = "select balance.cost_item_id,item.item_remark,balance.balance,balance.update_time from " \
                  "cost_account_balance balance,cost_item item where item.id = balance.cost_item_id " \
                  "order by balance desc;"
            print(sql)
            tmp_result = mysql_conn.select(sql)
        except Exception as e:
            print('except, reason: %s' % e)
        else:
            result_dict['success'] = True
            result_dict['message'] = 'success'
            result_dict['code'] = 0
            for record in tmp_result:
                single_record = {}
                item_id = record[0]
                item_remark = record[1]
                balance = record[2]
                record_time = record[3].strftime("%Y-%m-%d %H:%M:%S")
                single_record['item_id'] = item_id
                single_record['item_remark'] = item_remark
                single_record['balance'] = balance
                single_record['record_time'] = record_time
                data_list.append(single_record)
        finally:
            mysql_conn.dispose()

    body_dict['data'] = data_list
    result_dict['count'] = total_count
    result_dict['body'] = body_dict
    result_json = json.dumps(result_dict, ensure_ascii=False)
    return HttpResponse(result_json, content_type="application/json,charset=utf-8")


if __name__ == "__main__":
    query_account_balance('xxx')
