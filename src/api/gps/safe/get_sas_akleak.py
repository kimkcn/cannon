#!/usr/bin/env python3
# coding:utf-8
from django.http import HttpResponse
import json

from src.lib import db_mysql
mysql_conn = db_mysql.MyPymysqlPool()
from src.lib import django_api
django_api.DjangoApi().os_environ_update()


def get_sas_akleak(request):
    akleak_list = []
    akleak_body_dict = {}
    akleak_reponse_dict = {}
    success = False
    code = 1
    message = ''

    try:
        page = int(request.GET['page'])
        limit = int(request.GET['limit'])
    except:
        page = 1
        limit = 10

    try:
        ak_id = str(request.GET['ak_id'])
    except:
        ak_id = ''

    offset = (page - 1) * limit  # （当前页数-1）*每页数量 = 每页的开始位置

    # 获取表数据总条数
    try:
        sql_count = "select count(id) from %s ;" % ('safe_sas_akleak')
        total_count = int(mysql_conn.select(sql_count)[0][0])
    except:
        total_count = 0
    print(total_count)

    if total_count > 0:
        try:
            # 执行查询表数据
            sql_cmd = "select * from %s where ak_id like '%%%s%%' limit %s,%s" % \
                      ('safe_sas_akleak', ak_id, offset, limit)
            result = mysql_conn.select(sql_cmd)
        except:
            pass
        else:
            # 循环赋值，定义列表
            for record in result:
                ak_id = record[1]
                host = record[2]
                fileurl = record[3]
                repourl = record[4]
                user = record[5]
                filetype = record[6]
                code = record[7]

                single_akleak = {}
                single_akleak['ak_id'] = ak_id
                single_akleak['host'] = host
                single_akleak['fileurl'] = fileurl
                single_akleak['repourl'] = repourl
                single_akleak['user'] = user
                single_akleak['filetype'] = filetype
                single_akleak['code'] = code

                akleak_list.append(single_akleak)
            code = '200'
            success = True
            message = 'ok'

    akleak_body_dict['data'] = akleak_list
    akleak_body_dict['count'] = total_count

    akleak_reponse_dict['code'] = code
    akleak_reponse_dict['success'] = success
    akleak_reponse_dict['message'] = message
    akleak_reponse_dict['body'] = akleak_body_dict
    akleak_result_json = json.dumps(akleak_reponse_dict, ensure_ascii=False)

    return HttpResponse(akleak_result_json, content_type="application/json,charset=utf-8")


if __name__ == "__main__":
    get_sas_akleak('xxx')