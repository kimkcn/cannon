#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from datetime import datetime, date, timedelta
try:
    import simplejson as json
except ImportError:
    import json
import pymysql
from conf import pn_problem_collect_conf
from src.lib import db_mysql
from src.lib import zabbix_api
zabbix = zabbix_api.ZabbixApi()

item_name_delay = pn_problem_collect_conf.item_name_delay
pn_event_delay_data_table = 'pn_event_delay_data'

def get_itemid(hostip,source):
    status = False
    try:
        result = zabbix.get_item_with_hostip(hostip)
        #print('item_result',result)
    except Exception as e:
        print('error:get itemid api is fail!')
    else:
        if not result:
            print('error:get itemid api is null ;')
            return status
        try:
            item_info = result['result']
            # print('item_info',item_list)
        except:
            return status
        if not item_info:
            print('warn:item result is null ;')
            return status
        #itemid = item_info[0]['itemid']
        #print(len(item_info),item_info)
        for i in item_info:
            if i['name'] not in item_name_delay:
                #print(i['name'])
                item_info.remove(i)
            elif source == 'aliyun':
                if i['name'] in  ['opscloud-2-ping', 'opscloud-1-ping']:
                    #print(i['name'])
                    item_info.remove(i)
            elif source == 'aws':
                if i['name'] in  ['proxy-aws.zabbix.ops.yangege.cn-ping', 'aws-template-3-ping']:
                    #print(i['name'])
                    item_info.remove(i)
            item_info = list(item_info)
        return item_info

def insert_event_delay_data(item_result,start,stop,source_node):
    for a in item_result:
        pn_node = a['name'][:-5]    #获取节点名称   去掉字符串末尾5个字符
        print(pn_node)
        #history_result = zabbix.get_history(a['itemid'],start,stop)
        try:
            conn = pymysql.connect(host='47.99.229.254', user='zabbix', passwd='zabbix', port=10029, db='zabbix',charset='utf8')
            cur = conn.cursor(cursor=pymysql.cursors.DictCursor)  # 生成游标对象
            select_history = "SELECT * FROM %s WHERE clock BETWEEN %s and %s AND itemid = %s ORDER BY `value` DESC;" % ('history', start, stop, a['itemid'])
            print('select_history',select_history)
            cur.execute(select_history)
            rows = cur.fetchall()
            cur.close()  # 关闭游标
            conn.close()  # 关闭连接

        except Exception as e:
            print(e, 'error:select history is fail!!!')
            return False
        else:
            if not rows:
                print('error:select history is null.')
                return True
            #print(len(history_result),history_result)
            print(len(rows))

            s = 0
            n = 0
            for r in rows:
                if r['value'] != 0:     #判断该clock点的icmp的值是否为0，为0则跳过继续遍历
                    s = s +  r['value']
                    n = n + 1
            if n == 0 or n < 10000:      #判断有效icmp值的个数是否为0或10000；满足则认为该天的icmp监控存在异常，需人为分析
                print('The number of valid values is less than 10000. ',n)
                return True
            else:
                print('s and n',s,n)
                valueAvg = format(s / n , '.4f')
            one_day = n
            percent50 = int(one_day - (one_day * 0.5))
            percent60 = int(one_day - (one_day * 0.6))
            percent70 = int(one_day - (one_day * 0.7))
            percent80 = int(one_day - (one_day * 0.8))
            percent90 = int(one_day - (one_day * 0.9))
            percent95 = int(one_day - (one_day * 0.95))
            percent96 = int(one_day - (one_day * 0.96))
            percent97 = int(one_day - (one_day * 0.97))
            percent98 = int(one_day - (one_day * 0.98))
            percent99 = int(one_day - (one_day * 0.99))
            percent9999 = int(one_day - (one_day * 0.9999))
            print(percent9999,percent99,percent98,percent97,percent96,percent95,percent90,percent80,percent70,percent60,percent50)

            valueMax = rows[0]['value']
            valueA = rows[percent9999]['value']
            valueB = rows[percent99]['value']
            valueC = rows[percent98]['value']
            valueD = rows[percent97]['value']
            valueE = rows[percent96]['value']
            valueF = rows[percent95]['value']
            valueG = rows[percent90]['value']
            valueH = rows[percent80]['value']
            valueI = rows[percent70]['value']
            valueJ = rows[percent60]['value']
            valueK = rows[percent50]['value']
            print('valueAvg',valueAvg,valueMax,valueA,valueB,valueC,valueD,valueE,valueF,valueG,valueH,valueI)

            select_delay_data =  "SELECT * FROM %s WHERE date = '%s' AND itemid = '%s' ;" % (pn_event_delay_data_table, yesterday, a['itemid'])
            print(select_delay_data)
            try:
                mysql_conn = db_mysql.MyPymysqlPool('mysql')
                select_delay_data_result = mysql_conn.select(select_delay_data)
                print('select_delay_data_result',select_delay_data_result)
            except Exception as e:
                print(e,'error:select delay_data is fail!!!')
            else:
                if not select_delay_data_result:
                    insert_delay_data_result = "insert into %s(date,valueAvg,valueMax,valueA,valueB,valueC,valueD,valueE,valueF,valueG,valueH,valueI,valueJ,valueK,source,PNnode,itemid) " \
                                              "values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % (
                                                pn_event_delay_data_table, yesterday,valueAvg,valueMax,valueA,valueB,valueC,valueD,valueE,valueF,valueG,valueH,valueI,valueJ,valueK,source_node,pn_node,a['itemid'])
                    print('insert_delay_data_result',insert_delay_data_result)
                    try:
                        mysql_conn.insert(insert_delay_data_result)
                        #print('123123')
                    except Exception as e:
                        print(e,'error:insert pn_event_delay_data_table is fail!!! ')
            mysql_conn.dispose()
    return True

def get_pn_event_delay_data(task_id=None):
    global start,stop,yesterday
    global stop

    for i in range(-3, 0 ):
        yesterday = date.today() + timedelta(days= i)  # 昨天日期
        print(type(yesterday),yesterday)
        start = int(time.mktime(time.strptime(str(yesterday), '%Y-%m-%d')))
        stop = start + 86400
        #print('end_time',start,stop)

        hostip = ['192.168.10.90','172.17.33.53']
        status = False

        try:
            aliyun_item_result = get_itemid(hostip[0],'aliyun')
            aws_item_result = get_itemid(hostip[1],'aws')
        except Exception as e:
            print('error:get itemid is fail!!!')
            return  status
        else:
            if not aliyun_item_result or not aws_item_result:
                print('One of aliyun_item_result and aws_item_result is empty ;')
                return status
            else:
                #print(len(aliyun_item_result),len(aws_item_result), aliyun_item_result)
                if len(aliyun_item_result) != 10 or len(aws_item_result) != 10:
                    print('error:get item quantity is wrong!')
                    return status
            #print(len(aliyun_item_result),len(aws_item_result),aliyun_item_result)
            aliyun_insert = insert_event_delay_data(aliyun_item_result, start, stop, 'aliyun')
            aws_insert = insert_event_delay_data(aws_item_result, start, stop, 'aws')

            if not aliyun_insert or not aws_insert:
                print("error: One of aliyun_insert and aws_insert is fail with '%s' data." %(yesterday))
                return status
    return True



if __name__ == "__main__":
    get_pn_event_delay_data()
