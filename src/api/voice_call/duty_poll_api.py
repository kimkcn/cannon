#!/usr/bin/env python3
#coding=utf-8

import time
import datetime
from django.http import HttpResponse
from conf import voice_call_conf
from src.api.voice_call import voice_notification_api
from src.lib import db_mysql

token = voice_call_conf.token_voice_call     #获取调用语音接口试需要的token
Duty_Roster = voice_call_conf.Duty_Roster     #获取假期人员排班表
Employee_List = voice_call_conf.Employee_List  #获取员工及电话号码对应信息
DefaultNum = voice_call_conf.DefaultNum   #获取默认值班号码
Sre_Number = voice_call_conf.Sre_Number   #获取日常按周轮班顺序列表
alert_content = voice_call_conf.alert_content    #获取语音告警的内容
PeopleNum=len(Sre_Number)
appname = 'sre'
employee_list_table =  'employee_list'
mysql_conn = db_mysql.MyPymysqlPool()

def CheckPhone(PhoneNum):
    if len(PhoneNum) != 11 or PhoneNum[0] != "1" or PhoneNum.isdigit() is False:
        return DefaultNum
    return PhoneNum


def duty_voice_call():
    today = time.strftime("%Y%m%d")
    voice_result = {'code': 500, 'success': False, 'message': 'voice call is fail!!!', 'data': ' '}
    if today in Duty_Roster:        #判断今天是否为排班假期时间，是则输出当天排班人员的姓名和手机号
        DutyMan = Duty_Roster[today]
        #DutyNum = Employee_List[DutyMan]
    else:
        WeekNum = int(time.strftime('%W'))      # 获取今天是第几周
        #WeekNum=int(datetime.datetime.strptime('20200315','%Y%m%d').strftime('%W'))       # 获取指定日期属于当年的第几周

        if WeekNum == 0:
            WeekNum = 52 % PeopleNum
        elif WeekNum >= PeopleNum:
            WeekNum = WeekNum % PeopleNum

        print("Today is week %d" % WeekNum)
        DutyMan = Sre_Number[WeekNum]
        #DutyNum = Employee_List[DutyMan]
    select_number_sql = "select number from %s where stage_name = '%s';" % (employee_list_table, DutyMan)
    #DutyNum = mysql_conn.select(select_number_sql)
    try:
        sql_result = mysql_conn.select(select_number_sql)
    except Exception as e:
        voice_result['message'] = 'Exception:Failed to get the dutyer number from the mysql'
        print("Exception:Failed to get the dutyer number from the mysql",e)
    else:
        if sql_result:
            for i in sql_result:
                for DutyNum in i:
                    DutyNum = str(DutyNum)
            DutyNum = CheckPhone(DutyNum)
            voice_result = voice_notification_api.voice_alert(DutyNum, appname, token, alert_content)

    return voice_result


def duty_handler_local():
    voice_result = duty_voice_call()
    return voice_result


def duty_handler(request):
    voice_result = duty_voice_call()
    return HttpResponse(voice_result)


def query_duty_man(duty_time = time.strftime("%Y%m%d")):
    result ={}
    if isinstance(duty_time,int):
        duty_time = str(duty_time)
    try:
        datetime.datetime.strptime(duty_time, '%Y%m%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYYMMDD")
    if duty_time in Duty_Roster:        #判断今天是否为排班假期时间，是则输出当天排班人员的姓名和手机号
        DutyMan = Duty_Roster[duty_time]
        #DutyNum = Employee_List[DutyMan]
    else:
        #WeekNum = int(time.strftime('%W'))      # 获取今天是第几周
        WeekNum=int(datetime.datetime.strptime(duty_time,'%Y%m%d').strftime('%W'))       # 获取指定日期属于当年的第几周

        if WeekNum == 0:
            WeekNum = 52 % PeopleNum
        elif WeekNum >= PeopleNum:
            WeekNum = WeekNum % PeopleNum

        #print("Today is week %d" % WeekNum)
        DutyMan = Sre_Number[WeekNum]
        #DutyNum = Employee_List[DutyMan]
    select_number_sql = "select number from %s where stage_name = '%s';" % (employee_list_table, DutyMan)
    aql_result = mysql_conn.select(select_number_sql)
    
    if not aql_result:
        result['name'] = 'jiji'
        result['number'] = 15757185179
    else:
        for i in aql_result:
            for DutyNum in i:
                DutyNum = DutyNum
        result['name'] = DutyMan
        result['number'] = DutyNum


    return result


if __name__ == '__main__':
    duty_handler('xxx')
