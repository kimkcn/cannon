#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import sys, datetime, os
sys.path.append("..")
from django.http import HttpResponse
from conf import alert_conf
from src.lib import db_mysql
from django.views.decorators.clickjacking import xframe_options_sameorigin
try:
    import simplejson as json
except ImportError:
    import json


def show_task_schedule(request):
    table_name = 'task_scheduler'
    job_id = str(request.GET['job_id'])
    job_name = str(request.GET['job_name'])
    job_status = str(request.GET['job_status'])

    data_list = []
    body_dict = {}
    result_dict = {}
    from src.lib import django_api
    django_api.DjangoApi().os_environ_update()
    mysql_conn = db_mysql.MyPymysqlPoolDict()
    code = 500
    message = "fail"
    success = False

    sql = "select * from %s where job_id like '%%%s%%' and job_name like '%%%s%%' and " \
          "job_status like '%%%s%%' order by last_schedule_starttime desc;" % \
          (table_name, job_id, job_name, job_status)

    try:
        tmp_result = mysql_conn.select(sql)
    except Exception as e:
        print(e)
    else:
        if tmp_result:
            for record in tmp_result:
                if record['job_status'] == 'normal':
                    record['job_status'] = '正常'
                else:
                    record['job_status'] = '暂停'
                if record['last_schedule_status'] in ['True', 'success']:
                    record['last_schedule_status'] = '成功'
                else:
                    record['last_schedule_status'] = '失败'
                record['last_schedule_starttime'] = record['last_schedule_starttime'].strftime("%Y-%m-%d %H:%M:%S")
                record['last_schedule_endtime'] = record['last_schedule_endtime'].strftime("%Y-%m-%d %H:%M:%S")
        else:
            tmp_result = ""
        code = 0
        message = "ok"
        success = True
        data_list = tmp_result
    finally:
        mysql_conn.dispose()

    body_dict['data'] = data_list
    result_dict = {'code': code, 'success': success, 'message': message, 'body': body_dict}
    result_json = json.dumps(result_dict, ensure_ascii=False)
    return HttpResponse(result_json, content_type="application/json,charset=utf-8")


def query_task_job_config(request):
    table_name = 'task_job_config'
    try:
        job_id = str(request.GET['jobId'])
        job_status = str(request.GET['jobStatus'])
    except:
        job_id = ""
        job_status = ""

    data_list = []
    body_dict = {}
    from src.lib import django_api
    django_api.DjangoApi().os_environ_update()
    mysql_conn = db_mysql.MyPymysqlPoolDict()
    code = 500
    message = "fail"
    success = False

    try:
        sql = "select id, job_id jobId, `trigger`, trigger_args triggerArgs, jitter, run_at_startup runAtStartup, " \
              "enable jobStatus from %s where job_id like '%%%s%%' and enable like '%%%s%%' order by " \
              "trigger_args desc;" % (table_name, job_id, job_status)
        print("sql: ", sql)
        tmp_result = mysql_conn.select(sql)
        print(tmp_result, type(tmp_result))
    except Exception as e:
        print(e)
    else:
        if not tmp_result:
            tmp_result = ""
        code = 200
        success = True
        message = "ok"
        data_list = tmp_result
    finally:
        mysql_conn.dispose()

    body_dict['data'] = data_list
    result_dict = {'code': code, 'success': success, 'message': message, 'body': body_dict}
    result_json = json.dumps(result_dict, ensure_ascii=False)
    print(result_json)
    return HttpResponse(result_json, content_type="application/json,charset=utf-8")


def update_task_job_config(request):    # 任务配置信息的变更接口!
    code = 500
    success = False
    message = 'fail'
    result_dict = {'code': code, 'success': success, 'message': message}
    from src.lib import django_api
    django_api.DjangoApi().os_environ_update()

    if request.method == 'PUT':  # 当提交表单时
        mysql_conn = db_mysql.MyPymysqlPoolDict()
        table_name = 'task_job_config'
        table_id = json.loads(request.body.decode()).get('id')
        job_id = json.loads(request.body.decode()).get('jobId')
        trigger = json.loads(request.body.decode()).get('trigger')
        trigger_args = json.loads(request.body.decode()).get('triggerArgs')
        jitter = json.loads(request.body.decode()).get('jitter')
        run_at_startup = json.loads(request.body.decode()).get('runAtStartup')
        job_status = json.loads(request.body.decode()).get('jobStatus')

        if not job_id or not trigger or not trigger_args:
            result_dict['message'] = '必填参数(*)不能为空'
            result_json = json.dumps(result_dict, ensure_ascii=False)
            return HttpResponse(result_json, content_type="application/json,charset=utf-8")

        if trigger == "crontab":
            values = trigger_args.split()
            if len(values) != 5:
                result_dict['message'] = 'crontab参数列数不正确，输入 {}, 需要 5'.format(len(values))
                result_json = json.dumps(result_dict, ensure_ascii=False)
                return HttpResponse(result_json, content_type="application/json,charset=utf-8")
        elif trigger == "cron":
            import re
            if not re.search('second', trigger_args):
                result_dict['message'] = 'cron仅支持second！'
                result_json = json.dumps(result_dict, ensure_ascii=False)
                return HttpResponse(result_json, content_type="application/json,charset=utf-8")

        update_sql = "update %s set job_id='%s',`trigger`='%s', trigger_args='%s', jitter=%s, run_at_startup='%s', " \
                     "enable='%s' where `id`=%s" % \
                     (table_name, job_id, trigger, trigger_args, jitter, run_at_startup, job_status, table_id)
        print('update_sql: ', update_sql)
        try:
            mysql_conn.update(update_sql)
        except Exception as e:
            print('update task exception: ', e)
            result_dict['message'] = "更新数据库异常"
        else:
            result_dict['code'] = 200
            result_dict['success'] = True
            result_dict['message'] = "更新任务成功"
        mysql_conn.dispose()
    else:
        result_dict['message'] = '请求方法错误'

    result_json = json.dumps(result_dict, ensure_ascii=False)
    print(result_json)
    return HttpResponse(result_json, content_type="application/json,charset=utf-8")


def add_task_job_config(request):    # 任务配置信息的变更接口!
    code = 500
    success = False
    message = 'fail'
    result_dict = {'code': code, 'success': success, 'message': message}
    from src.lib import django_api
    django_api.DjangoApi().os_environ_update()

    if request.method == 'POST':  # 当提交表单时
        print(request.body.decode())
        table_name = 'task_job_config'
        job_id = json.loads(request.body.decode()).get('jobId')
        trigger = json.loads(request.body.decode()).get('trigger')
        trigger_args = json.loads(request.body.decode()).get('triggerArgs')

        if not job_id or not trigger or not trigger_args:
            result_dict['message'] = '必填参数(*)不能为空'
            result_json = json.dumps(result_dict, ensure_ascii=False)
            return HttpResponse(result_json, content_type="application/json,charset=utf-8")

        if trigger == "crontab":
            values = trigger_args.split()
            if len(values) != 5:
                result_dict['message'] = 'crontab参数列数不正确，输入 {}, 需要 5'.format(len(values))
                result_json = json.dumps(result_dict, ensure_ascii=False)
                return HttpResponse(result_json, content_type="application/json,charset=utf-8")
        elif trigger == "cron":
            import re
            if not re.search('second', trigger_args):
                result_dict['message'] = 'cron仅支持second！'
                result_json = json.dumps(result_dict, ensure_ascii=False)
                return HttpResponse(result_json, content_type="application/json,charset=utf-8")

        # 判断记录是否已存在
        mysql_conn = db_mysql.MyPymysqlPoolDict()
        sql = "select * from %s where job_id = '%s'" % (table_name, job_id)
        try:
            tmp_result = mysql_conn.select(sql)
        except Exception as e:
            print('query task exception: ', e)
            result_dict['message'] = "查询数据库失败"
        else:
            if tmp_result:
                result_dict['message'] = '记录已存在'
            else:
                jitter = json.loads(request.body.decode()).get('jitter')
                run_at_startup = json.loads(request.body.decode()).get('runAtStartup')
                job_status = json.loads(request.body.decode()).get('jobStatus')

                add_sql = "INSERT INTO %s (`job_id`, `trigger`, `trigger_args`, `jitter`, `run_at_startup`, `enable`)" \
                          " VALUES ('%s', '%s', '%s', %s, '%s', '%s');" % \
                          (table_name, job_id, trigger, trigger_args, jitter, run_at_startup, job_status)
                try:
                    mysql_conn.insert(add_sql)
                except Exception as e:
                    print('insert task exception: ', e)
                    result_dict['message'] = "写入数据库异常"
                else:
                    result_dict['code'] = 200
                    result_dict['success'] = True
                    result_dict['message'] = "增加任务成功"
        mysql_conn.dispose()
    else:
        result_dict['message'] = '请求方法错误'

    result_json = json.dumps(result_dict, ensure_ascii=False)
    print(result_json)
    return HttpResponse(result_json, content_type="application/json,charset=utf-8")


def delete_task_job_config(request):    # 任务配置信息的变更接口!
    code = 500
    success = False
    data_list = []
    body_dict = {}
    from src.lib import django_api
    django_api.DjangoApi().os_environ_update()

    if request.method == 'POST':  # 当提交表单时
        mysql_conn = db_mysql.MyPymysqlPoolDict()
        table_name = 'task_job_config'
        table_id = int(request.body.decode())
        #table_id = json.loads(request.body.decode()).get('id')
        delete_sql = "delete from %s where id=%s" % (table_name, table_id)
        try:
            mysql_conn.delete(delete_sql)
        except Exception as e:
            print('delete task exception: ', e)
        else:
            code = 200
            success = True
            message = "删除任务成功"
        mysql_conn.dispose()
    else:
        message = '请求方法错误'

    body_dict['data'] = data_list
    result_dict = {'code': code, 'success': success, 'message': message, 'body': body_dict}
    result_json = json.dumps(result_dict, ensure_ascii=False)
    print(result_json)
    return HttpResponse(result_json, content_type="application/json,charset=utf-8")


if __name__ == "__main__":
    #show_task_schedule('xxx')
    query_task_job_config('xxx')
