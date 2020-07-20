#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import os
import configparser
from src.lib import db_mysql
try:
    import simplejson as json
except ImportError:
    import json

file_path = os.path.join(os.path.dirname(__file__), "../../../conf/key.conf")
cf = configparser.ConfigParser()
cf.read(file_path)
table_name = 'cost_account_balance'


def query_account_balance(task_id=None):
    import aliyunsdkcore
    from aliyunsdkcore.acs_exception.exceptions import ClientException
    mysql_conn = db_mysql.MyPymysqlPool()
    for ak_section in cf.sections():
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        if ak_section.startswith('aliyun') or ak_section.startswith('tencentcloud'):
            try:
                accessid = cf.get(ak_section, 'AccessKeyId')
                accesssecret = cf.get(ak_section, 'AccessKeySecret')
                regionid = cf.get(ak_section, 'DefaultRegionId')
                cost_item_id = cf.get(ak_section, 'CostItemId')
            except Exception as e:
                print("except, reason: %s" % e)
                continue

            if ak_section.startswith('aliyun'):
                cloud_type = 'aliyun'
                from src.lib.cloud import aliyun_api
                try:
                    result_json = aliyun_api.AliyunApi(accessid, accesssecret, regionid).query_account_balance()
                    result_total = json.loads(result_json, encoding='utf-8')
                    tmp = float(result_total['Data']['AvailableAmount'].replace(',', ''))
                except aliyunsdkcore.acs_exception.exceptions.ServerException:
                    print("aliyunsdkcore.acs_exception.exceptions.ServerException")
                except Exception as e:
                    print("except, reason: %s" % e)
                else:
                    balance = tmp

            elif ak_section.startswith('tencentcloud'):
                cloud_type = 'tencentcloud'
                from src.lib.cloud import tencentcloud_api
                try:
                    result_json = tencentcloud_api.TencentCloudApi(accessid, accesssecret, regionid).query_account_balance()
                    result_total = json.loads(result_json, encoding='utf-8')
                    tmp = float(int(result_total['Balance'])/100)
                except Exception as e:
                    print("except, reason: %s" % e)
                else:
                    balance = tmp

            # 检查是否存在记录，存在则update，不存在则insert
            sql = "select * from %s where cost_item_id = '%s';" %(table_name, cost_item_id)
            print(sql)
            try:
                result = mysql_conn.select(sql)
            except Exception as e:
                print('except, reason: %s' % e)
            else:
                if result:      # update
                    record_id = result[0][0]
                    sql = "update %s set balance=%s,update_time='%s' where id='%s';" % \
                          (table_name, balance, update_time, record_id)
                    mysql_conn.update(sql)
                else:           # insert
                    sql = "insert into %s(cost_item_id, balance, update_time) values('%s', %s, '%s');" % \
                      (table_name, cost_item_id, balance, update_time)
                    mysql_conn.insert(sql)
    mysql_conn.dispose()
    return True


if __name__ == "__main__":
    query_account_balance()
