#!/usr/bin/env python
#coding=utf-8

import os,logging,time,json,urllib,configparser
from django.http import HttpResponse,request,HttpRequest
from conf import voice_call_conf
from src.lib import db_mysql

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkdyvmsapi.request.v20170525.SingleCallByTtsRequest import SingleCallByTtsRequest

#accessKeyid = voice_call_conf.accessKeyid   # 获取阿里云accessKeyId值
#accessSecret = voice_call_conf.accessSecret     # 获取阿里云accessSecret值
#area = voice_call_conf.area     # 获取阿里云area值
logfile = voice_call_conf.logfile   # 获取日志输出路径
retry_count = voice_call_conf.retry_count   # 获取错误重试次数
retry_interval = voice_call_conf.retry_interval     # 获取错误重试间隔时间
mysql_conn = db_mysql.MyPymysqlPool('mysql')

file_path = os.path.join(os.path.dirname(__file__), "../../../conf/key.conf")
cf = configparser.ConfigParser()
cf.read(file_path)
ak_section = 'voice'    # 默认用阿里云主账号的a k
accessKeyid = cf.get(ak_section, 'AccessKeyId')
accessSecret = cf.get(ak_section, 'AccessKeySecret')
area = cf.get(ak_section, 'DefaultRegionId')

#定义默认的code和status值
status = False
code = 500

#将日志文件路径拆分成目录和文件，通过判断依次创建
logfilename = os.path.dirname(__file__) + '/voice_call.log'
#(logfilepath,logfilename) = os.path.split(logfile)
#if not os.path.isfile(logfile):
#    if not os.path.exists(logfilepath):
#        os.makedirs(logfilepath)
#    os.chdir(logfilepath)
#    #os.mknod(logfilename)

client = AcsClient(accessKeyid, accessSecret, area)


def record_info_log(message):
    LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"  #配置输出日志格式
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'  #配置输出时间的格式，注意月份和天数不要搞乱了
    logging.basicConfig(level=logging.INFO,
                        format=LOG_FORMAT,
                        datefmt = DATE_FORMAT,
                        filemode = 'a',
                        filename = logfilename
                        )
    logging.info(message)

    return True

def record_error_log(message):
    LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"  #配置输出日志格式
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'  #配置输出时间的格式，注意月份和天数不要搞乱了
    logging.basicConfig(level=logging.INFO,
                        format=LOG_FORMAT,
                        datefmt = DATE_FORMAT,
                        filemode = 'a',
                        filename = logfilename
                        )
    logging.error(message)

    return True

# 将返回值打包成字典转为json格式
def to_json_result(code,message,status):
    dict_response = {}
    dict_response['code'] = code
    dict_response['success'] = status
    dict_response['message'] = message
    dict_response['data'] = ' '
    result = json.dumps(dict_response)
    return result

def voice_alert(number,appname,token,alert_content,parameter=""):
    log_table_name = 'voice_call_log'
    token_table_name = 'voice_call_token'
    status = False
    code = 500
    now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    if not number or not appname or not token :
        status_message = ' error : appname,number,token value cannot be empty.'
        alert_result_json = to_json_result(code, status_message, status)
        return alert_result_json

    select_token_record_sql = "select * from %s where token = '%s';" % (token_table_name, token)
    try:
        result = mysql_conn.select(select_token_record_sql)   #根据传入的token值来匹配数据
    except Exception as e:
        status_message = e
    else:
        if not result:
            print('invalid token')
            status_message = 'error: {} is an invalid token'.format(token)
            alert_result_json = to_json_result(code, status_message, status)
            return alert_result_json

        if len(number) != 11 or number[0] != "1" or number.isdigit() is False:
            status_message ='error: {} is an invalid mobile number'.format(number)
            alert_result_json = to_json_result(code, status_message, status)
            return alert_result_json
        attempts = 0
        status = False
        while attempts < retry_count and not status:
            try:
                AliRequest = SingleCallByTtsRequest()
                AliRequest.set_accept_format('json')
                AliRequest.set_CalledShowNumber("051068584651")
                AliRequest.set_CalledNumber(number)
                AliRequest.set_TtsCode("TTS_180955214")
                AliRequest.set_TtsParam(alert_content)
                AliRequest.set_PlayTimes(2)
                AliRequest.set_Volume(100)
                response = client.do_action_with_exception(AliRequest)
                print(response)
                CodeReq = '"Code":"OK"'
                CodeReq = CodeReq.encode()
                code_result = CodeReq in response
                if not code_result:
                    raise Exception('voice call is fail!!!')
            except Exception as Err:
                status = False
                status_message = str(Err)
                record_error_log(status_message)
                time.sleep(retry_interval)
            else:
                status_message = "voice call is sucess!!!"
                status = True
                code = 200
                insert_new_record_sql = "insert into %s(date,appname,number,alert_content,token) " \
                                        "values('%s','%s','%s','%s','%s')" % (
                                            log_table_name, now_time, appname, number, parameter, token)
                mysql_conn.insert(insert_new_record_sql)  # 将此次语音接口调用记录插入到sql表中
                mysql_conn.end()
                message = "appname:%s, called_number: %s %s" % (appname, number, response)
                record_info_log(message)
            attempts += 1
    alert_result_json = to_json_result(code, status_message, status)
    return alert_result_json

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

def  call_up(request):
    if request.method == 'POST':  # 当提交表单时
        postBody = request.body
        postBody = postBody.decode()
        postBody = UrlChuLi(postBody, "utf-8").url_jm()
        appname = json.loads(request.body.decode()).get('appname')
        content = json.loads(request.body.decode()).get('content')
        number = json.loads(request.body.decode()).get('number')
        token = json.loads(request.body.decode()).get('token')
        if content and len(content) < 20:
            alert_content = str({"告警内容": "{}".format(content)})
        else:
            alert_content = str({"告警内容": "触发灾难级告警"})
        alert_result_json = voice_alert(number, appname, token, alert_content, postBody)
    else:
        status_message = 'error: please use method post to request'
        alert_result_json = to_json_result(code, status_message, status)
        return HttpResponse(alert_result_json)

    return HttpResponse(alert_result_json)

if __name__ == "__main__":
    call_up('xxx')