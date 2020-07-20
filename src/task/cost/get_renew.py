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


def iso_to_timestamp(iso_time):
    import re
    import datetime
    part_a = re.split('[TZ]', iso_time)[0]
    part_b = re.split('[TZ]', iso_time)[1]

    date_time = "%s %s" % (part_a, part_b)

    time_stamp = int(datetime.datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S").timestamp())
    #print(time_stamp)

    return time_stamp


def query_aliyun_product_renew(accessid, accesssecret, regionid, cost_item_id):
    import datetime
    import aliyunsdkcore
    from aliyunsdkcore.acs_exception.exceptions import ClientException
    from src.lib.cloud import aliyun_api
    last_day = 30
    status = False
    table_name = "cost_product_renew"

    time_part_a = (datetime.datetime.now()-datetime.timedelta(days=last_day)).strftime('%Y-%m-%d')
    time_part_b = (datetime.datetime.now()-datetime.timedelta(days=last_day)).strftime('%H:%M:%S')

    end_time_start = "%sT%sZ" % (time_part_a, time_part_b)
    end_time_end = "2199-03-23T12:00:00Z"

    # 首先查询返回的条数，以决定需要查询的页数
    pass

    try:
        result_json = aliyun_api.AliyunApi(accessid, accesssecret, regionid).query_available_instance(end_time_start, end_time_end)
        result_total = json.loads(result_json, encoding='utf-8')
        tmp_result = result_total['Data']['InstanceList']
    except aliyunsdkcore.acs_exception.exceptions.ServerException:
        print("aliyunsdkcore.acs_exception.exceptions.ServerException")
    except Exception as e:
        print("except: %s" % e)
        return status
    else:
        status = True
        if not tmp_result:
            return status

    # 获取db中数据
    mysql_conn = db_mysql.MyPymysqlPoolDict()
    sql = "select * from %s where cost_item_id = %s;" % (table_name, cost_item_id)
    db_result = mysql_conn.select(sql)

    for instance in tmp_result:
        status = instance['Status']
        subscription_type = instance['SubscriptionType']
        product_code = instance['ProductCode']
        instance_id = instance['InstanceID']
        try:
            product_type = instance['ProductType']
        except KeyError:
            product_type = ""
        try:
            sub_status = instance['SubStatus']
        except KeyError:
            sub_status = ""
        renew_status = instance['RenewStatus']
        instance_name = ""

        end_time = iso_to_timestamp(instance['EndTime'])
        create_time = iso_to_timestamp(instance['CreateTime'])

        sql = "INSERT INTO cost_product_renew (cost_item_id, instance_id, instance_name, product_code, product_type, " \
              "status, subscription_type, end_time, create_time, sub_status, renew_status) VALUES " \
              "(%s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % \
              (cost_item_id, instance_id, instance_name, product_code, product_type, status,
               subscription_type, end_time, create_time, sub_status, renew_status)

        if not db_result:
            result = mysql_conn.insert(sql)
            continue

        update = False
        for db_record in db_result:
            db_instance_id = db_record['instance_id']

            if instance_id == db_instance_id:   # instance_id一致，或者需要更新数据，或者数据一致不需要更新
                update = True
                db_id = db_record['id']
                db_status = db_record['status']
                db_subscription_type = db_record['subscription_type']
                db_end_time = db_record['end_time']
                db_sub_status = db_record['sub_status']
                db_renew_status = db_record['renew_status']

                if status == db_status and end_time == db_end_time and renew_status == db_renew_status and \
                        sub_status == db_sub_status and subscription_type == db_subscription_type:
                    break

                # update
                sql = "UPDATE %s set status = '%s', subscription_type = '%s', end_time = '%s', " \
                      "sub_status = '%s', renew_status = '%s' where id = %s" % \
                      (table_name, status, subscription_type, end_time, sub_status, renew_status, db_id)
                result = mysql_conn.update(sql)
                break
        if not update:  # insert
            result = mysql_conn.insert(sql)

    mysql_conn.dispose()
    return status


def query_renew_handler(task_id=None):
    for ak_section in cf.sections():
        if ak_section.startswith('aliyun'):
            accessid = cf.get(ak_section, 'AccessKeyId')
            accesssecret = cf.get(ak_section, 'AccessKeySecret')
            regionid = cf.get(ak_section, 'DefaultRegionId')
            cost_item_id = int(cf.get(ak_section, 'CostItemId'))
            result = query_aliyun_product_renew(accessid, accesssecret, regionid, cost_item_id)


if __name__ == "__main__":
    #iso_to_timestamp("2018-11-01T03:30:22Z")
    query_renew_handler()
