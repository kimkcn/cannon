#!/usr/bin/env python3
# coding:utf-8
import time
import datetime
# 项目的lib
from src.lib import db_mysql

# 加载配置文件,读取表明等
import os
import configparser


class BecomeCalculate:
    def __init__(self, calculate_data_list):
        file_path = os.path.join(os.path.dirname(__file__), "../../conf/table.conf")
        cf = configparser.ConfigParser()
        cf.read(file_path)
        table_section = 'table_name'    # 读取表的名称
        self.object_info_table = cf.get(table_section, 'object_info_table')
        self.calculate_table = cf.get(table_section, 'calculate_table')
        self.task_job_table = cf.get(table_section, 'task_job_config_table')
        self.calculate_data_list = calculate_data_list

    def exec_data_list(self):  # 需要传入list格式的数据
        mysql_conn = db_mysql.MyPymysqlPoolDict()
        success = False
        if isinstance(self.calculate_data_list, list):
            for calculate_data in self.calculate_data_list:
                if isinstance(calculate_data, dict):
                    try:
                        if calculate_data['job_id']:  # 如果传入的是task_id则直接使用，如果传入的是job_id则搜索task_config表中id值
                            job_id = calculate_data['job_id']
                            try:  # 根据job_id获取在task配置表里的id,这里命名为task_id
                                sql = "select id from %s where job_id = '%s';" % (self.task_job_table, job_id)
                                sql_result = mysql_conn.select(sql)
                            except Exception as e:  # 如果查询语句执行失败, 则退出
                                print('%s 查询job_id表失败，退出；job_id为 %s' % (e, job_id))
                                continue  # 查询task_id有问题，结束当前循环
                            else:
                                if sql_result and len(sql_result) == 1:
                                    task_id = sql_result[0]['id']
                                else:
                                    print('请检查 %s 表中，job_id为 %s 的数据准确性' % (self.task_job_table, job_id))
                                    continue  # task_job配置表中数据不准确，退出当前循环
                        else:
                            task_id = calculate_data['task_id']
                        object_filed = calculate_data['object_filed']
                        object_value = calculate_data['object_value']

                        try:  # 如果没有传object_remark_name则默认使用object_value作为展示名
                            object_remark_name = calculate_data['object_remark_name']
                        except Exception as e:
                            object_remark_name = calculate_data['object_value']
                        metric_dict = calculate_data['metric_dict']

                        try:  # 如果没有传update_time则使用当前调用函数的时间作为update_time
                            update_time = calculate_data['update_time']
                        except Exception as e:
                            update_time = datetime.datetime.now()
                    except Exception as e:  # object_remark_name和update_time以外的，其他所有参数为必传项
                        print(' %s ' % e)
                        continue  # 传入数据格式有问题，结束当前循环
                    else:
                        # try:  # 根据job_id获取在task配置表里的id,这里命名为task_id
                        #     sql = "select id from %s where job_id = '%s';" % (self.task_job_table, job_id)
                        #     sql_result = mysql_conn.select(sql)
                        # except Exception as e:  # 如果查询语句执行失败, 则退出
                        #     print('%s 查询job_id表失败，退出；job_id为 %s' % (e, job_id))
                        #     continue  # 查询task_id有问题，结束当前循环
                        # else:
                        #     if sql_result and len(sql_result) == 1:
                        #         task_id = sql_result[0]['id']
                        try:
                            success = self.become_calculate_data(mysql_conn, task_id, object_filed, object_value, object_remark_name, metric_dict, update_time)
                        except Exception as e:
                            print('% s 数据获取成功，但执行数据抽象化失败' % e)
                            continue

                else:  # 如果当条数据格式不对，则执行下一条数据循环
                    print('传入的列表中的元素需要为dict格式')
                    continue
        else:  # 如果没接收到list格式的传入数据，则失败
            print('未接收到list格式的数据')
            mysql_conn.dispose()
            return success
        mysql_conn.dispose()
        return success

    def become_calculate_data(self, mysql_conn, task_id, object_filed, object_value, object_remark_name, metric_dict, update_time):
        success = False
        try:  # 更新object_info表的信息
            success, object_id = self.update_object_info(mysql_conn, task_id, object_filed, object_value, object_remark_name)
        except Exception as e:  # 如果更新更新object_info表执行失败，则退出
            print('更新object信息失败' % e)
            return success
        else:
            try:
                success = self.update_calculate_data(mysql_conn, object_id, metric_dict, update_time)
            except Exception as e:  # 如果查询语句执行失败, 则退出
                print('更新计算表失败' % e)
                return success
            else:
                success = True
        return success

    def update_object_info(self, mysql_conn, task_id, object_filed, object_value, object_remark_name):
        success = False
        try:  # 查看object表中是否已经有此对象
            sql = "select id , object_remark_name from %s where task_id = '%s' and object_filed = '%s' and " \
                  "object_value = '%s';" % (self.object_info_table, task_id, object_filed, object_value)
            sql_result = mysql_conn.select(sql)
        except Exception as e:  # 如果查询语句执行失败，则返回值为None的object_id
            print('do sql failed %s' % e)
            object_id = None
            # return success, object_id
        else:  # 如果查询语句执行成功，则根据返回结果进一步判断
            if sql_result and len(sql_result) == 1:  # 如果返回结果是True，且返回了一条数据，那么说明此对象已经存在，直接返回object_id
                object_id = sql_result[0]['id']
                success = True
                if sql_result[0]['object_remark_name'] != object_remark_name:
                    try:  # 如果传入的object_remark_name与原表中object_remark_name不一致，则更新object_remark_name为最新传入的值
                        sql = "update %s set object_remark_name = '%s' where id = %s;" % \
                                  (self.object_info_table, object_remark_name, object_id)
                        mysql_conn.update(sql)
                    except Exception as e:
                        print('do sql failed %s' % e)
                        object_id = None
                # return success, object_id
            elif sql_result and len(sql_result) > 1:  # 如果返回结果是True，且返回了多条数据，那么说明此对象已经存在多个，此为异常需要处理，返回值为None的object_id
                print('对象id有多个,请检查对象id')
                object_id = None
                # return success, object_id
            else:  # 剩余的case为，如果返回结果是False或者返回条数为0，则说明此全局对象表中不存在，此时应该插入该对象数据，并返回插入后的object_id
                print('未查询到此object_id,将插入此object_id')
                try:  # 向object表中插入此条数据
                    sql = "insert into %s(task_id, object_filed, object_value, object_remark_name) values('%s', " \
                          "'%s', '%s', '%s');" % (self.object_info_table, task_id, object_filed,
                                                  object_value, object_remark_name)  # 插入一条object_id
                    mysql_conn.insert(sql)
                    mysql_conn.end()  # 插入语句需要立刻提交，这样才能进行后续查询object_id，以返回
                except Exception as e:
                    print('%s 向object表中插入对象数据失败，失败的对象为:  %s : %s : %s : %s' % (e, task_id, object_filed, object_value, object_remark_name))
                    object_id = None
                    # return success, object_id
                else:
                    time.sleep(1)  # 1秒后查询
                    try:  # 执行插入object数据成功后，需要反查object表,获取刚刚插入数据的id，此id即为object_id
                        sql = "select id from %s where task_id = '%s' and object_filed = '%s' and object_value = '%s';" \
                              % (self.object_info_table, task_id, object_filed, object_value)
                        sql_result = mysql_conn.select(sql)
                    except Exception as e:
                        print('%s 向object表中插入对象数据失败，失败的对象为:  %s : %s : %s' % (e, task_id, object_filed, object_value))
                        object_id = None
                        # return success, object_id
                    else:
                        if sql_result and len(sql_result) == 1:
                            object_id = sql_result[0]['id']
                            success = True
                            # return success, object_id
                        elif sql_result and len(sql_result) > 1:
                            print('对象id有多个,请检查对象id')
                            object_id = None
                            # return success, object_id
                        else:
                            object_id = None
                            print('对象表中插入数据失败，数据: %s : %s : %s' % (task_id, object_filed, object_value))
                            # return success, object_id
        return success, object_id

    def update_calculate_data(self, mysql_conn, object_id, metric_dict, update_time):
        success = False
        metric_dict = eval(metric_dict)
        for metric_filed in metric_dict.keys():  # 将传入的metric_dict中的key取出来
            metric_value = metric_dict[metric_filed]
            try:  # 从计算表中查找同一个对象同一个metric_filed的数据的条数
                sql = "select id from %s where object_id = '%s' and metric_filed = '%s';" \
                      % (self.calculate_table, object_id, metric_filed)
                sql_result = mysql_conn.select(sql)
            except Exception as e:  # 更改失败则退出
                print('%s: 搜索计算表中查找同一个对象同一个metric_filed的数据失败' % e)
                return success
            else:
                if sql_result and len(sql_result) == 1:  # 如果查到同一个对象同一个metric_filed的数据有且为一个，那么更新数据即可
                    try:
                        sql = "update %s set metric_value = '%s', update_time = '%s' where object_id = '%s' and " \
                              "metric_filed = '%s';" % (self.calculate_table, metric_value, update_time, object_id, metric_filed)
                        mysql_conn.update(sql)
                    except Exception as e:  # 更改失败则退出
                        print('%s: 更新计算表数据失败' % e)
                        return success
                    else:
                        success = True
                elif sql_result is False:  # 没有查询到结果时可能会返回False，此时也应插入新数据
                    try:  # 计算表里插入一条新的数据
                        sql = "insert into %s(object_id, metric_filed, metric_value, update_time) values('%s', '%s', " \
                              "'%s', '%s');" % (self.calculate_table, object_id, metric_filed, metric_value, update_time)
                        mysql_conn.insert(sql)
                    except Exception as e:  # 更改失败则退出
                        print('%s: 向计算表里插入新数据失败，数据为 %s:%s:%s:%s' % (e, object_id, metric_filed, metric_value, update_time))
                        return success
                    else:
                        success = True
        return success


if __name__ == "__main__":
    BecomeCalculate('xxx').exec_data_list()

