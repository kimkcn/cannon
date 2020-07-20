#!/usr/bin/env python3
# coding=utf-8
import json
import math
from datetime import datetime

# 项目的lib
from src.lib.cloud import aliyun_api
from src.lib import db_mysql

# 获取安全告警事件总条数
format = 'json'
page = 1
limit = 20
From = 'sas'

response = aliyun_api.AliyunApi().describe_alarmevent_list(format, page, limit, From)
result = json.loads(response, encoding='utf-8')
total_count = result['PageInfo']['TotalCount']  # 安全告警事件总条数


def get_sasalert_info(task_id=False):
    success = False
    current_page = 1
    response_limit = 20
    total_page = math.ceil(total_count/limit)  # 获取告警事件的总条数
    m = 0
    while current_page <= total_page:
        alert_response = aliyun_api.AliyunApi().describe_alarmevent_list(format, current_page, response_limit, From)
        alert_result = json.loads(alert_response, encoding='utf-8')
        events = alert_result['SuspEvents']
        for i in events:
            print(i)
            event_id = i['AlarmUniqueInfo']
            level = i['Level']
            event_type = i['AlarmEventType']
            event_name = i['AlarmEventName']
            try:
                instance_id = i['InstanceId']
            except:
                instance_id = None
            start_time = datetime.fromtimestamp(float(i['StartTime']/1000))
            last_time = datetime.fromtimestamp(float(i['GmtModified']/1000))
            alert_status = str(i['Dealed'])
            print(alert_status)
            alert_id = i['SecurityEventIds']
            now_time = datetime.now()
            try:
                update_sql_success_list = list()
                success = update_sql(event_id, level, event_type, event_name, instance_id, start_time, last_time, alert_status, alert_id, now_time)
            except Exception as e:
                print('更新数据表失败 : %s' % e)
                return success
            else:
                update_sql_success_list.append(success)
            for single_success in update_sql_success_list:
                if single_success is False:
                    m += 1
        current_page += 1
    if m == 0:
        success = True
    return success


def update_sql(event_id, level, event_type, event_name, instance_id, start_time, last_time, alert_status, alert_id, now_time):
    mysql_conn = db_mysql.MyPymysqlPool()
    success = False
    try:
        sql = "select count(*) from %s where event_id = '%s'" % ('safe_sas_alert', event_id)
        sql_result = mysql_conn.select(sql)
    except Exception as e:
        print('do sql failed %s' % e)
        return success
    else:
        if result:
            try:
                event_count = sql_result[0][0]
            except Exception as e:
                print('maybe sql_result type is wrong: %s' % e)
                return success
        else:
            print('云安全中心没有产生告警')
            success = True
            return success
    if event_count == 0:  # 如果表中没有同一个event_id的事件，则直接将alert数据写入表中
        try:
            sql = "insert into %s(event_id, level, event_type, event_name, instance_id, start_time, last_time, " \
                  "alert_status, alert_id, update_time) values('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'," \
                  " '%s')" % ('safe_sas_alert', event_id, level, event_type, event_name, instance_id, start_time,
                              last_time, alert_status, alert_id, now_time)
            mysql_conn.insert(sql)
        except Exception as e:
            print('do sql failed %s' % e)
            return success
    elif event_count == 1:  # 如果表中有同一个event_id的事件，则更新数据
        try:
            sql = "update %s set last_time = '%s', alert_status = '%s', alert_id = '%s', update_time = '%s' where " \
                  "event_id = '%s';" % ('safe_sas_alert', last_time, alert_status, alert_id, now_time, event_id)
            mysql_conn.update(sql)
        except Exception as e:
            print('do sql failed %s' % e)
            return success
    else:
        print("event_id 大于1，请查询数据库数据准确性")
        return success
    mysql_conn.dispose()
    success = True
    return success


if __name__ == "__main__":
    get_sasalert_info()