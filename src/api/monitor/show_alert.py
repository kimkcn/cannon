#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import sys, datetime, os
sys.path.append("..")
from django.http import HttpResponse
from conf import alert_conf
from src.lib import db_mysql
from django.views.decorators.clickjacking import xframe_options_sameorigin
try:
    import simplejson as json
except ImportError:
    import json


@xframe_options_sameorigin
def get_alert_list(request):
    mysql_conn = db_mysql.MyPymysqlPool()

    alertfrom = str(request.GET['alertfrom'])
    product = str(request.GET['product'])
    level = str(request.GET['level'])
    status = str(request.GET['status'])
    page = int(request.GET['page'])
    limit = int(request.GET['limit'])

    data_list = []
    result_dict = {}
    body_dict = {}
    from src.lib import django_api
    django_api.DjangoApi().os_environ_update()
    offset = (page-1)*limit     # （当前页数-1）*每页数量 = 每页的开始位置
    delta_hours = 720
    starttime = datetime.datetime.now()-datetime.timedelta(hours=delta_hours)
    code = 500
    message = 'fail'
    success = False

    # 获取总条数，用于返回的json里面输出
    try:
        sql = "select count(id) from %s where alert_from like '%%%s%%' and production like '%%%s%%' and " \
              "current_state like '%%%s%%' and priority like '%%%s%%' and start_time > '%s';" % \
              (alert_conf.table_name, alertfrom, product, status, level, starttime)
        print(sql)
        total_count = int(mysql_conn.select(sql)[0][0])
    except:
        total_count = -1

    if total_count > 0:
        # 获取每页的告警信息
        try:
            sql = "select * from %s where alert_from like '%%%s%%' and production like '%%%s%%' and " \
                  "current_state like '%%%s%%' and priority like '%%%s%%' and " \
                  "start_time > '%s' order by start_time desc limit %s,%s;" %\
                  (alert_conf.table_name, alertfrom, product, status, level, starttime, offset, limit)
            print(sql)
            tmp_result = mysql_conn.select(sql)
        except:
            pass
        else:
            if tmp_result:
                code = 0
                success = True
                for record in tmp_result:
                    alert_from = record[1]
                    production = record[2]
                    resource = record[4]
                    alert_state_tmp = record[5]
                    alert_detail = record[6]
                    expression = record[7]
                    if record[8] is not None:
                        value = int(record[8])
                    else:
                        value = None
                    start_time = record[9].strftime("%Y-%m-%d %H:%M:%S")
                    end_time = ""
                    if record[10]:
                        end_time = record[10].strftime("%Y-%m-%d %H:%M:%S")
                    priority = record[11]
                    priority_format = priority
                    single_alert = {}

                    if production in alert_conf.black_list:
                        continue

                    if priority == 1:
                        priority_format = "灾难"
                    elif priority == 2:
                        priority_format = "严重"
                    elif priority == 3:
                        priority_format = "一般"
                    else:
                        priority_format = "未知"

                    if alert_state_tmp == "OK":
                        alert_state = "恢复"
                    elif alert_state_tmp == "ALARM":
                        alert_state = "告警"

                    single_alert['alert_from'] = alert_from
                    single_alert['production'] = production
                    single_alert['resource'] = resource
                    single_alert['priority'] = priority_format
                    single_alert['alert_state'] = alert_state
                    single_alert['alert_detail'] = alert_detail
                    single_alert['expression'] = expression
                    single_alert['value'] = value
                    single_alert['start_time'] = start_time
                    single_alert['end_time'] = end_time
                    data_list.append(single_alert)
    elif total_count == 0:
        code = 0
        message = 'success'
        success = True

    body_dict['data'] = data_list
    body_dict['count'] = total_count
    result_dict['code'] = code
    result_dict['success'] = success
    result_dict['message'] = message
    result_dict['body'] = body_dict
    mysql_conn.dispose()
    result_json = json.dumps(result_dict, ensure_ascii=False)
    return HttpResponse(result_json, content_type="application/json,charset=utf-8")


if __name__ == "__main__":
    get_alert_list('xxx')
