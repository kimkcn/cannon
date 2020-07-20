#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from datetime import datetime, date, timedelta
from src.lib import db_mysql
try:
    import simplejson as json
except ImportError:
    import json
from src.lib import db_mysql
mysql_conn = db_mysql.MyPymysqlPool()

pn_event_table='pn_event'
pn_event_source_data_table='pn_event_source_data'
pn_event_data_table='pn_event_data'

aliyun_host = ('opscloud-1')
aws_host = ('aws-template-2')

def get_col_and_value(dic):
    COLstr = ''  # 列的字段
    ROWstr = ''  # 行字段

    for key in dic.keys():
        COLstr = COLstr + key  + ','
        ROWstr = (ROWstr + "'%s'" + ',') % (dic[key])

    COLstr = COLstr.strip(',')
    ROWstr = ROWstr.strip(',')
    #print(COLstr,'11111',ROWstr)
    return COLstr,ROWstr

#判断源数据是否为有效的的事件，是则将数据insert到专线事件表
def analysis_insert(source_data,mark):
    if source_data:
        mysql_conn = db_mysql.MyPymysqlPool('mysql')
        for i in source_data:
            #print(i,i['clock'])
            if i['pn_node'] == 'aws-mark' or i['pn_node'] == 'aliyun-mark': #当节点为mark节点，则跳过这条源数据
                continue
            else:
                for b in source_data:   #第二次遍历源数据列表，通过是否存在相同时间的mark事件判断第一次遍历的源数据是否为有效的事件数据
                    if b['pn_node'] != mark:    #当第二次遍历节点不是为mark直接跳过
                        #print(b['pn_node'])
                        continue
                    else:
                        if i['type'] != b['type']:  #不是同一事件类型也不比较，跳过
                            continue
                        else:
                            #print('3333333333333333')
                            if abs(i['clock'] - b['clock']) >= 2:   #第一次遍历和第二次遍历的出的数据clock相差超过2秒则理解为不同时间的事件，不做判断跳过
                                continue
                            else:
                                if i['source'] != b['source']:      #判断源节点是否一致，否则不比较跳过
                                    continue
                                else:
                                    #print('111111111111111111',abs(i['clock'] - b['clock']),i['clock'])
                                    break
                else:
                    if str(i['pn_eventid']) in eventid_exists_list: #判断该有效的专线事件是否已在专线事件表中入库
                        pass
                    else:
                        key,value = get_col_and_value(i)  #将字典的key和value拆分成
                        #print(a, '11111', b)
                        try:
                            insert_event = "insert into %s( %s ) VALUES (%s);" % (pn_event_data_table,key,value)
                            print(insert_event)
                            mysql_conn.insert(insert_event)
                            #mysql_conn.end()
                        except Exception as e:
                            print(e,'insert mysql is fail!')
                            mysql_conn.dispose()
                            return False
        mysql_conn.dispose()
    return True

def get_pn_event(task_id=None):
    global start,stop,event,eventid_exists_list

    for i in range(-3, 0 ):
        mysql_conn = db_mysql.MyPymysqlPool('mysql')
        mysql_conn_dict = db_mysql.MyPymysqlPoolDict()
        eventid_exists_list = []
        yesterday = date.today() + timedelta(days=i)  # 昨天日期
        print(type(yesterday), yesterday)
        start = int(time.mktime(time.strptime(str(yesterday), '%Y-%m-%d')))
        stop = start + 86400
        status = False
        #stop = time.time()  # 当前时间的时间戳
        #start = stop - 86400    #当前时间1天前的时间戳
        #print(start,stop)

        #从源数据表中获取源为aws有关专线block和telnet异常的事件的源数据
        select_source_aws_data = "select itemid,pn_eventid,clock,r_clock,source,pn_node,type from %s where clock BETWEEN '%s' AND '%s' AND TYPE IN %s AND source = '%s';" % (pn_event_source_data_table, start, stop, (0,2), aws_host)
        # 从源数据表中获取源为aliyun有关专线block和telnet异常的事件的源数据
        select_source_aliyun_data = "select itemid,pn_eventid,clock,r_clock,source,pn_node,type from %s where clock BETWEEN '%s' AND '%s' AND TYPE IN %s AND source = '%s';" % (pn_event_source_data_table, start, stop, (0,2), aliyun_host)
        # 从专线事件表中筛选出该时段所有的异常事件数据，用于和筛选出来的源数据校验是否已入库
        select_eventid = "select %s from %s where clock BETWEEN  '%s' AND '%s';" % ('pn_eventid', pn_event_data_table, start, stop)

        print('select_source_aws_data', select_source_aws_data)
        print('select_source_aliyun_data', select_source_aliyun_data)

        try:
            eventid_exists = mysql_conn.select(select_eventid)
            source_aws_data = mysql_conn_dict.select(select_source_aws_data)
            source_aliyun_data = mysql_conn_dict.select(select_source_aliyun_data)
            mysql_conn.dispose()
            mysql_conn_dict.dispose()
        except Exception as e:
            print(e,'error:get mysql is fail.')
            mysql_conn.dispose()
            mysql_conn_dict.dispose()
            return  status

        print('source_aws_data', source_aws_data)
        print('source_aliyun_data', source_aliyun_data)
        print('eventid',eventid_exists)
        if eventid_exists:
            for t in eventid_exists:
                eventid_exists_list.append(t[0])
            #print(t[0])
        eventid_exists_list = str(eventid_exists_list)
        print('eventid_exists_list',eventid_exists_list)

        if source_aliyun_data:
            aliyun_insert = analysis_insert(source_aliyun_data, 'aliyun-mark')
            if aliyun_insert:
                status = True
        if source_aws_data:
            aws_insert = analysis_insert(source_aws_data, 'aws-mark')
            if not aws_insert:
                status = False
            else:
                status = True

        if not status:
            print("error: One of aliyun_insert and aws_insert is fail with '%s' data." % (yesterday))

    return True




if __name__ == "__main__":
    get_pn_event()
