#!/usr/bin/env python3
# coding:utf-8
from django.http import HttpResponse
import json

from src.lib import db_mysql
mysql_conn = db_mysql.MyPymysqlPool()
from src.lib import django_api
django_api.DjangoApi().os_environ_update()


def get_sas_alert(request):
    event_list = []
    event_body_dict = {}
    event_reponse_dict = {}
    success = False
    code = 1
    message = ''

    try:
        page = int(request.GET['page'])
        limit = int(request.GET['limit'])
    except:
        page = 1
        limit = 10

    try:
        level = str(request.GET['level'])
    except:
        level = 'serious'
    try:
        alert_status = str(request.GET['alert_status'])
    except:
        alert_status = 'True'
    try:
        event_type = str(request.GET['event_type'])
    except:
        event_type = ''

    offset = (page - 1) * limit  # （当前页数-1）*每页数量 = 每页的开始位置

    # 获取表数据总条数
    try:
        sql_count = "select count(id) from %s ;" % ('safe_sas_alert')
        total_count = int(mysql_conn.select(sql_count)[0][0])
    except:
        total_count = 0

    if total_count > 0:
        try:
            # 执行查询表数据
            sql_cmd = "select * from %s where level = '%s' and alert_status = '%s' and event_type like '%%%s%%' order by last_time desc limit %s,%s" % \
                      ('safe_sas_alert', level, alert_status, event_type, offset, limit)
            result = mysql_conn.select(sql_cmd)
        except:
            pass
        else:
            # 循环赋值，定义列表
            for record in result:
                event_id = record[1]
                level = record[2]
                event_name = record[3]
                event_type = record[4]
                instance_id = record[5]
                instance_name = record[6]
                start_time = record[9].strftime("%Y-%m-%d %H:%M:%S")
                last_time = record[10].strftime("%Y-%m-%d %H:%M:%S")
                alert_status = record[11]

                single_event = {}
                single_event['doevent_id'] = event_id
                single_event['level'] = level
                single_event['event_name'] = event_name
                single_event['event_type'] = event_type
                single_event['instance_id'] = instance_id
                single_event['instance_name'] = instance_name
                single_event['start_time'] = start_time
                single_event['last_time'] = last_time
                single_event['alert_status'] = alert_status
                event_list.append(single_event)
            code = '0'
            success = True
            message = 'ok'

    event_body_dict['data'] = event_list
    event_body_dict['count'] = total_count

    event_reponse_dict['code'] = code
    event_reponse_dict['success'] = success
    event_reponse_dict['message'] = message
    event_reponse_dict['body'] = event_body_dict
    expire_result_json = json.dumps(event_reponse_dict, ensure_ascii=False)
    print(expire_result_json)

    return HttpResponse(expire_result_json, content_type="application/json,charset=utf-8")

if __name__ == "__main__":
    get_sas_alert('xxx')
