#!/usr/bin/env python3
# coding:utf-8
import os
import math
import json
from datetime import datetime

# 项目的lib
from src.lib.cloud import aliyun_api
from src.lib import db_mysql
mysql_conn = db_mysql.MyPymysqlPool()


def get_vul_info(task_id=False):
    type_list = ['cve', 'sys', 'cms', 'app', 'emg']
    for vul_type in type_list:
        get_total_page(vul_type)


def get_total_page(vul_type):
    format = 'json'
    dealed = 'n'
    page = 1
    limit = 20

    response = aliyun_api.AliyunApi().describe_vul_list(format, vul_type, dealed, page, limit)
    result = json.loads(response, encoding='utf-8')
    total_count = result['TotalCount']

    total_page = math.ceil(total_count/limit) # 获取总页数

    get_info(total_page, limit, vul_type, dealed)

def get_info(total_page, limit, vul_type, dealed):
    page = 1
    while page <= total_page:
        response = aliyun_api.AliyunApi().describe_vul_list(format, vul_type, dealed, page, limit)
        result = json.loads(response, encoding='utf-8')

        vul = result['VulRecords']
        for i in  vul:
            vul_id = i['PrimaryId']
            vul_type = i['Type']
            vul_name = i['Name']
            vul_aliasname = i['AliasName']
            vul_tag = i['Tag']
            vul_firsttime = datetime.fromtimestamp(float(i['FirstTs']/1000))
            vul_lasttime = datetime.fromtimestamp(float(i['LastTs']/1000))
            vul_status = i['Status']
            vul_necessity = i['Necessity']
            try:
                instance_id = i['InstanceId']
                instance_name = i['InstanceName']
            except:
                instance_id = None
                instance_name = None
            try:
                pub_ip = i['InternetIp']
            except:
                pub_ip = None
            try:
                pri_ip = i['IntranetIp']
            except:
                pri_ip = None

            update_sql(vul_id, vul_type, vul_name, vul_aliasname, vul_tag, vul_firsttime, vul_lasttime, vul_status, vul_necessity, instance_id, instance_name, pub_ip, pri_ip)
        page += 1

def update_sql(vul_id, vul_type, vul_name, vul_aliasname, vul_tag, vul_firsttime, vul_lasttime, vul_status, vul_necessity, instance_id, instance_name, pub_ip, pri_ip):
    sql = "select count(*) from %s where vul_id = '%s'" % ('safe_sas_vul', vul_id)
    result = mysql_conn.select(sql)
    vulid_count = result[0][0]
    if vulid_count == 0:
        sql = "insert into %s(vul_id, vul_type, vul_name, vul_aliasname, vul_tag, vul_firsttime, vul_lasttime, vul_status, vul_necessity, instance_id, instance_name, pub_ip, pri_ip ) values('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
              ('safe_sas_vul', vul_id, vul_type, vul_name, vul_aliasname, vul_tag, vul_firsttime, vul_lasttime, vul_status, vul_necessity, instance_id, instance_name, pub_ip, pri_ip)
        mysql_conn.insert(sql)
        mysql_conn.end()
    elif vulid_count == 1:
        sql = "select vul_lasttime, vul_status, vul_necessity, instance_name, pub_ip, pri_ip from %s where vul_id = '%s'" % ('safe_sas_vul', vul_id)
        result = mysql_conn.select(sql)
        old_vul_lasttime = result[0][0]
        old_vul_status = result[0][1]
        old_vul_necessity = result[0][2]
        old_instance_name = result[0][3]
        old_pub_ip = result[0][4]
        old_pri_ip = result[0][5]

        if old_vul_lasttime != vul_lasttime or old_vul_status != vul_status or old_vul_necessity != vul_necessity or old_instance_name != instance_name or old_pub_ip != pub_ip or old_pri_ip != pri_ip :
            sql = "update %s set vul_lasttime = '%s', vul_status = '%s', vul_necessity = '%s', instance_name = '%s', pub_ip = '%s', pri_ip = '%s' where vul_id = '%s';" % \
                  ('safe_sas_vul', vul_lasttime, vul_status, vul_necessity, instance_name, pub_ip, pri_ip, vul_id)
            mysql_conn.update(sql)
            mysql_conn.end()
    else:
        print("vul_id 大于1，请查询数据库数据准确性")


if __name__ == "__main__":
    get_vul_info()