#!/usr/bin/env python3
# coding:utf-8
import os
from django.http import HttpResponse
import json
from src.lib import db_mysql,django_api

mysql_conn = db_mysql.MyPymysqlPool()


def get_sslexpiretime(request):
    expiretime_list = []
    ssl_result_dict = {}
    ssl_body_dict = {}
    success = False
    code = 500
    message = ''

    try:
        page = int(request.GET['page'])
        limit = int(request.GET['limit'])
    except Exception as e:
        print("%s:未传入，使用默认值" % e)
        page = 1
        limit = 10

    try:
        domain_name = str(request.GET['domain_name'])
    except Exception as e:
        print("%s:未传入，按顺序查找" % e)
        domain_name = ''
    try:
        match_status = str(request.GET['match_status'])
    except Exception as e:
        print("%s:未传入，按顺序查找" % e)
        match_status = ''

    django_api.DjangoApi().os_environ_update()
    offset = (page-1)*limit     # （当前页数-1）*每页数量 = 每页的开始位置

    # 获取表数据总条数
    try:
        sql_count = "select count(id) from %s where domain_name like '%%%s%%' and match_status like '%%%s%%';" % ('ssl_expire_date', domain_name, match_status)
        total_count = int(mysql_conn.select(sql_count)[0][0])
    except Exception as e:
        print("%s:表中无数据或表数据异常" % e)
        total_count = 0

    if total_count > 0:
        try:
            # 执行查询表数据
            sql_cmd = "select * from %s where domain_name like '%%%s%%' and match_status like '%%%s%%' order by " \
                      "expire_date limit %s,%s ;" % ('ssl_expire_date', domain_name, match_status, offset, limit)
            result = mysql_conn.select(sql_cmd)
        except Exception as e:
            print("%s:sql查询异常" % e)
            pass
        else:
            # 循环赋值，定义列表
            try:
                for record in result:
                    ssl_id = record[0]
                    domain = record[1]
                    domain_name = record[2]
                    expire_date = record[3].strftime("%Y-%m-%d %H:%M:%S")
                    ssl_cn = record[4]
                    match_status = record[5]
                    if match_status == 'False':
                        match_status = '不匹配'
                    elif match_status == 'True':
                        match_status = '匹配'
                    time = record[6].strftime("%Y-%m-%d %H:%M:%S")

                    single_expiretime = dict()
                    single_expiretime['id'] = ssl_id
                    single_expiretime['domain'] = domain
                    single_expiretime['domain_name'] = domain_name
                    single_expiretime['expire_date'] = expire_date
                    single_expiretime['ssl_cn'] = ssl_cn
                    single_expiretime['match_status'] = match_status
                    single_expiretime['time'] = time
                    expiretime_list.append(single_expiretime)
                code = 200
                success = True
                message = 'ok'
            except Exception as e:
                print("%s:赋值出错可能是数据表字段有误,或数据库取数据有误" % e)
                pass
    ssl_body_dict['data'] = expiretime_list
    ssl_body_dict['count'] = total_count

    ssl_result_dict['code'] = code
    ssl_result_dict['success'] = success
    ssl_result_dict['message'] = message
    ssl_result_dict['body'] = ssl_body_dict
    expire_result_json = json.dumps(ssl_result_dict,ensure_ascii=False)

    return HttpResponse(expire_result_json, content_type="application/json,charset=utf-8")


if __name__ == "__main__":
    get_sslexpiretime('xxx')