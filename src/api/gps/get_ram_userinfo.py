#!/usr/bin/env python3
# coding:utf-8
import os
from django.http import HttpResponse
import json
from src.lib import db_mysql,django_api

mysql_conn = db_mysql.MyPymysqlPool()


def get_ram_userinfo(request):
    userinfo_list = []
    ram_result_dict = {}
    ram_body_dict = {}
    success = False
    code = 500
    message = ''

    try:
        page = int(request.GET['page'])
        limit = int(request.GET['limit'])
    except Exception as e:
        print("%s:未传入page或limit，使用默认值" % e)
        page = 1
        limit = 10

    try:
        username = str(request.GET['username'])
    except Exception as e:
        print("%s:未传入username，使用默认值" % e)
        username = ''

    django_api.DjangoApi().os_environ_update()
    offset = (page - 1) * limit  # （当前页数-1）*每页数量 = 每页的开始位置

    # 获取表数据总条数
    try:
        sql_count = "select count(id) from %s ;" % ('ram_user_info')
        total_count = int(mysql_conn.select(sql_count)[0][0])
    except Exception as e:
        print("%s:表数据为空，使用默认值" % e)
        total_count = 0

    if total_count > 0:
        try:
            # 执行查询表数据
            sql_cmd = "select * from %s where username like '%%%s%%' order by username limit %s,%s" % \
                      ('ram_user_info', username, offset, limit)
            result = mysql_conn.select(sql_cmd)
        except Exception as e:
            print("%s:查询数据失败" % e)
            pass
        else:
            # 循环赋值，定义列表
            for record in result:
                username = record[1]
                login_enable = record[2]
                try:
                    lastlogin_time = record[3].strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    print("%s:未获取到用户最后登录时间" % e)
                    lastlogin_time = ''
                policies_info = record[4]
                ak_info = record[5]

                single_userinfo = dict()
                single_userinfo['username'] = username
                single_userinfo['login_enable'] = login_enable
                single_userinfo['lastlogin_time'] = lastlogin_time
                single_userinfo['policies_info'] = policies_info
                single_userinfo['ak_info'] = ak_info

                userinfo_list.append(single_userinfo)
            code = 200
            success = True
            message = 'ok'
    ram_body_dict['data'] = userinfo_list
    ram_body_dict['count'] = total_count

    ram_result_dict['code'] = code
    ram_result_dict['success'] = success
    ram_result_dict['message'] = message
    ram_result_dict['body'] = ram_body_dict
    ram_result_json = json.dumps(ram_result_dict, ensure_ascii=False)

    print(ram_result_json)
    return HttpResponse(ram_result_json, content_type="application/json,charset=utf-8")


if __name__ == "__main__":
    get_ram_userinfo('xxx')