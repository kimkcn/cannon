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


def query_bill_overview(request):
    from src.lib import django_api
    django_api.DjangoApi().os_environ_update()
    mysql_conn = db_mysql.MyPymysqlPoolDict()

    body_dict = {}
    result_dict = {'code': 500, 'success': False, 'message': 'fail', 'body': body_dict}
    table_name = 'cost_bill_overview'

    cost_item_id = str(request.GET['cost_item_id'])
    billing_cycle = str(request.GET['billing_cycle'])
    product_code = str(request.GET['product'])

    sql = "select item.item_remark as item_remark, bill.billing_cycle as billing_cycle, " \
          "bill.product_code as product, sum(bill.pretax_amount) as pretax_amount from cost_bill_overview bill," \
          "cost_item item where item.id = bill.cost_item_id and cost_item_id like '%%%s%%' and " \
          "product_code like '%%%s%%' and billing_cycle like '%%%s%%' " \
          "group by item_remark,billing_cycle,product_code order by billing_cycle desc, pretax_amount desc;" % \
          (cost_item_id, product_code, billing_cycle)
    print(sql)

    try:
        tmp_result = mysql_conn.select(sql)
    except Exception as e:
        print('except, reason: %s' % e)
        result_dict['message'] = '数据库查询失败!'
    else:
        data_list = []
        result_dict['success'] = True
        result_dict['code'] = 0
        if not tmp_result:
            result_dict['message'] = '无匹配的数据'
        else:
            result_dict['message'] = 'success'
            data_list = tmp_result
    finally:
        mysql_conn.dispose()

    body_dict['data'] = data_list
    result_dict['body'] = body_dict
    result_json = json.dumps(result_dict, ensure_ascii=False)
    return HttpResponse(result_json, content_type="application/json,charset=utf-8")


if __name__ == "__main__":
    query_bill_overview('xxx')
