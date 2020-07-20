#!/usr/bin/env python3
# coding:utf-8
from django.http import HttpResponse
import json
from src.lib import db_mysql, django_api
# 调用mysql方法
mysql_conn = db_mysql.MyPymysqlPoolDict()


def get_problem_data(request):
    expression_id_list = list()
    result_list = list()
    single_problem = dict()
    problem_list = list()
    problem_response_dict = dict()
    problem_body_dict = dict()
    success = False
    code = 1
    message = ''
    # 设置默认的page和limit值
    try:
        page = int(request.GET['page'])
        limit = int(request.GET['limit'])
    except Exception as e:
        print("%s:未传入page或limit，使用默认值" % e)
        page = 1
        limit = 10
    # 接收传入的类型，根据类型搜索相同方法的表达式id
    try:
        gps_type = str(request.GET['type'])
        sql_cmd = "select id from %s where method_name = '%s'" % ('gps_rules', gps_type)
        result = mysql_conn.select(sql_cmd)
        for i in result:
            expression_id = i['id']
            expression_id_list.append(expression_id)
    except Exception as e:
        print("%s:未传入，使用默认值" % e)
    # 接收传入的异常数据主体
    try:
        gps_object = str(request.GET['gps_object'])
    except Exception as e:
        print("%s:未传入gps_object，使用默认值" % e)
        gps_object = ''
    # 接收传入的异常级别
    try:
        level = str(request.GET['level'])
    except Exception as e:
        print("%s:未传入level，使用默认值" % e)
        level = ''
    # 设置每页起始值
    django_api.DjangoApi().os_environ_update()
    offset = (page - 1) * limit  # （当前页数-1）*每页数量 = 每页的开始位置
    # 获取表数据总条数
    try:
        sql_count = "select count(id) from gps_problem;"
        total_count = int(mysql_conn.select(sql_count)[0]['count(id)'])
    except Exception as e:
        print("%s:表中无数据" % e)
        total_count = 0

    if total_count > 0 and len(expression_id_list) > 0:
        try:
            for m in expression_id_list:
                # 执行查询表数据
                sql_cmd = "select * from %s where expression_id like '%s' and gps_object like '%%%s%%' and level like " \
                          "'%%%s%%' order by time limit %s,%s;" % ('gps_problem', m, gps_object, level, offset, limit)
                result = mysql_conn.select(sql_cmd)
                result_list.append(result)
        except Exception as e:
            print("%s:sql语句执行失败" % e)
            pass

    elif total_count > 0 and len(expression_id_list) == 0:
        try:
            sql_cmd = "select * from %s where gps_object like '%%%s%%' and level like '%%%s%%'" \
                      " order by time limit %s,%s;" % ('gps_problem', gps_object, level, offset, limit)
            result = mysql_conn.select(sql_cmd)
            result_list.append(result)
        except Exception as e:
            print("%s:sql语句执行失败" % e)
            pass
    else:
        message = '请检查gps_problem表中是否有数据'

    if len(result_list[0]) > 0:
        # 循环赋值，定义列表
        result = result_list[0]
        for record in result:
            expression_id = record['expression_id']
            level = record['level']
            gps_object = record['gps_object']
            value = record['value']
            time = record['time'].strftime("%Y-%m-%d %H:%M:%S")
            status = record['status']

            single_problem['expression_id'] = expression_id
            single_problem['level'] = level
            single_problem['gps_object'] = gps_object
            single_problem['value'] = value
            single_problem['time'] = time
            single_problem['status'] = status
            problem_list.append(single_problem)
        code = 0
        success = True
        message = 'ok'

    problem_body_dict['data'] = problem_list
    problem_body_dict['count'] = len(problem_list)
    problem_response_dict['code'] = code
    problem_response_dict['success'] = success
    problem_response_dict['message'] = message
    problem_response_dict['body'] = problem_body_dict
    problem_result_json = json.dumps(problem_response_dict, ensure_ascii=False)

    return HttpResponse(problem_result_json, content_type="application/json,charset=utf-8")


if __name__ == "__main__":
    get_problem_data('xxx')
