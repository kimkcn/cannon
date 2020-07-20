#!/usr/bin/env python
#coding=utf-8

import time,json,urllib
from django.http import HttpResponse
from src.lib import db_mysql
from conf  import pn_problem_collect_conf

pn_event_delay_data_table='pn_event_delay_data'
pn_event_data_table='pn_event_data'
pn_event_history_table='pn_event_history'
pn_master_list = tuple(pn_problem_collect_conf.pn_master_list)
pn_backup_list = tuple(pn_problem_collect_conf.pn_backup_list)
pn_aws_list = tuple(pn_problem_collect_conf.pn_aws_list)
pn_aliyun_list = tuple(pn_problem_collect_conf.pn_aliyun_list)

#定义默认的code和status值
#status = False
#code = 500


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
    body_dict = {}
    body_dict['data'] = data_list

    # 定义默认的code和status值
    code = 500
    success = False
    if request.method == 'POST':  # 当提交表单时
        try:
            start_time = json.loads(request.body.decode()).get('start_time')
            end_time = json.loads(request.body.decode()).get('end_time')
            source_node = json.loads(request.body.decode()).get('source_node')
            node = json.loads(request.body.decode()).get('node')
            pn_attribute = json.loads(request.body.decode()).get('pn_attribute')
            type = json.loads(request.body.decode()).get('type')
        except Exception as e:
            print(e,'error: Failed to get transfer parameters.')
            status_message = " error : Failed to get transfer parameters."
            result_json = to_json_result(code, status_message, success, body_dict)
            return HttpResponse(result_json)
        #判断传入的源节点参数，并进行转换
        if source_node:
            if source_node not in ('aws','aliyun') and source_node != '':
                status_message = " error : source_node' value is incorrect."
                result_json = to_json_result(code, status_message, success, body_dict)
                return HttpResponse(result_json)
            else:
                if source_node == 'aliyun':
                    source_node = 'opscloud-1'
                elif source_node == 'aws':
                    source_node = 'aws-template-2'
                elif source_node == '':
                    source_node = 'opscloud-1'
        else:
            source_node = 'opscloud-1'

        if not start_time or not end_time :
            status_message = ' error : start_time,end_time value cannot be empty.'
            result_json = to_json_result(code, status_message, success,body_dict)
            return HttpResponse(result_json)

        start_time = is_vaild_data(start_time)
        end_time = is_vaild_data(end_time)

        if not start_time or  not end_time:
            status_message = ' error : One of start_time and end_time value is invaild.'
            result_json = to_json_result(code, status_message, success, body_dict)
            return HttpResponse(result_json)


        if start_time > end_time:
            status_message = ' error : start_time cannot be greater than end_time.'
            result_json = to_json_result(code, status_message, success, body_dict)
            return HttpResponse(result_json)
        if not type:
            pn_type = 0
        else:
            if type == 'telnet':
                pn_type = 2
            elif type == 'dealy':
                pn_type = 1
            elif  type == 'block':
                pn_type = 0


        if not node or node == '':
            if pn_attribute == 'master':
                node = pn_master_list
            elif pn_attribute == 'backup':
                node = pn_backup_list
            elif pn_attribute == '' or not pn_attribute or pn_attribute == 'all':
                if source_node == 'opscloud-1':
                    node = pn_aws_list
                elif source_node == 'aws-template-2':
                    node = pn_aliyun_list
        else:
            pn_list = pn_master_list + pn_backup_list + pn_aws_list + pn_aliyun_list
            print('pn_list',pn_list)
            if node not in pn_list:
                print("存在")
                print('111', node, pn_master_list)
                status_message = " error : node' value is incorrect. "
                body_dict['data'] = data_list
                result_json = to_json_result(code, status_message, success, body_dict)
                return HttpResponse(result_json)
            node = "('" + node + "')"   #将节点名称以字符串 转成类似元组的形式，sql语句只接受元组形式

        sql = "SELECT source,pn_node,type , MAX(r_clock - clock + 1) AS MaxDuration , SUM(r_clock - clock + 1) AS TotalDuration , COUNT(*) AS NumberOfTimes " \
              "FROM %s " \
              "WHERE clock BETWEEN %s AND %s  AND type = %s AND source = '%s'  AND pn_node IN %s " \
              "GROUP BY pn_node;" % (
                pn_event_data_table, start_time, end_time, pn_type, source_node, node)
        print('sql',sql)


        try:
            mysql_conn_dict = db_mysql.MyPymysqlPoolDict()
            result = mysql_conn_dict.select(sql)
            print('sql_result',result)
            mysql_conn_dict.dispose()
        except Exception as e:
            mysql_conn_dict.dispose()
            status_message = 'error: Database query failed. '
            print(e, status_message)
            result_json = to_json_result(code, status_message, success, body_dict)
            return HttpResponse(result_json)
        else:
            if not result:
                status_message = ' error : No eligible data.'
                result_json = to_json_result(code, status_message, success, body_dict)
                return HttpResponse(result_json)
            print('sql_result02',result)
            for r in result:
                if r['source'] == 'opscloud-1':
                    r['source'] = 'aliyun'
                elif r['source'] == 'aws-template-2':
                    r['source'] = 'aws'

                if r['pn_node'] == 'opscloud-1':
                    r['pn_node'] = 'aliyun'
                elif r['pn_node'] == 'aws-template-3':
                    r['pn_node'] = 'aws'
                r['TotalDuration'] = int(r['TotalDuration'])
            print('sql_result03', result)

            status_message = 'succes'
            code = 0
            success = True
            body_dict['data'] = result
            result_json = to_json_result(code, status_message, success, body_dict)
            print(result_json)

            return HttpResponse(result_json)
    else:
        status_message = ' error : Please use post request.'
        result_json = to_json_result(code, status_message, success, data_list)
        return HttpResponse(result_json)

def judge_source(source_node):
    if source_node not in ('aws', 'aliyun'):
        status_message = " error : source_node' value is incorrect."
        return status_message,False
    else:
        if source_node == 'aliyun':
            source_node = 'opscloud-1'
        elif source_node == 'aws':
            source_node = 'aws-template-2'

    return source_node

def judge_time(start_time,end_time):
    print(start_time,end_time)
    try:
        start_time = time.strptime(start_time, "%Y-%m-%d")
        end_time = time.strptime(end_time, "%Y-%m-%d")
    except Exception as e :
        status_message = ' error : One of start_time and end_time value is invaild.'
        print(e,status_message)
        return False
    else:
        if start_time > end_time:
            status_message = ' error : start_time cannot be greater than end_time.'
            return False
    return True

def  pn_delay_status(request):
    from src.lib import django_api
    django_api.DjangoApi().os_environ_update()
    data_list = []
    body_dict = {}
    body_dict['data'] = data_list
    # 定义默认的code和status值
    code = 500
    success = False
    if request.method == 'POST':  # 当提交表单时
        try:
            start_time = json.loads(request.body.decode()).get('start_time')
            end_time = json.loads(request.body.decode()).get('end_time')
            source_node = json.loads(request.body.decode()).get('source_node')
            node = json.loads(request.body.decode()).get('node')
            pn_attribute = json.loads(request.body.decode()).get('pn_attribute')
        except Exception as e:
            print(e,'error: Failed to get transfer parameters.')
            status_message = " error : Failed to get transfer parameters."
            result_json = to_json_result(code, status_message, success, body_dict)
            return HttpResponse(result_json)
        #判断传入的源节点参数
        if source_node:
            if source_node not in ('aws','aliyun') and source_node != '':
                status_message = " error : source_node' value is incorrect."
                result_json = to_json_result(code, status_message, success, body_dict)
                return HttpResponse(result_json)
            elif source_node == '':
                source_node = 'aliyun'
        else:
            source_node = 'aliyun'

        if start_time and end_time :
            result_time = judge_time(start_time, end_time)
            if not result_time:
                status_message = " error :One of start_time and end_time value is incorrect."
                result_json = to_json_result(code, status_message, success, body_dict)
                return HttpResponse(result_json)
        else:
            status_message = ' error : start_time,end_time value cannot be empty.'
            result_json = to_json_result(code, status_message, success, body_dict)
            return HttpResponse(result_json)



        if not node or node == '':
            if pn_attribute == 'master':
                node = pn_master_list
            elif pn_attribute == 'backup':
                node = pn_backup_list
            elif pn_attribute == '' or not pn_attribute or pn_attribute == 'all':
                if source_node == 'aliyun':
                    node = pn_aws_list
                elif source_node == 'aws':
                    node = pn_aliyun_list
        else:
            pn_list = pn_master_list + pn_backup_list + pn_aws_list + pn_aliyun_list
            print('pn_list',pn_list)
            if node not in pn_list:
                status_message = " error : node' value is incorrect. "
                result_json = to_json_result(code, status_message, success, body_dict)
                return HttpResponse(result_json)
            node = "('" + node + "')"   #将节点名称以字符串 转成类似元组的形式，sql语句只接受元组形式

        sql = "SELECT CAST(date AS CHAR ) AS date,source,PNnode,valueAvg,valueMax,valueA,valueB,valueC,valueD,valueE,valueF,valueG,valueH,valueI,valueJ,valueK " \
              "FROM %s " \
              "where date BETWEEN '%s' AND '%s' AND source = '%s' AND PNnode IN %s;" % (
                pn_event_delay_data_table, start_time, end_time, source_node, node)
        print('sql',sql)


        try:
            mysql_conn_dict = db_mysql.MyPymysqlPoolDict()
            result = mysql_conn_dict.select(sql)
            print('sql_result',result)
            mysql_conn_dict.dispose()
        except Exception as e:
            mysql_conn_dict.dispose()
            status_message = 'error: Database query failed. '
            print(e,status_message)
            result_json = to_json_result(code, status_message, success, body_dict)
            return HttpResponse(result_json)
        else:
            if not result:
                status_message = ' error : No eligible data.'
                result_json = to_json_result(code, status_message, success, body_dict)
                return HttpResponse(result_json)
            print('sql_result02',result)

            status_message = 'succes'
            code = 0
            success = True
            body_dict['data'] = result
            result_json = to_json_result(code, status_message, success, body_dict)
            print(result_json)

            return HttpResponse(result_json)
    else:
        status_message = ' error : Please use post request.'
        result_json = to_json_result(code, status_message, success, body_dict)
        return HttpResponse(result_json)

if __name__ == "__main__":
    pn_status('xxx')