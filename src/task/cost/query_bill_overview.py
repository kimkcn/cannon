#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime, time
import configparser
import aliyunsdkcore
from aliyunsdkcore.acs_exception.exceptions import ClientException
from src.lib import db_mysql
try:
    import simplejson as json
except ImportError:
    import json

file_path = os.path.join(os.path.dirname(__file__), "../../../conf/key.conf")
cf = configparser.ConfigParser()
cf.read(file_path)
table_name = 'cost_bill_overview'


def query_aliyun_bill(accessid, accesssecret, regionid, cost_item_id):
    current_cycle = datetime.datetime.now().strftime('%Y-%m')
    last_cycle = (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).strftime('%Y-%m')
    update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

    from src.lib.cloud import aliyun_api
    for cycle in [last_cycle, current_cycle]:
        try:
            result_json = aliyun_api.AliyunApi(accessid, accesssecret, regionid).query_bill_overview(cycle)
            result_total = json.loads(result_json, encoding='utf-8')
            tmp_result = result_total['Data']['Items']['Item']
            billing_cycle = result_total['Data']['BillingCycle']
        except aliyunsdkcore.acs_exception.exceptions.ServerException:
            print("aliyunsdkcore.acs_exception.exceptions.ServerException")
        except Exception as e:
            print("except: %s" % e)
        else:
            if len(tmp_result) == 0:
                continue
            # 获取db中数据
            mysql_conn = db_mysql.MyPymysqlPool()
            sql = "select * from %s where billing_cycle = '%s' and cost_item_id = %s;" % (table_name, cycle, cost_item_id)
            db_result = mysql_conn.select(sql)

            for record in tmp_result:
                product_name = record['ProductName']
                product_code = record['ProductCode']
                product_detail = record['ProductDetail']
                product_detail_code = record['ProductType']
                pretax_amount = float(record['PretaxAmount'])
                subscription_type = record['SubscriptionType']
                bill_type = record['Item']

                insert_sql = "INSERT INTO %s(cost_item_id,product_code,product_name,product_detail_code," \
                             "product_detail,billing_cycle,pretax_amount,subscription_type,bill_type, " \
                             "update_time) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', %s, '%s', '%s', '%s');" \
                             % (table_name, cost_item_id, product_code, product_name, product_detail_code,
                                product_detail, billing_cycle, pretax_amount, subscription_type, bill_type,
                                update_time)

                if not db_result:
                    result = mysql_conn.insert(insert_sql)
                else:
                    update = False
                    for db_record in db_result:
                        db_record_id = int(db_record[0])
                        db_cost_item_id = int(db_record[1])
                        db_product_code = db_record[2]
                        db_product_detail = db_record[5]
                        db_pretax_amount = db_record[7]
                        db_subscription_type = db_record[8]
                        db_bill_type = db_record[9]

                        if cost_item_id == db_cost_item_id and product_code == db_product_code and product_detail == db_product_detail and subscription_type == db_subscription_type and bill_type == db_bill_type:
                            update = True
                            db_update_time = db_record[10]
                            db_update_time_month = datetime.datetime.strftime(db_update_time, '%Y-%m')
                            if cycle != current_cycle and db_update_time_month != cycle:
                                break
                            elif pretax_amount == db_pretax_amount:
                                break
                            # update
                            sql = "UPDATE %s set pretax_amount = '%s' where id = %s" \
                                  % (table_name, pretax_amount, db_record_id)
                            result = mysql_conn.update(sql)
                            break
                    if not update:
                        result = mysql_conn.insert(insert_sql)
    mysql_conn.dispose()
    return True


def query_tencentcloud_bill(cost_item_id):
    from src.lib.cloud import tencentcloud_api
    from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

    current_cycle = datetime.date(datetime.date.today().year, datetime.date.today().month, 1)
    last_cycle = datetime.date(datetime.date.today().year, datetime.date.today().month-1, 1)
    update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

    for cycle in [current_cycle, last_cycle]:
        cycle_first_day = (cycle.replace(day=1)).strftime('%Y-%m-%d')
        cycle_last_day = (cycle.replace(month=cycle.month + 1, day=1) - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        start_time = "%s 00:00:00" % cycle_first_day
        end_time = "%s 23:59:59" % cycle_last_day
        month = cycle.strftime('%Y-%m')
        try:
            result_json = tencentcloud_api.TencentCloudApi().query_product_bill(start_time, end_time)
            result_total = json.loads(result_json, encoding='utf-8')
            #print(result_total)
            tmp_result = result_total['SummaryOverview']
        except TencentCloudSDKException as err:
            print(err)
        except Exception as e:
            print("except: %s" % e)
        else:
            mysql_conn = db_mysql.MyPymysqlPool()
            if tmp_result:
                # 获取db中数据
                sql = "select * from %s where billing_cycle = '%s' and cost_item_id = %s;" % (
                    table_name, month, cost_item_id)
                db_result = mysql_conn.select(sql)

                for record in tmp_result:
                    product_name = record['BusinessCodeName']
                    product_code = record['BusinessCode']
                    pretax_amount = float(record['RealTotalCost'])

                    insert_sql = "INSERT INTO %s(cost_item_id,product_code,product_name,billing_cycle," \
                                 "pretax_amount, update_time) VALUES (%s, '%s', '%s', '%s', '%s', '%s');" \
                                 % (table_name, cost_item_id, product_code, product_name, month, pretax_amount, update_time)

                    if not db_result:
                        result = mysql_conn.insert(insert_sql)
                    else:
                        update = False
                        for db_record in db_result:
                            db_record_id = int(db_record[0])
                            db_cost_item_id = int(db_record[1])
                            db_product_code = db_record[2]
                            db_pretax_amount = db_record[7]

                            if cost_item_id == db_cost_item_id and product_code == db_product_code:
                                update = True
                                db_update_time = db_record[10]
                                db_update_time_month = datetime.datetime.strftime(db_update_time, '%Y-%m')
                                if month != current_cycle and db_update_time_month != month:
                                    break
                                elif pretax_amount == db_pretax_amount:
                                    break
                                # update
                                sql = "UPDATE %s set pretax_amount = '%s' where id = %s" \
                                      % (table_name, pretax_amount, db_record_id)
                                result = mysql_conn.update(sql)
                                break
                        if not update:
                            result = mysql_conn.insert(insert_sql)
    mysql_conn.dispose()
    return True


def query_aws_bill(cost_item_id):
    try:
        import simplejson as json
    except ImportError:
        import json
    from src.lib.cloud import aws_api
    status = False

    # 每次获取本月和上月的账单数据，避免上月结尾的数据遗漏
    current_cycle = datetime.date(datetime.date.today().year, datetime.date.today().month, 1)
    last_cycle = datetime.date(datetime.date.today().year, datetime.date.today().month-1, 1)
    update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

    for cycle in [current_cycle, last_cycle]:
        month_start = (cycle.replace(day=1)).strftime('%Y-%m-%d')
        month_end = (cycle.replace(month=cycle.month + 1, day=1) - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        month = cycle.strftime('%Y-%m')

        try:
            response = aws_api.AwsApi().get_cost_and_usage(month_start, month_end)
            tmp_result = json.loads(json.dumps(response))
            result_total = tmp_result['ResultsByTime'][0]['Groups']
        except Exception as e:
            print("except: %s" % e)
        else:
            status = True

            # 获取db数据，用于数据比对，确认写入还是更新
            if len(result_total) == 0:
                return status

            mysql_conn = db_mysql.MyPymysqlPoolDict()
            # 获取db中数据
            sql = "select * from %s where billing_cycle = '%s' and cost_item_id = %s;" % (table_name, month, cost_item_id)
            db_result = mysql_conn.select(sql)

            # 分类计算，写入数据库
            for product in result_total:
                if len(product['Keys']) != 1:
                    print('error')
                    continue
                product_code = product['Keys'][0]
                tmp_amount = float(product['Metrics']['BlendedCost']['Amount'])*7   # 简单按照*7来计算美元汇率
                pretax_amount = float('%.2f' % tmp_amount)
                insert_sql = "INSERT INTO cost_bill_overview (cost_item_id, product_code, billing_cycle, " \
                             "pretax_amount, update_time) VALUES (%s, '%s', '%s', %s, '%s');" % \
                             (cost_item_id, product_code, month, pretax_amount, update_time)

                if not db_result:
                    result = mysql_conn.insert(insert_sql)
                else:
                    update = False
                    for db_record in db_result:
                        db_record_id = int(db_record['id'])
                        db_cost_item_id = int(db_record['cost_item_id'])
                        db_product_code = db_record['product_code']
                        db_pretax_amount = db_record['pretax_amount']

                        if cost_item_id == db_cost_item_id and product_code == db_product_code:
                            update = True
                            db_update_time = db_record['update_time']
                            db_update_time_month = datetime.datetime.strftime(db_update_time, '%Y-%m')
                            if month != current_cycle and db_update_time_month != month:
                                break
                            elif pretax_amount == db_pretax_amount:
                                break
                            # update
                            sql = "UPDATE %s set pretax_amount = '%s' where id = %s" \
                                  % (table_name, pretax_amount, db_record_id)
                            result = mysql_conn.update(sql)
                            break
                    if not update:
                        result = mysql_conn.insert(insert_sql)
            mysql_conn.dispose()
    return status


def query_bill_overview_handler(task_id=None):
    for ak_section in cf.sections():
        if ak_section.startswith('aliyun') or ak_section.startswith('tencentcloud') or ak_section.startswith('aws'):
            accessid = cf.get(ak_section, 'AccessKeyId')
            accesssecret = cf.get(ak_section, 'AccessKeySecret')
            regionid = cf.get(ak_section, 'DefaultRegionId')
            cost_item_id = int(cf.get(ak_section, 'CostItemId'))

            if ak_section.startswith('aliyun'):
                result = query_aliyun_bill(accessid, accesssecret, regionid, cost_item_id)
            elif ak_section.startswith('tencentcloud'):
                result = query_tencentcloud_bill(cost_item_id)
            elif ak_section.startswith('aws'):
                result = query_aws_bill(cost_item_id)
    return True


if __name__ == "__main__":
    query_bill_overview_handler()
