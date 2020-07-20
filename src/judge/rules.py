#!/usr/bin/env python3
# coding:utf-8
from django.http import HttpResponse
import json

# 项目的lib
from src.lib import db_mysql, django_api
mysql_conn = db_mysql.MyPymysqlPool()


def add_rules(request):  # 新增规则
    expression_list = []
    expression_reponse_dict = {}
    success = False
    code = 500
    expression_body_dict = {}
    try:
        expression_name = request.GET['expression_name']
    except Exception as e:
        print("%s:未传入表达式名称" % e)
        expression_name = ''
    try:
        method_name = request.GET['method_name']
    except Exception as e:
        print("%s:未传入方法" % e)
        method_name = ''
    try:
        level = int(request.GET['level'])
    except Exception as e:
        print("%s:未传入策略级别" % e)
        level = ''
    try:
        compare = request.GET['compare']
    except Exception as e:
        print("%s:未传入运算符" % e)
        compare = ''
    try:
        reference_value = request.GET['reference_value']
    except Exception as e:
        print("%s:未传入阈值" % e)
        reference_value = ''
    try:
        available = request.GET['available']
    except Exception as e:
        print("%s:未传入可用性，默认true" % e)
        available = True
    if expression_name and method_name and level and compare and reference_value and available:
        sql = "select count(*) from %s where expression_name = '%s'" % ('gps_rules', expression_name)
        sql_result = mysql_conn.select(sql)
        expression_count = sql_result[0][0]

        if expression_count == 0:
            if expression_name:
                sql = "insert into %s(expression_name, method_name, level, compare, reference_value, available)" \
                      " values('%s', '%s', '%s', '%s', '%s', '%s') " % ('gps_rules', expression_name, method_name, level,
                                                                        compare, reference_value, available)
                mysql_conn.insert(sql)
                mysql_conn.end()
                message = 'add new rule successful'
                success = True
                code = 200
            else:
                message = 'please make sure you have choose a rule'
        else:
            message = 'this rule has exist'
            code = 204
            success = False
    else:
        print('传入参数不完整')
        message = '传入参数不完整，need expression_name, method_name, level, compare, reference_value, available'
        code = 204
        success = False

    expression_body_dict['data'] = expression_list
    expression_body_dict['count'] = len(expression_list)

    expression_reponse_dict['code'] = code
    expression_reponse_dict['success'] = success
    expression_reponse_dict['message'] = message
    expression_reponse_dict['body'] = expression_body_dict
    expression_result_json = json.dumps(expression_reponse_dict, ensure_ascii=False)

    return HttpResponse(expression_result_json, content_type="application/json,charset=utf-8")


def delete_rules(request):
    expression_list = []
    expression_reponse_dict = {}
    expression_body_dict = {}

    try:
        expression_name = str(request.GET['expression_name'])
    except Exception as e:
        print("%s:未传入表达式名" % e)
        expression_name = ''
    try:
        expression_id = request.GET['id']
    except Exception as e:
        print("%s:未传入表达式id" % e)
        expression_id = ''

    if not expression_id and not expression_name:
        message = 'please input a id or expression for delete'
        success = False
        code = 204

    elif expression_id and expression_name:
        sql = "delete from %s where id = '%s'" % ('gps_rules', expression_id)
        mysql_conn.delete(sql)
        mysql_conn.end()
        message = 'this rule delete successful'
        success = True
        code = 200
    elif not expression_name and expression_id:
        sql = "delete from %s where id = '%s'" % ('gps_rules', expression_id)
        mysql_conn.delete(sql)
        mysql_conn.end()
        message = 'this rule delete successful'
        success = True
        code = 200
    else:
        sql = "delete from %s where expression_name = '%s'" % ('gps_rules', expression_name)
        mysql_conn.delete(sql)
        mysql_conn.end()
        message = 'this rule delete successful'
        success = True
        code = 200

    expression_body_dict['data'] = expression_list
    expression_body_dict['count'] = len(expression_list)

    expression_reponse_dict['code'] = code
    expression_reponse_dict['success'] = success
    expression_reponse_dict['message'] = message
    expression_reponse_dict['body'] = expression_body_dict
    expression_result_json = json.dumps(expression_reponse_dict, ensure_ascii=False)

    return HttpResponse(expression_result_json, content_type="application/json,charset=utf-8")


def select_rules(request):
    expression_list = []
    expression_reponse_dict = {}
    success = False
    code = 500
    message = ''
    expression_body_dict = {}

    try:
        page = int(request.GET['page'])
        limit = int(request.GET['limit'])
    except Exception as e:
        print("%s:将使用默认的page和limit" % e)
        page = 1
        limit = 10

    try:
        expression_name = str(request.GET['expression_name'])
    except Exception as e:
        print("%s:未传入表达式名称" % e)
        expression_name = ''

    django_api.DjangoApi().os_environ_update()
    offset = (page - 1) * limit  # （当前页数-1）*每页数量 = 每页的开始位置

    # 获取表数据总条数
    try:
        sql_count = "select count(id) from gps_rules"
        total_count = int(mysql_conn.select(sql_count)[0][0])
    except Exception as e:
        print("%s:rules表中无数据" % e)
        total_count = 0
        pass
    print(total_count)
    if total_count > 0:
        try:
            # 执行查询表数据
            sql_cmd = "select * from %s where expression_name like '%%%s%%' order by level limit %s,%s"\
                      % ('gps_rules', expression_name, offset, limit)
            result = mysql_conn.select(sql_cmd)
        except Exception as e:
            print("%s:没有查询到相关规则" % e)
            success = False
            code = 204
            message = "没有查询到表达式中包含:"+expression_name+"的相关规则"
            pass
        else:
            # 循环赋值，定义列表
            for record in result:
                expression_id = record[0]
                expression_name = record[1]
                method_name = record[2]
                level = record[3]
                compare = record[4]
                reference_value = record[5]
                available = record[6]

                single_expression = dict()
                single_expression['id'] = expression_id
                single_expression['expression_name'] = expression_name
                single_expression['method_name'] = method_name
                single_expression['level'] = level
                single_expression['compare'] = compare
                single_expression['reference_value'] = reference_value
                single_expression['available'] = available
                expression_list.append(single_expression)
            code = 200
            success = True
            message = 'ok'
    expression_body_dict['data'] = expression_list
    expression_body_dict['count'] = len(expression_list)

    expression_reponse_dict['code'] = code
    expression_reponse_dict['success'] = success
    expression_reponse_dict['message'] = message
    expression_reponse_dict['body'] = expression_body_dict
    expression_result_json = json.dumps(expression_reponse_dict, ensure_ascii=False)

    return HttpResponse(expression_result_json, content_type="application/json,charset=utf-8")


def update_rules(request):  # 修改表达式
    expression_list = []
    expression_reponse_dict = {}
    expression_body_dict = {}

    try:
        expression_id = str(request.GET['id'])
    except Exception as e:
        print("%s:未传入表达式id" % e)
        expression_id = ''
    try:
        expression_name = str(request.GET['expression_name'])
    except Exception as e:
        print("%s:未传入表达式名称" % e)
        expression_name = ''
    try:
        method_name = str(request.GET['method_name'])
    except Exception as e:
        print("%s:未传入异常判定的方法" % e)
        method_name = ''
    try:
        level = int(request.GET['level'])
    except Exception as e:
        print("%s:未传入策略级别" % e)
        level = ''
    try:
        compare = str(request.GET['compare'])
    except Exception as e:
        print("%s:未传入运算法" % e)
        compare = ''
    try:
        reference_value = str(request.GET['reference_value'])
    except Exception as e:
        print("%s:未传入阈值" % e)
        reference_value = ''
    try:
        available = str(request.GET['available'])
    except Exception as e:
        print("%s:未传入可用性，默认启用" % e)
        available = True

    if expression_id and not expression_name:
        sql = "select id, expression_name, method_name, level, compare, reference_value, available from %s " \
              "where id = '%s'" % ('gps_rules', expression_id)
        result = mysql_conn.select(sql)
    elif not expression_id and expression_name:
        sql = "select id, expression_name, method_name, level, compare, reference_value, available from %s " \
              "where expression_name = '%s'" % ('gps_rules', expression_name)
        result = mysql_conn.select(sql)
    elif expression_id and expression_name:
        sql = "select id, expression_name, method_name, level, compare, reference_value, available from %s " \
              "where id = '%s'" % ('gps_rules', expression_id)
        result = mysql_conn.select(sql)
    else:
        print('未传入策略表达式名称和id,无法更新')
        result = dict()
        pass
    if not result:
        success = False
        code = 204
        message = 'there is no this expression，need a rule'
    else:
        old_expression_name = result[0][1]  # 将从sql中查询的结果取str类型的过期时间
        old_method_name = result[0][2]
        old_level = result[0][3]
        old_compare = result[0][4]
        old_reference_value = result[0][5]
        old_available = result[0][6]

        if not expression_name:
            expression_name = old_expression_name
        if not method_name:
            method_name = old_method_name
        if not level:
            level = old_level
        if not compare:
            compare = old_compare
        if not reference_value:
            reference_value = old_reference_value
        if not available:
            available = old_available

        if expression_name != old_expression_name or method_name != old_method_name or level != old_level or \
                compare != old_compare or reference_value != old_reference_value or available != old_available:
            sql_cmd = "update %s set expression_name = '%s', method_name = '%s', level = '%s', compare = '%s', " \
                      "reference_value = '%s' available = '%s' where id = '%s'" % \
                      ('gps_rules', expression_name, method_name, level, compare, reference_value, available, expression_id)
            mysql_conn.update(sql_cmd)
            mysql_conn.end()
        success = True
        code = 200
        message = 'update expression successful'

    expression_body_dict['data'] = expression_list
    expression_body_dict['count'] = len(expression_list)

    expression_reponse_dict['code'] = code
    expression_reponse_dict['success'] = success
    expression_reponse_dict['message'] = message
    expression_reponse_dict['body'] = expression_body_dict
    expression_result_json = json.dumps(expression_reponse_dict, ensure_ascii=False)

    return HttpResponse(expression_result_json, content_type="application/json,charset=utf-8")


if __name__ == "__main__":
    select_rules('xxx')