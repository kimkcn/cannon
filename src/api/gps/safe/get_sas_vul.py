#!/usr/bin/env python3
# coding:utf-8
from django.http import HttpResponse
import json

from src.lib import db_mysql
mysql_conn = db_mysql.MyPymysqlPool()
from src.lib import django_api
django_api.DjangoApi().os_environ_update()


def get_sas_vul_count(request):
    vul_name_list = []
    vul_name_body_dict = {}
    vul_name_reponse_dict = {}
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
        vul_type = str(request.GET['vul_type'])
    except:
        vul_type = 'cve'

    offset = (page - 1) * limit  # （当前页数-1）*每页数量 = 每页的开始位置

    # 获取不同的漏洞名的和相同漏洞的个数
    sql_name_count = "select vul_name, count(*) from %s where vul_type = '%s' and vul_status = 1 group by vul_name order by count(*) desc;" % ('safe_sas_vul', vul_type)
    for i in mysql_conn.select(sql_name_count):
        single_name = {}
        #print(type(i), i)
        name = i[0]
        count = i[1]
        single_name[name] = count
        vul_name_list.append(single_name)
    code = '200'
    success = True
    message = 'ok'

    vul_name_body_dict['data'] = vul_name_list
    vul_name_body_dict['count'] = len(vul_name_list)

    vul_name_reponse_dict['code'] = code
    vul_name_reponse_dict['success'] = success
    vul_name_reponse_dict['message'] = message
    vul_name_reponse_dict['body'] = vul_name_body_dict
    vul_name_result_json = json.dumps(vul_name_reponse_dict, ensure_ascii=False)
    return HttpResponse(vul_name_result_json, content_type="application/json,charset=utf-8")


def get_sas_vul_list(request):
    vul_list = []
    vul_body_dict = {}
    vul_reponse_dict = {}
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
        vul_name = str(request.GET['vul_name'])
    except:
        vul_name = ''

    offset = (page - 1) * limit  # （当前页数-1）*每页数量 = 每页的开始位置
    # 获取表数据总条数
    try:
        sql_count = "select count(*) from %s where vul_name  = '%s' and vul_status = 1 ;" % ('safe_sas_vul', vul_name)
        total_count = int(mysql_conn.select(sql_count)[0][0])
    except:
        total_count = 0

    if total_count > 0:
        try:
            # 执行查询表数据
            sql_cmd = "select * from %s where vul_name = '%s' and vul_status = 1 limit %s,%s" % \
                      ('safe_sas_vul', vul_name, offset, limit)
            result = mysql_conn.select(sql_cmd)
        except:
            pass
        else:
            # 循环赋值，定义列表
            for record in result:
                vul_id = record[1]
                vul_type = record[2]
                vul_aliasname = record[4]
                vul_tag = record[5]
                first_time = record[6].strftime("%Y-%m-%d %H:%M:%S")
                lasttime = record[7].strftime("%Y-%m-%d %H:%M:%S")
                vul_status = record[8]
                instance_id = record[10]
                instance_name = record[11]
                instance_pub_ip = record[12]
                instance_pri_ip = record[13]

                single_vul_list = {}
                single_vul_list['vul_id'] = vul_id
                single_vul_list['vul_type'] = vul_type
                single_vul_list['vul_aliasname'] = vul_aliasname
                single_vul_list['vul_tag'] = vul_tag
                single_vul_list['first_time'] = first_time
                single_vul_list['lasttime'] = lasttime
                single_vul_list['vul_status'] = vul_status
                single_vul_list['instance_id'] = instance_id
                single_vul_list['instance_name'] = instance_name
                single_vul_list['instance_pub_ip'] = instance_pub_ip
                single_vul_list['instance_pri_ip'] = instance_pri_ip

                vul_list.append(single_vul_list)
            code = '200'
            success = True
            message = 'ok'

    vul_body_dict['data'] = vul_list
    vul_body_dict['count'] = total_count

    vul_reponse_dict['code'] = code
    vul_reponse_dict['success'] = success
    vul_reponse_dict['message'] = message
    vul_reponse_dict['body'] = vul_body_dict
    vul_result_json = json.dumps(vul_reponse_dict, ensure_ascii=False)

    return HttpResponse(vul_result_json, content_type="application/json,charset=utf-8")


if __name__ == "__main__":
    get_sas_vul_count('xxx')