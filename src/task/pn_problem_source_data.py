#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
try:
    import simplejson as json
except ImportError:
    import json
from conf import pn_problem_collect_conf
from src.lib import db_mysql
from src.lib import zabbix_api
from conf import cannon_conf
#mysql_conn = db_mysql.MyPymysqlPool()
zabbix = zabbix_api.ZabbixApi()
hostip_list = pn_problem_collect_conf.hostip_list
pn_node_list = pn_problem_collect_conf.pn_node_list
trigger_delay = pn_problem_collect_conf.trigger_delay
trigger_block = pn_problem_collect_conf.trigger_block
trigger_telnet = pn_problem_collect_conf.trigger_telnet
template_name = pn_problem_collect_conf.template_name

pn_event_table='pn_event'
pn_event_source_data_table='pn_event_source_data'
pn_event_history_table='pn_event_history'

task_log_file = cannon_conf.task_manage_log
#start = time.strptime('2020-05-11 16:56:15', "%Y-%m-%d %H:%M:%S")
#stop = time.strptime('2020-05-17 21:12:15', "%Y-%m-%d %H:%M:%S")
#start = int(time.mktime(start))
#stop = int(time.mktime(stop))
eventid_list = []


def get_itemid(triggerid):
    status = False
    result = zabbix.get_item(triggerid)
    # print('result',triggerid,result)

    if not result:
        return status
    try:
        item_info = result['result']
        # print('item_info',item_list)
    except:
        return status
    if not item_info:
        return status
    itemid = item_info[0]['itemid']
    return itemid

def get_templateid(template_name):
    status = False
    result = zabbix.get_template(template_name)
    template_info = []
    if not result:
        return template_info, status
    try:
        template_info = result['result']
    except:
        return template_info, status
    #print(template_info[0]['templateid'])
    return template_info[0]['templateid']

def get_eventids(triggerid_info):
    eventid_info = []
    for key in triggerid_info:
        event_info = zabbix.get_event(triggerid_info[key], start, stop)
        # print('event_info',event_info)
        if not event_info:
            return event_info, 'event is null'
        try:
            event_info = event_info['result']
        except:
            return event_info
        if event_info:
            # print('event_info',event_info)
            for event in event_info:
                # print(event['name'],event['eventid'])
                eventid_info.append(event['eventid'])
    print('eventid_info', eventid_info)
    return eventid_info

def get_porblem_info(eventids):
    problem_info = []
    for eventid_d in eventids:
        problem_data = zabbix.get_problem(eventid_d)
        if not problem_data:
            return problem_data,  'problem is null'
        try:
            problem_data = problem_data['result']
            # print('problem_data',problem_data)
        except:
            return problem_data
        if problem_data:
            problem_info.append(problem_data)
    return problem_info

def insert_event_source_data(problem_info,triggerid_info,event_type,hostname):
    mysql_conn = db_mysql.MyPymysqlPool('mysql')
    for pi in problem_info:
        select_eventid_sql = "select * from %s where pn_eventid = '%s';" % (pn_event_source_data_table, pi[0]['eventid'])
        result = mysql_conn.select(select_eventid_sql)  # 根据传入的eventid值来匹配数据
        #print('pi',pi,result)
        if not result:
            #print('mei you chong fu shu ju le')
            node_name = pi[0]['name'].split(' ', )[0]
            if node_name == hostname or pi[0]['r_clock'] == '0':
                #print('test shi fou xiang deng')
                break

            for key in triggerid_info:
                #print('triggerid_info',triggerid_info,pi[0]['name'])
                if key == pi[0]['name']:
                    triggerid = triggerid_info[key]
                    itemid01 = get_itemid(triggerid)
                    #print('itemid01',itemid01)
                    sql_insert_problem_info = "insert into %s(pn_eventid,clock,r_clock,pn_node,type,itemid,source) " \
                                      "values('%s','%s','%s','%s','%s','%s','%s')" % (
                                          pn_event_source_data_table, pi[0]['eventid'], pi[0]['clock'], pi[0]['r_clock'],
                                          node_name, event_type, itemid01, hostname)
                    mysql_conn.insert(sql_insert_problem_info)
    mysql_conn.dispose()

def get_pn_event_source_data(task_id=None):
    global start
    global stop
    stop = time.time()  # 当前时间的时间戳
    print('当前时间',time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) )
    start = stop - 168800  # 当前时间3小时前的时间戳
    status = False
    if pn_node_list.__len__() != 12:
        return False

    for hostip in hostip_list:
        hostname = zabbix.get_hostname_with_hostip(hostip)
        print('hostname',hostname)
        triggers_get = zabbix.get_pn_trigger(hostip)
        if not triggers_get:
            return triggers_get, status, 'trigger is null'
        try:
            triggers_get = triggers_get['result']
            print('triggers_get',triggers_get)
        except:
            print("get trigger is  error")
            return False,
        #print('triggers_info',triggers_info)
        #triggerid_delay = {}
        triggerid_block = {}
        triggerid_telnet = {}
        for i in triggers_get:
            #for d in trigger_delay:
                #if d == i['description']:
                    #triggerid_delay[d] = i['triggerid']
            for b in trigger_block:
                if b == i['description']:
                    triggerid_block[b] = i['triggerid']
            for t in trigger_telnet:
                if t == i['description']:
                    triggerid_telnet[t] = i['triggerid']

        #eventid_delay = get_eventids(triggerid_delay)
        eventid_block = get_eventids(triggerid_block)
        eventid_telnet = get_eventids(triggerid_telnet)
        #print('triggerid_block',triggerid_block)
        #print('triggerid_telnet',triggerid_telnet)


        #problem_delay_info = get_porblem_info(eventid_delay)
        problem_block_info = get_porblem_info(eventid_block)
        problem_telnet_info = get_porblem_info(eventid_telnet)
        #print('problem_delay_info',problem_delay_info)
        #print('problem_block_info',problem_block_info)
        #print('problem_telnet_info',problem_telnet_info)

        #insert_event_source_data(problem_delay_info,triggerid_delay,1,hostname)
        insert_event_source_data(problem_block_info,triggerid_block,0,hostname)
        insert_event_source_data(problem_telnet_info,triggerid_telnet,2,hostname)

    return True

if __name__ == "__main__":
    get_pn_event_source_data()
