#!/usr/bin/env python3
# coding:utf-8
import json
import os
import configparser
from datetime import datetime
from django.http import HttpResponse
from src.lib import django_api
django_api.DjangoApi().os_environ_update()
# 项目的lib
from src.judge import judge_compare
from src.lib import db_mysql


def ssl_expire_judge():
    success = False
    method_name = 'ssl_expire_judge'
    try:
        result_list, success, problem_table, rules_table = get_init_info(method_name)
    except Exception as e:
        print('do get_init_info failed %s' % e)
        return success
    for m in result_list:  # 将取到的有效期与当天日期判断算出剩余有效期天数，将此天数与表达式中阈值做对比，输出对比结果judge_result
        gps_object = m['gps_object']
        value0 = m['value0']
        reference_value = m['reference_value']
        compare = m['compare']
        level = m['level']
        expression_id = m['expression_id']
        begin_time = m['update_time'].strftime("%Y-%m-%d %H:%M:%S")
        end_time = m['update_time'].strftime("%Y-%m-%d %H:%M:%S")
        reference_value = int(reference_value)
        now_time = datetime.now()  # 判断执行的时间

        now_data = datetime.now()
        value = int((value0 - now_data).days)

        try:
            judge_result = judge_compare.do_compare(value, compare, reference_value)  # 执行判断，获取result
        except Exception as e:
            print('do_compare failed %s' % e)
            return success
        try:
            success = do_judge(problem_table, gps_object, expression_id, judge_result, level, value, now_time,
                               begin_time, end_time)  # 根据判定结果，决定是否写入异常数据表
        except Exception as e:
            print('do_judge failed %s' % e)
            return success
    return success


def ssl_match_judge():
    success = False
    method_name = 'ssl_match_judge'
    try:
        result_list, success, problem_table, rules_table = get_init_info(method_name)
    except Exception as e:
        print('do get_init_info failed %s' % e)
        return success
    for m in result_list:  # 将取到的值与阈值做对比，输出对比结果judge_result
        gps_object = m['gps_object']
        reference_value = m['reference_value']
        compare = m['compare']
        level = m['level']
        expression_id = m['expression_id']
        begin_time = m['update_time'].strftime("%Y-%m-%d %H:%M:%S")
        end_time = m['update_time'].strftime("%Y-%m-%d %H:%M:%S")
        reference_value = int(reference_value)
        if m['value0'] == 'True':
            value = 0
        elif m['value0'] == 'False':
            value = 1
        elif m['value0'] is None:
            value = ''
        else:
            print('原表数据有误')
            value = ''
        reference_value = int(reference_value)
        now_time = datetime.now()  # 判断执行的时间

        try:
            judge_result = judge_compare.do_compare(value, compare, reference_value)  # 执行判断，获取result
        except Exception as e:
            print('do_compare failed %s' % e)
            return success
        try:
            success = do_judge(problem_table, gps_object, expression_id, judge_result, level, value, now_time,
                               begin_time, end_time)  # 根据判定结果，决定是否写入异常数据表
        except Exception as e:
            print('do_judge failed %s' % e)
            return success
    return success


def ak_leak_judge():
    success = False
    method_name = 'ak_leak_judge'
    try:
        result_list, success, problem_table, rules_table = get_init_info(method_name)  # 获取需要判断的原始数据表，表字段名，阈值，level等
    except Exception as e:
        print('do get_init_info3 failed %s' % e)
        return success
    for m in result_list:  # 将取到的值与阈值做对比，输出对比结果judge_result
        gps_object = m['gps_object']
        reference_value = int(m['reference_value'])
        compare = m['compare']
        level = m['level']
        expression_id = m['expression_id']
        begin_time = m['update_time'].strftime("%Y-%m-%d %H:%M:%S")
        end_time = m['update_time'].strftime("%Y-%m-%d %H:%M:%S")
        value = m['value0']
        now_time = datetime.now()

        try:
            judge_result = judge_compare.do_compare(value, compare, reference_value)  # 执行判断，获取result
        except Exception as e:
            print('do_compare failed %s' % e)
            return success
        try:
            success = do_judge(problem_table, gps_object, expression_id, judge_result, level, value, now_time,
                           begin_time, end_time)  # 根据判定结果，决定是否写入异常数据表
        except Exception as e:
            print('do_judge failed %s' % e)
            return success
    success = True
    return success


def tencent_cost_judge():
    success = False
    id_name = 'tencent_master'
    method_name = 'tencent_cost_judge'
    try:
        success = cost_judge(id_name, method_name)
    except Exception as e:
        print('do judge failed %s' % e)
        return success
    else:
        return success


def alimaster_cost_judge():
    success = False
    id_name = 'aliyun_master'
    method_name = 'alimaster_cost_judge'
    try:
        success = cost_judge(id_name, method_name)
    except Exception as e:
        print('do judge failed %s' % e)
        return success
    else:
        return success


def alimaishou_cost_judge():
    success = False
    id_name = 'aliyun_maishou'
    method_name = 'alimaishou_cost_judge'
    try:
        success = cost_judge(id_name, method_name)
    except Exception as e:
        print('do judge failed %s' % e)
        return success
    else:
        return success


def cost_judge(id_name, method_name):
    mysql_conn = db_mysql.MyPymysqlPoolDict()
    success = False
    problem_table = 'gps_problem'
    rules_table = 'gps_rules'
    cost_id_table = 'cost_item'

    file_path = os.path.join(os.path.dirname(__file__), "../../conf/key.conf")
    cf = configparser.ConfigParser()
    cf.read(file_path)
    section = 'cloud_id'
    cloud_id = cf.get(section, id_name)
    print(cloud_id)
    try:
        status, result = get_method_info(method_name)
    except Exception as e:
        print('do get_method_info failed %s' % e)
        return success
    else:
        if status is False:
            print('do get_method_info failed %s')
            return success
        else:
            source_table = result['source_table']
            judge_metric = result['judge_metric']
            judge_object = result['judge_object']

    try:
        sql = "select * from %s where available = '1' and method_name = '%s';" % (rules_table, method_name)
        sql_result = mysql_conn.select(sql)
    except Exception as e:
        print('执行sql failed %s:' % e)
        return success
    else:
        expression_id = sql_result[0]['id']
        level = sql_result[0]['level']
        compare = sql_result[0]['compare']
        reference_value = int(sql_result[0]['reference_value'])

    result_dict = dict()

    try:
        sql = "select item_remark from %s where id = '%s'" % (cost_id_table, cloud_id)
        sql_result = mysql_conn.select(sql)
    except Exception as e:
        print('执行sql failed %s:' % e)
        return success
    else:
        gps_object = sql_result[0]['item_remark']

    try:  # 根据账户id获取云账户的余额
        sql_cmd = "select %s, update_time from %s where %s = '%s';" % (judge_metric, source_table, judge_object, cloud_id)
        result = mysql_conn.select(sql_cmd)
    except Exception as e:
        print('执行sql failed %s:' % e)
        return success
    else:
        result_dict['gps_object'] = gps_object
        value0 = result[0][judge_metric]
        result_dict['update_time'] = result[0]['update_time']

    begin_time = result_dict['update_time'].strftime("%Y-%m-%d %H:%M:%S")
    end_time = result_dict['update_time'].strftime("%Y-%m-%d %H:%M:%S")
    reference_value = int(reference_value)
    now_time = datetime.now()  # 判断执行的时间
    value = value0
    try:
        judge_result = judge_compare.do_compare(value, compare, reference_value)
    except Exception as e:
        print('judge_result failed %s:' % e)
        return success
    try:
        success = do_judge(problem_table, gps_object, expression_id, judge_result, level, value, now_time, begin_time, end_time)
    except Exception as e:
        print('do_judge failed %s:' % e)
        return success
    mysql_conn.dispose()
    return success


def get_init_info(method_name):
    mysql_conn = db_mysql.MyPymysqlPoolDict()
    result_list = list()
    gps_object_list = list()
    success = False
    problem_table = 'gps_problem'
    rules_table = 'gps_rules'
    try:
        status, result = get_method_info(method_name)
    except Exception as e:
        print('do get_init_info failed %s' % e)
        return success
    else:
        if status is False:
            print('do get_init_info failed %s')
            return success
        else:
            source_table = result['source_table']
            judge_object = result['judge_object']
            judge_metric = result['judge_metric']

    try:
        sql = "select * from %s where available = '1' and method_name = '%s';" % (rules_table, method_name)
        sql_result = mysql_conn.select(sql)
    except Exception as e:
        print('do sql failed %s' % e)
        return success
    else:
        if sql_result:
            for i in sql_result:
                try:
                    expression_id = i['id']
                    level = i['level']
                    compare = i['compare']
                    reference_value = i['reference_value']
                except Exception as e:
                    return success
                try:
                    sql_cmd = "select id, %s, %s, update_time from %s;" % (judge_object, judge_metric, source_table)
                    result = mysql_conn.select(sql_cmd)
                except Exception as e:
                    print('do sql failed %s' % e)
                    return success
                else:
                    if result is not False and len(result) > 0:
                        for m in result:
                            result_dict = dict()
                            try:
                                result_dict['gps_object'] = m[judge_object]
                                result_dict['value0'] = m[judge_metric]
                                result_dict['update_time'] = m['update_time']
                                result_dict['expression_id'] = expression_id
                                result_dict['level'] = level
                                result_dict['compare'] = compare
                                result_dict['reference_value'] = reference_value
                            except Exception as e:
                                print('表中无数据')
                                result_list = None
                                gps_object_list = None
                            else:
                                gps_object_list.append(m[judge_object])
                                result_list.append(result_dict)

                # delete已经不存在的对象，但是在异常数据表里的row
                try:
                    sql_cmd = "select gps_object from %s where expression_id = '%s';" % (problem_table, expression_id)
                    result = mysql_conn.select(sql_cmd)
                except Exception as e:
                    print('do del old-sql failed %s' % e)
                    return success
                else:
                    if result is not False and len(result) > 0:
                        sql_object_list = list()
                        for n in result:
                            sql_object_list.append(n['gps_object'])
                        del_list = [y for y in sql_object_list if y not in gps_object_list]
                        if len(del_list) > 0:
                            for del_object in del_list:
                                try:
                                    sql = "delete from %s where gps_object = '%s'" % (problem_table, del_object)
                                    mysql_conn.delete(sql)
                                except Exception as e:
                                    print('do del old-sql failed %s' % e)
                                    return success
    success = True
    mysql_conn.dispose()
    return result_list, success, problem_table, rules_table


def get_method_info(method_name):
    mysql_conn = db_mysql.MyPymysqlPoolDict()
    status = False
    result = dict()
    try:
        sql_cmd = "select source_table, judge_object, judge_metric from gps_judge_methods where name = '%s';" % (method_name)
        sql_result = mysql_conn.select(sql_cmd)
    except Exception as e:
        print('do sql failed %s' % e)
        return status, result
    else:
        source_table = sql_result[0]['source_table']
        judge_object = sql_result[0]['judge_object']
        judge_metric = sql_result[0]['judge_metric']
        result['source_table'] = source_table
        result['judge_object'] = judge_object
        result['judge_metric'] = judge_metric
        status = True
    mysql_conn.dispose()
    return status, result


def do_judge(problem_table, gps_object, expression_id, judge_result, level, value, time, begin_time, end_time):
    mysql_conn = db_mysql.MyPymysqlPoolDict()
    success = False
    # 获取同一个规则同一个对象的异常数据的个数
    try:
        sql = "select count(*) AS count from %s where gps_object = '%s' and expression_id = '%s' and status = 1;" % \
              (problem_table, gps_object, expression_id)
        result = mysql_conn.select(sql)
        monitor_count = result[0]['count']
    except Exception as e:
        monitor_count = 0
        print('do sql failed: %s' % e)

    if monitor_count == 0 and judge_result is True:
        # 如果gps_problem没表中没有该域名的异常数据,且判断结果为异常，则直接表中加入这条异常数据
        status = 1
        try:
            sql = "insert into %s(expression_id, level, gps_object, value, update_time, status, begin_time) values('%s', '%s', " \
                  "'%s', '%s','%s', '%s', '%s');" % (problem_table, expression_id, level, gps_object, value, time,
                                                     status, begin_time)
            mysql_conn.insert(sql)
            success = True
        except Exception as e:
            print('do sql failed: %s' % e)
    if monitor_count == 0 and judge_result is False:
        success = True
        pass
    if monitor_count == 1:
        try:
            sql_cmd = "select id, expression_id, level, value, status, update_time from %s where gps_object = '%s' and " \
                      "expression_id = '%s';" % (problem_table, gps_object, expression_id)
            result = mysql_conn.select(sql_cmd)
            problem_id = result[0]['id']
            if judge_result is True:
                status = 1
                sql = "update %s set expression_id = '%s', level = '%s', value = '%s', status = '%s', update_time = '%s' " \
                      "where id = '%s';" % (problem_table, expression_id, level, value, status, time, problem_id)
                mysql_conn.update(sql)
            else:
                status = 0
                sql = "update %s set expression_id = '%s', level = '%s', value = '%s', status = '%s', " \
                      "update_time = '%s', end_time = '%s' where id = '%s';" % \
                      (problem_table, expression_id, level, value, status, time, end_time, problem_id)
                mysql_conn.update(sql)
            success = True
        except Exception as e:
            print('something failed: %s' % e)
    mysql_conn.dispose()
    return success


def do_all_judge(task_id=False):
    success = False
    success_dict = dict()

    success_dict['ssl_expire'] = ssl_expire_judge()
    success_dict['ssl_match'] = ssl_match_judge()
    success_dict['alimaster_cost_balance'] = alimaster_cost_judge()
    success_dict['alimaishou_cost_balance'] = alimaishou_cost_judge()
    success_dict['alitencent_cost_balance'] = tencent_cost_judge()
    success_dict['ak_leak'] = ak_leak_judge()
    m = 0
    for key, value in success_dict.items():
        if success_dict[key] is False:
            m += 1
    if m == 0:
        success = True
    return success


def http_all_judge(request):
    code = 500
    judge_body_dict = dict()
    judge_result_dict = dict()
    success = do_all_judge()
    success_dict = dict()
    message = ''

    success_dict['ssl_expire'] = ssl_expire_judge()
    success_dict['ssl_match'] = ssl_match_judge()
    success_dict['alimaster_cost_balance'] = alimaster_cost_judge()
    success_dict['alimaishou_cost_balance'] = alimaishou_cost_judge()
    success_dict['alitencent_cost_balance'] = tencent_cost_judge()
    success_dict['ak_leak'] = ak_leak_judge()
    m = 0
    for key, value in success_dict.items():
        if success_dict[key] is False:
            message = message + ' {}异常判定失败'.format(key)
            m += 1
        else:
            message = message + ' {}异常判定成功'.format(key)
    if m == 0:
        success = True
        code = 200

    judge_body_dict['data'] = ''
    judge_body_dict['count'] = len(success_dict)
    judge_result_dict['code'] = code
    judge_result_dict['success'] = success
    judge_result_dict['message'] = message
    judge_result_dict['code'] = code
    judge_result_dict['body'] = judge_body_dict
    judge_result_json = json.dumps(judge_result_dict, ensure_ascii=False)
    return HttpResponse(judge_result_json, content_type="application/json,charset=utf-8")


if __name__ == "__main__":
    # alert_serious_judge()
    do_all_judge()
