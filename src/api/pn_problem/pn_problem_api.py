#!/usr/bin/env python
#coding=utf-8

import time,json,urllib
from django.http import HttpResponse
from src.lib import db_mysql
from conf  import pn_problem_collect_conf


mysql_conn = db_mysql.MyPymysqlPool('mysql')
pn_event_table='pn_event'
pn_event_history_table='pn_event_history'
mysql_conn = db_mysql.MyPymysqlPool('mysql')
pn_master_list = tuple(pn_problem_collect_conf.pn_master_list)
pn_backup_list = tuple(pn_problem_collect_conf.pn_backup_list)
pn_aws_list = tuple(pn_problem_collect_conf.pn_aws_list)

#定义默认的code和status值
status = False
code = 500


# 将返回值打包成字典转为json格式
def to_json_result(code,message,status,data):
    dict_response = {}
    dict_response['code'] = code
    dict_response['success'] = status
    dict_response['message'] = message
    dict_response['body'] = data
    result = json.dumps(dict_response)
    return result

class UrlChuLi:
    """Url处理类，需要传入两个实参：UrlChuLi('实参','编码类型')，默认utf-8
    url编码方法：url_bm() url解码方法：url_jm()"""

    def __init__(self, can, encoding='utf-8'):
        self.can = can
        self.encoding = encoding

    def url_bm(self):
        """url_bm() 将传入的中文实参转为UrlEncode编码"""
        quma = str(self.can).encode(self.encoding)
        return urllib.parse.quote(quma)

    def url_jm(self):
        """url_jm() 将传入的url进行解码成中文"""
        quma = str(self.can)
        return urllib.parse.unquote(quma, self.encoding)

# 判断字符串是否是一个有效的时间字符串,并转为时间戳格式
def is_vaild_data(str_date):
    try:
        date = time.strptime(str_date, "%Y-%m-%d %H:%M:%S")
        time_stamp = int(time.mktime(date))
        return time_stamp
    except:
        return False

# 将时间戳转化为标准时间格式
def timestamp_to_time(timestamp):
    time_array = time.localtime(timestamp)
    standard_time = time.strftime("%Y-%m-%d %H:%M:%S", time_array)
    return standard_time

# 将总秒数转为天时分秒格式
def sec_to_time(sec):
    day = sec // 86400
    hour = (sec - day * 86400) // 3600
    minute = (sec - hour * 3600 - day * 86400) // 60
    second = sec - hour * 3600 - minute * 60 - day * 86400
    if day == 0 and hour == 0 and minute == 0:
        return (str(second) + "s")
    elif day == 0 and hour == 0 and minute != 0 and second != 0:
        return(str(minute) + "m " + str(second) + "s")
    elif day == 0 and hour == 0 and minute != 0 and second == 0:
        return(str(minute) + "m")
    elif day == 0 and hour != 0 and minute == 0 and second == 0:
        return(str(hour) + "h")
    elif day == 0 and hour != 0 and minute != 0 and second == 0:
        return(str(hour) + "h " + str(minute) + "m")
    elif day == 0 and hour != 0 and second != 0:
        return(str(hour) + "h " + str(minute) + "m " + str(second) + "s")
    elif day != 0 and hour == 0 and minute == 0 and second == 0:
        return(str(day) + "d")
    elif day != 0 and minute != 0 and second == 0:
        return(str(day) + "d " + str(hour) + "h " + str(minute) + "m" )
    elif day != 0 and hour != 0 and minute == 0 and second == 0:
        return(str(day) + "d " + str(hour) + "h")
    else:
        return(str(day) + "d " + str(hour) + "h " + str(minute) + "m " + str(second) + "s")



def  pn_status(request):
    from src.lib import django_api
    django_api.DjangoApi().os_environ_update()
    data_list = []
    #result_dict = {}
    body_dict = {}
    code = 500
    success = False
    if request.method == 'POST':  # 当提交表单时

        #postBody = request.body
        #postBody = postBody.decode()
        #postBody = UrlChuLi(postBody, "utf-8").url_jm()
        start_time = json.loads(request.body.decode()).get('start_time')
        end_time = json.loads(request.body.decode()).get('end_time')
        node = json.loads(request.body.decode()).get('node')
        pn_attribute = json.loads(request.body.decode()).get('pn_attribute')
        type = json.loads(request.body.decode()).get('type')

        if not start_time or not end_time :
            status_message = ' error : start_time,end_time value cannot be empty.'
            body_dict['data'] = data_list
            result_json = to_json_result(code, status_message, status,body_dict)
            return HttpResponse(result_json)

        start_time = is_vaild_data(start_time)
        end_time = is_vaild_data(end_time)

        if start_time > end_time:
            status_message = ' error : start_time cannot be greater than end_time.'
            body_dict['data'] = data_list
            result_json = to_json_result(code, status_message, status, body_dict)
            return HttpResponse(result_json)
        if not type:
            type = ''
        if pn_attribute:
            if pn_attribute == 'master':
                pn = pn_master_list
            elif pn_attribute == 'backup':
                pn = pn_backup_list
            elif pn_attribute == 'all':
                pn = pn_aws_list
            else:
                if pn_attribute == '':
                    node = ''
                    sql = "select clock,r_clock,pn_node,type from %s where clock BETWEEN %s AND %s  AND pn_node LIKE '%%%s%%' AND type LIKE '%%%s%%' ORDER BY clock DESC;" % (
                        pn_event_table, start_time, end_time, node, type)
                else:
                    status_message = "error for pn_attribute : pn_attribute value only 'master' or 'backup' or 'all'."
                    body_dict['data'] = data_list
                    result_json = to_json_result(code, status_message, success, body_dict)
                    return HttpResponse(result_json)

            sql = "select clock,r_clock,pn_node,type from %s where clock BETWEEN %s AND %s  AND pn_node IN %s AND type LIKE '%%%s%%' ORDER BY clock DESC;" % (
                pn_event_table, start_time, end_time, pn, type)
        else:
            if not node:
                node = ''
                print('node is null')
            sql = "select clock,r_clock,pn_node,type from %s where clock BETWEEN %s AND %s  AND pn_node LIKE '%%%s%%' AND type LIKE '%%%s%%' ORDER BY clock DESC;" % (
                pn_event_table, start_time, end_time, node, type)



        #sql = "select clock,r_clock,pn_node,type from %s where clock BETWEEN %s AND %s  AND pn_node IN '%%%s%%' AND type LIKE '%%%s%%' ;" % (
        #    pn_event_table, start_time, end_time, pn, type)
        print(sql,'sqlsqlsqlsqlsqls')
        '''
        if start_time is False or end_time is False:
            status_message = 'error for %s or %s : Please enter standard time format' % (start_time,end_time)
            result_json = to_json_result(code, status_message, success,data_list)
            return HttpResponse(result_json)
        if node and not type:
            sql = "select clock,r_clock,pn_node,type from %s where clock BETWEEN %s AND %s AND pn_node = %s;" % (
            pn_event_table, start_time, end_time, node)
        elif node and type:
            sql = "select clock,r_clock,pn_node,type from %s where clock BETWEEN %s AND %s AND pn_node = %s AND type = %s;" % (
            pn_event_table, start_time, end_time, node, type)
        elif pn_attribute and type:
            if pn_attribute == 'master':
                sql = "select clock,r_clock,pn_node,type from %s where clock BETWEEN %s AND %s AND pn_node in  %s AND type = %s;" % (
                pn_event_table, start_time, end_time, pn_master_list, type)
                print('type',type,sql)
            elif pn_attribute == 'backup':
                sql = "select clock,r_clock,pn_node,type from %s where clock BETWEEN %s AND %s AND pn_node in  %s AND type = %s;" % (
                pn_event_table, start_time, end_time, pn_backup_list, type)
            elif pn_attribute == 'all':
                sql = "select clock,r_clock,pn_node,type from %s where clock BETWEEN %s AND %s AND pn_node in  %s AND type = %s;" % (
                pn_event_table, start_time, end_time, pn_aws_list, type)
            else:
                status_message = "error for pn_attribute : pn_attribute value only 'master' or 'backup' or 'all'."
                result_json = to_json_result(code, status_message, success, data_list)
                return HttpResponse(result_json)
        elif pn_attribute and not type:
            if pn_attribute == 'master':
                sql = "select clock,r_clock,pn_node,type from %s where clock BETWEEN %s AND %s AND pn_node in  %s ;" % (
                pn_event_table, start_time, end_time, pn_master_list)
            elif pn_attribute == 'backup':
                sql = "select clock,r_clock,pn_node,type from %s where clock BETWEEN %s AND %s AND pn_node in  %s ;" % (
                pn_event_table, start_time, end_time, pn_backup_list)
            elif pn_attribute == 'all':
                sql = "select clock,r_clock,pn_node,type from %s where clock BETWEEN %s AND %s AND pn_node in  %s ;" % (
                pn_event_table, start_time, end_time, pn_aws_list)
            else:
                status_message = "error for pn_attribute : pn_attribute value only 'master' or 'backup' or 'all'."
                result_json = to_json_result(code, status_message, success, data_list)
                return HttpResponse(result_json)
        elif type and not pn_attribute and not node:
            sql = "select clock,r_clock,pn_node,type from %s where clock BETWEEN %s AND %s AND type = %s;" % (
            pn_event_table, start_time, end_time, type)
        elif not type and not pn_attribute and not node:
            sql = "select clock,r_clock,pn_node,type from %s where clock BETWEEN %s AND %s ;" % (
            pn_event_table, start_time, end_time)
            '''
        result = mysql_conn.select(sql)
        if not result:
            status_message = ' error : No eligible data.'
            body_dict['data'] = data_list
            result_json = to_json_result(code, status_message, status, body_dict)
            return HttpResponse(result_json)
        print(result)
        for r in result:
            result_dict = {}
            event_start_time = timestamp_to_time(r[0])
            event_end_time = timestamp_to_time(r[1])
            duration = int(r[1]) -int(r[0])
            #duration = sec_to_time(duration)
            if r[3] == 1:
                problem_type = 'delay'
            elif r[3] == 0:
                problem_type = 'block'
            result_dict['node'] = r[2]
            result_dict['clock'] = event_start_time
            result_dict['r_clock'] = event_end_time
            result_dict['duration'] = duration
            result_dict['problem_type'] = problem_type
            data_list.append(result_dict)
        status_message = 'succes'
        code = 0
        success = True
        body_dict['data'] = data_list
        result_json = to_json_result(code, status_message, success, body_dict)
        print(result_json)

        return HttpResponse(result_json)
    else:
        status_message = ' error : Please use post request.'
        result_json = to_json_result(code, status_message, status, data_list)
        return HttpResponse(result_json)


if __name__ == "__main__":
    pn_status('xxx')