#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 监控启停接口，用于发布时控制机器的监控启停，并数据入库

import sys, time
from src.lib import zabbix_api
from src.lib import db_mysql
from django.http import HttpResponse
sys.path.append("../../")
from conf import alert_conf
try:
    import simplejson as json
except ImportError:
    import json


def zabbix_monitor_switch(request):
    action = int(request.GET['action'])
    hostip = request.GET['privateIp']
    zabbix_ak = request.GET['ak']
    success = False
    code = 500
    message = 'fail'
    result_dict = {'code': code, 'success': success, 'message': message}
    mysql_conn = db_mysql.MyPymysqlPool()

    if zabbix_ak != '1d42ee7b99a7d92bdbdaccc3edc30a9f' or action not in [0, 1]:
        result_dict['message'] = 'Args error!'
        result_json = json.dumps(result_dict, ensure_ascii=False)
        return HttpResponse(result_json, content_type="application/json,charset=utf-8")

    retry = 0

    zabbix = zabbix_api.ZabbixApi()
    while retry < 3:
        if action == 1:
            action_name = 'enable'
            result = zabbix.host_enable(hostip)
        else:   # action == 0
            action_name = 'disable'
            result = zabbix.host_disable(hostip)

        if not result:
            result_dict['message'] = '%s %s 失败!' % (action_name, hostip)
            result_json = json.dumps(result_dict, ensure_ascii=False)
            return HttpResponse(result_json, content_type="application/json,charset=utf-8")

        result_dict['code'] = 200
        result_dict['success'] = True
        result_dict['message'] = '%s %s 成功!' % (action_name, hostip)

        # 监控启停的操作记录入库
        action_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        host_name = zabbix.get_hostname_with_hostip(hostip)

        if not host_name:
            result_dict['message'] = '通过zabbix_api获取hostname失败!'
            result_json = json.dumps(result_dict, ensure_ascii=False)
            return HttpResponse(result_json, content_type="application/json,charset=utf-8")

        sql = "insert into %s(host_ip, host_name, action, time) values('%s', '%s', '%s', '%s')" %\
              (alert_conf.zabbix_switch_table, hostip, host_name, action_name, action_time)
        try:
            result = mysql_conn.insert(sql)
        except Exception as e:
            result_dict['message'] = '写入操作记录失败!'
        else:
            result_dict['message'] = '%s %s, 所有动作完成, 最终成功!' % (action_name, hostip)
            break
        retry += 1
        time.sleep(2)
    mysql_conn.dispose()
    result_json = json.dumps(result_dict, ensure_ascii=False)
    return HttpResponse(result_json, content_type="application/json,charset=utf-8")


if __name__ == "__main__":
    zabbix_monitor_switch('xxx')
