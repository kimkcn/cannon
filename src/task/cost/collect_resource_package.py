#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import aliyunsdkcore
from aliyunsdkcore.acs_exception.exceptions import ClientException
from src.lib import db_mysql
try:
    import simplejson as json
except ImportError:
    import json


def collect_aliyun_resource_package(task_id=None):
    mysql_conn = db_mysql.MyPymysqlPool()
    table_name = 'cost_resource_package'
    cost_item_id = 1

    from src.lib.cloud import aliyun_api
    try:
        result_json = aliyun_api.AliyunApi().query_resource_package()
        result_total = json.loads(result_json, encoding='utf-8')
        tmp_result = result_total['Data']['Instances']['Instance']
        #print(tmp_result)
    except aliyunsdkcore.acs_exception.exceptions.ServerException:
        print("aliyunsdkcore.acs_exception.exceptions.ServerException")
    except:
        print("except")
    else:
        if len(tmp_result) == 0:
            return True
        # 获取db中数据，只选取状态有效 + 扣费类型不为总量恒定型
        sql = "select * from %s;" % table_name
        db_result = mysql_conn.select(sql)

        for record in tmp_result:
            #print(record)
            deduct_type = record['DeductType']
            status = record['Status']
            package_id = record['InstanceId']
            package_name = record['Remark']
            package_type = record['PackageType']
            support_product = json.dumps(record['ApplicableProducts']['Product'])
            total_amount = float(record['TotalAmount'])
            total_amount_unit = record['TotalAmountUnit']
            remaining_amount = float(record['RemainingAmount'])
            remaining_amount_unit = record['RemainingAmountUnit']
            effective_time = record['EffectiveTime']
            expiry_time = record['ExpiryTime']
            update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

            if status == 'Available' and remaining_amount < 0.01:
                status = 'Useup'
            insert_sql = "INSERT INTO %s(cost_item_id,package_id,package_name,package_type,status," \
                         "support_product,total_amount,total_amount_unit,remaining_amount,remaining_amount_unit," \
                         "deduct_type,effective_time,expiry_time,update_time) VALUES " \
                         "(%s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', %s, '%s', '%s', '%s', '%s', '%s');" % \
                         (table_name,cost_item_id,package_id,package_name,package_type,status,support_product,
                          total_amount,total_amount_unit,remaining_amount,remaining_amount_unit,deduct_type,
                          effective_time,expiry_time,update_time)
            #print(sql)
            if not db_result:
                result = mysql_conn.insert(insert_sql)
                continue
            update = False
            for db_record in db_result:
                db_record_id = int(db_record[0])
                db_package_id = db_record[2]
                db_status = db_record[5]
                db_remaining_amount = db_record[9]

                if package_id == db_package_id:
                    update = True
                    if db_status == 'Useup' or db_status == 'Expired' or deduct_type == 'Absolute':
                        break
                    elif db_remaining_amount == remaining_amount:
                        break
                    # update
                    #print(db_package_id, db_remaining_amount, package_id, remaining_amount)
                    if remaining_amount < 0.01 and db_status == 'Available':
                        status = 'Useup'
                    sql = "UPDATE %s set status = '%s', remaining_amount = '%s', remaining_amount_unit = '%s' where " \
                          "id = %s" % (table_name, status, remaining_amount, remaining_amount_unit, db_record_id)
                    result = mysql_conn.update(sql)
                    break
            if not update:
                result = mysql_conn.insert(insert_sql)
    mysql_conn.dispose()
    return True


if __name__ == "__main__":
    collect_aliyun_resource_package()
