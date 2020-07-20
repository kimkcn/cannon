#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import aliyunsdkcore
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcms.request.v20190101.DescribeAlertHistoryListRequest import DescribeAlertHistoryListRequest
from aliyunsdkslb.request.v20140515.DescribeLoadBalancerAttributeRequest import DescribeLoadBalancerAttributeRequest
import time, datetime
import sys, os
import configparser
sys.path.append("..")
sys.path.append("../../")
from conf import alert_conf
from src.lib import db_mysql

try:
    import simplejson as json
except ImportError:
    import json

file_path = os.path.join(os.path.dirname(__file__), "../../../conf/key.conf")
cf = configparser.ConfigParser()
cf.read(file_path)
ak_section = "aliyun_master"
accessid = cf.get(ak_section, 'AccessKeyId')
accesssecret = cf.get(ak_section, 'AccessKeySecret')
regionid = cf.get(ak_section, 'DefaultRegionId')
client = AcsClient(accessid, accesssecret, regionid)
page_size = 100     # 单个页面的最大告警条数


def get_LoadBalancerName(loadbalancerid):    # 通过slb api获取loadbalancername
    request = DescribeLoadBalancerAttributeRequest()
    request.set_accept_format('json')
    request.set_LoadBalancerId(loadbalancerid)
    loadbalancername = ''
    try:
        response = client.do_action_with_exception(request)
    except aliyunsdkcore.acs_exception.exceptions.ServerException:
        print("aliyunsdkcore.acs_exception.exceptions.ServerException")
    except:
        print("except")
    else:
        result = json.loads(response, encoding='utf-8')
        loadbalancername = result['LoadBalancerName']

    return loadbalancername

def get_aliyun_alert(page=1):
    request = DescribeAlertHistoryListRequest()
    request.set_accept_format('json')

    # 云监控接口需求的unix时间戳为ms，而time函数的值是s，因此数值*1000
    starttime_format = datetime.datetime.now()-datetime.timedelta(hours=alert_conf.last_hours)
    starttime = int(time.mktime(starttime_format.timetuple())*1000)
    now = int(time.time()*1000)
    #starttime = 1583841600000
    #now = 1583899200000
    request.set_StartTime(starttime)
    request.set_EndTime(now)
    request.set_Page(page)
    request.set_PageSize(page_size)
    request.set_Ascending(True)

    try:
        alert_json = client.do_action_with_exception(request)
        aliyun_alert_total = json.loads(alert_json, encoding='utf-8')
        total = aliyun_alert_total['Total']
    except aliyunsdkcore.acs_exception.exceptions.ServerException:
        print("aliyunsdkcore.acs_exception.exceptions.ServerException")
        aliyun_alert_total = {}
    except:
        print("except")
        aliyun_alert_total = {}

    return aliyun_alert_total


def check_record_exist(sql):
    # True = 记录已存在
    mysql_conn = db_mysql.MyPymysqlPool()
    try:
        result = mysql_conn.select(sql)
    except Exception as e:
        print(e)
    else:
        if result:
            return True
        else:
            return False
    finally:
        mysql_conn.dispose()


def aliyun_alert_handler(task_id=None):
    mysql_conn = db_mysql.MyPymysqlPool()
    aliyun_alert_total = get_aliyun_alert()
    aliyun_alert_list_filter = []
    status = False      # 默认未采集到数据
    alert_from = 'aliyun'

    if not aliyun_alert_total:
        return aliyun_alert_list_filter, status

    count = int(aliyun_alert_total['Total'])//page_size+1      # 分页数量

    for page in range(1, count+1):    # 分页获取告警数据
        # 逐条分析json中的报警数据
        aliyun_alert_total = get_aliyun_alert(page)
        for i in range(3):
            try:
                tmp = aliyun_alert_total['AlarmHistoryList']['AlarmHistory']
            except:
                if i == 2:
                    return False
                time.sleep(5)
                continue
        status = True
        for single_alert in aliyun_alert_total['AlarmHistoryList']['AlarmHistory']:
            production = single_alert['Namespace'].split('acs_')[1]
            priority = single_alert['Level']
            state = single_alert['Status']
            alert_time = int(single_alert['AlertTime']/1000)

            if production in alert_conf.black_list:        # 不统计黑名单产品的告警
                continue
            if state != 0:      # 阿里云告警状态，0表示告警或恢复，非0不需要关注
                continue

            if priority == 'P4':        # 不统计P4级别告警
                level = 3
                continue
            elif priority == 'P3':
                level = 2
            elif priority == 'P2':
                level = 1
            else:
                level = 0

            rule_name = single_alert['RuleName']
            metric = single_alert['MetricName']
            expression = single_alert['Expression']
            current_state = single_alert['State']
            Dimensions = single_alert['Dimensions']
            instancename = single_alert['InstanceName']
            resource = "%s  InstanceName: %s" % (Dimensions, instancename)

            # 反查slb获得LoadBalancerName
            if production == "slb":
                loadbalancerid = json.loads(single_alert['Dimensions'].encode('utf-8'))['instanceId']
                port = json.loads(single_alert['Dimensions'].encode('utf-8'))['port']
                loadbalancername = get_LoadBalancerName(loadbalancerid)
                resource = "instanceid: %s, port: %s, LoadBalancerName: %s" %(loadbalancerid, port, loadbalancername)
            elif production == "ecs":
                instanceid = json.loads(single_alert['Dimensions'].encode('utf-8'))['instanceId']
                resource = "instanceid: %s, InstanceName: %s" % (instanceid, instancename)

            start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(alert_time))
            tmp_result = "%s %s" %(rule_name, metric)
            alert_detail = tmp_result
            alert_value = float('%.2f' %float(single_alert['Value']))

            '''
            判断本条是告警，还是恢复
            是告警，则:
                1、判断 a + state 是否一致，一致to1.1，不一致to2
                    1.1、判断 a + expression + state是否一致，一致跳过，不一致写入一条新的
                2、判断 a + expression + start_time是否一致，确认是否同一条记录反复写，一致跳过，不一致to2.1
                    2.1 取 a + expression + state = 'OK' 最后一条记录，对比时间，如果本条时间在OK这条的结束时间之前，则跳过，如果在之后，则写入
            是恢复，判断下本条恢复的级别
                则找寻之前处于告警状态的这个告警项，production + resource + alert_detail + status(告警) + start_time < 本条时间的，将其置为正常
            '''

            print(single_alert)
            insert_sql = "insert into %s(alert_from,production,resource,current_state,alert_detail,expression," \
                         "alert_value,start_time,priority) values('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %s)" \
                         % (alert_conf.table_name, alert_from, production, resource, current_state, alert_detail, expression,alert_value, start_time, level)
            if current_state == 'ALARM':
                sql = "select * from %s where production = '%s' and resource = '%s' and alert_detail = '%s' and current_state = '%s' limit 1;" % (
                    alert_conf.table_name, production, resource, alert_detail, current_state)
                result = check_record_exist(sql)        # 检查记录在数据库中是否已存在, True = 这条记录在数据库中存在
                if result:
                    # 增加expression是否一致的判断
                    sql = "select * from %s where production = '%s' and resource = '%s' and alert_detail = '%s' and expression = '%s' and current_state = '%s' limit 1;" % (
                        alert_conf.table_name, production, resource, alert_detail, expression, current_state)
                    result = check_record_exist(sql)
                    if not result:
                        result = mysql_conn.insert(insert_sql)
                else:
                    # 判断 + expression + start_time是否一致
                    sql = "select * from %s where production = '%s' and resource = '%s' and alert_detail = '%s' and expression = '%s' and start_time = '%s' limit 1;" % (
                        alert_conf.table_name, production, resource, alert_detail, expression, start_time)
                    result = check_record_exist(sql)
                    if not result:
                        # 取最后一条ok的记录，解决记录重复问题
                        sql = "select * from %s where resource='%s' and alert_detail='%s' and expression='%s' and current_state='OK' order by start_time desc limit 1" % \
                              (alert_conf.table_name, resource, alert_detail, expression)
                        result = mysql_conn.select(sql)
                        if result:
                            last_ok_record_endtime = int(time.mktime(result[0][10].timetuple()))
                            if alert_time > last_ok_record_endtime:
                                result = mysql_conn.insert(insert_sql)
                        else:
                            result = mysql_conn.insert(insert_sql)
            elif current_state == 'OK':
                # 找寻之前处于告警状态的此告警项，production + resource + alert_detail + status(告警) + start_time < 本条时间的，将其置为正常
                sql = "select * from %s where production = '%s' and resource = '%s' and alert_detail = '%s' and current_state = 'ALARM' and start_time < '%s'" %\
                      (alert_conf.table_name, production, resource, alert_detail, start_time)
                result = mysql_conn.select(sql)
                if result:
                    for single in result:
                        record_id = single[0]
                        end_time = start_time    # 上一条的结束时间，等于本条的开始时间
                        sql = "UPDATE %s SET current_state='%s', alert_value=%s, end_time='%s' WHERE id=%s" % (alert_conf.table_name, current_state, alert_value, end_time, record_id)
                        result = mysql_conn.update(sql)
            aliyun_alert_list_filter.append(single_alert)

    # 当前线程的sql任务结束，提交或回滚
    mysql_conn.dispose()
    #print(status, aliyun_alert_list_filter)
    return status, aliyun_alert_list_filter


if __name__ == "__main__":
    aliyun_alert_handler()