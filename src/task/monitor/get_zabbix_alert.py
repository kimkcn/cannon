#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
print(sys.path)
from conf import alert_conf
try:
    import simplejson as json
except ImportError:
    import json

from src.lib import db_mysql
from src.lib import zabbix_api


def zabbix_alert_handler(task_id=None):
    mysql_conn = db_mysql.MyPymysqlPool()
    zabbix = zabbix_api.ZabbixApi()
    result = zabbix.get_trigger()
    print(result)
    alert_list = []
    status = False      #默认未采集到数据

    if not result:
        return alert_list, status
    try:
        alert_list = result['result']
    except:
        return alert_list, status

    # 提前获取数据库中的所有在报警状态的zabbix告警记录
    sql = "select * from %s where alert_from = 'zabbix' and current_state = 'ALARM' order by start_time desc;" % (alert_conf.table_name)
    db_zabbix_result = mysql_conn.select(sql)
    zabbix_result = []
    status = True
    alert_list_filter = []
    for single_alert in alert_list:
        try:
            priority = single_alert['priority']
            if priority == '2':
                level = 3
                continue
            elif priority == '3' or priority == '4':
                level = 2
            elif priority == '5':
                level = 1
            description = single_alert['description']
            resource = single_alert['hosts'][0]['host']
            expression = single_alert['expression']
            start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(single_alert['lastchange'])))
            alert_detail = "%s" %(description)
            current_state = "ALARM"
            alert_from = "zabbix"
            production = "ecs"
        except:
            print("error!")
            continue
        else:
            alert_list_filter.append(single_alert)

        tmp = [production, resource, alert_detail, expression]
        zabbix_result.append(tmp)

        '''检查production、resource、alert_detail是否有重复
        如果不重复，直接写入db
        如果有重复，例如同一个触发器连续报警，需要检查之前最后一条的报警状态：
                if 之前状态是恢复，本次是告警，则直接写入db
                if 之前状态是告警，本次是告警，则跳过。'''

        insert_new_record_sql = "insert into %s(alert_from,production,resource,current_state,alert_detail,expression,start_time,priority) " \
                                "values('%s','%s','%s','%s','%s','%s','%s','%s')" % \
                                (alert_conf.table_name,alert_from,production,resource,current_state,alert_detail,expression,start_time,level)

        # 判断产品+资源+告警详情是否重复
        sql = "select * from %s where production = '%s' and resource = '%s' and alert_detail = '%s' limit 1;" % (alert_conf.table_name, production, resource, alert_detail)
        result = mysql_conn.select(sql)
        if not result:  # 不重复，则写入这条告警
            mysql_conn.insert(insert_new_record_sql)
        else:
            # 再增加一个时间的判断
            sql = "select * from %s where production='%s' and resource='%s' and alert_detail='%s' and start_time='%s' limit 1;" % (
            alert_conf.table_name, production, resource, alert_detail, start_time)
            result = mysql_conn.select(sql)
            if result:  # 记录已存在
                continue

            sql = "select * from %s where production = '%s' and resource = '%s' and alert_detail = '%s' order by " \
                  "start_time desc limit 1" % (alert_conf.table_name, production, resource, alert_detail)
            result = mysql_conn.select(sql)
            last_state = result[0][5]

            if last_state == "ALARM" and current_state == "ALARM":
                continue
            elif last_state == "OK" and current_state == "ALARM":
                mysql_conn.insert(insert_new_record_sql)

    '''
    获取db中所有报警状态的zabbix报警项，和当前报警项做对比
    如果存在，则跳过
    如果不存在，则update该项状态，置为恢复，并获取当前时间，置为该条的结束时间
    '''
    if db_zabbix_result:
        for record in db_zabbix_result:
            record_id_in_db = record[0]
            production_in_db = record[2]
            resource_in_db = record[4]
            alert_detail_in_db = record[6]
            expression_in_db = record[7]
            result = False
            for i in zabbix_result:
                current_production = i[0]
                current_resource = i[1]
                current_alert_detail = i[2]
                current_expression = i[3]
                if production_in_db == current_production and resource_in_db == current_resource and \
                        alert_detail_in_db == current_alert_detail and expression_in_db == current_expression:
                    result = True
                    break
            if not result:
                end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                sql = "UPDATE %s SET current_state='OK', end_time='%s' WHERE id=%s" % (alert_conf.table_name, end_time, record_id_in_db)
                mysql_conn.update(sql)
    mysql_conn.dispose()
    #print(status, alert_list_filter)
    return status, alert_list_filter


if __name__ == "__main__":
    zabbix_alert_handler()
