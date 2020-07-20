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


def cloud_cost_calculate():
    mysql_conn = db_mysql.MyPymysqlPool()
    sql = "select cost_item_id, billing_cycle, pretax_amount from cost_bill_overview"
    cycle_total_cost_list = []
    try:
        result = mysql_conn.select(sql)
    except Exception as e:
        print('except, reason: %s' % e)
    else:
        if result:
            for record in result:
                item_cost_dict = {}
                cost_item_id = record[0]
                cycle = record[1]
                cost = record[2]

                if not cycle_total_cost_list:
                    item_cost_dict['cost_item_id'] = cost_item_id
                    item_cost_dict['cycle'] = cycle
                    item_cost_dict['cost'] = cost
                    cycle_total_cost_list.append(item_cost_dict)
                else:
                    update = False
                    for dict_in_list in cycle_total_cost_list:
                        cost_item_id_in_dict = dict_in_list['cost_item_id']
                        cycle_in_dict = dict_in_list['cycle']
                        if cost_item_id == cost_item_id_in_dict and cycle == cycle_in_dict:
                            dict_in_list['cost'] += cost
                            update = True
                            break
                    if not update:
                        item_cost_dict['cost_item_id'] = cost_item_id
                        item_cost_dict['cycle'] = cycle
                        item_cost_dict['cost'] = cost
                        cycle_total_cost_list.append(item_cost_dict)
    finally:
        mysql_conn.dispose()
    return cycle_total_cost_list


def calculate_handler(task_id=None):
    # 计算云账号费用数据，并汇总，写入分月费用总表
    update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    mysql_conn = db_mysql.MyPymysqlPool()
    table_name = 'cost_cycle_cost'

    # 计算后的数据
    result = cloud_cost_calculate()

    # 和数据库数据对比，并更新或写入数据库
    sql = "select * from %s" % table_name
    db_cycle_cost = mysql_conn.select(sql)

    for cost_item_record in result:
        cost_item_id = cost_item_record['cost_item_id']
        cycle = cost_item_record['cycle']
        cost = float('%.2f' % cost_item_record['cost'])
        sql = "insert into %s (cost_item_id, month, total_cost, update_time) values (%s, '%s', %s, '%s')" % \
              (table_name, cost_item_id, cycle, cost, update_time)

        update = False
        if not db_cycle_cost:
            # insert
            result = mysql_conn.insert(sql)
        else:
            for db_record in db_cycle_cost:
                db_id = db_record[0]
                db_cost_item_id = db_record[1]
                db_cycle = db_record[2]
                db_cost = db_record[3]
                if cost_item_id == db_cost_item_id and cycle == db_cycle:
                    update = True
                    if cost != db_cost:
                        # update
                        sql = "update %s set total_cost = %s where id = %s" % (table_name, cost, db_id)
                        result = mysql_conn.update(sql)
                    break
            if not update:
                # insert
                result = mysql_conn.insert(sql)

    mysql_conn.dispose()
    return True


if __name__ == "__main__":
    calculate_handler()
