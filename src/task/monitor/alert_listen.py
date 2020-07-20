#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 钉钉告警接口

from conf import alert_conf
from src.lib import db_redis
from src.lib import db_mysql
import requests
try:
    import simplejson as json
except ImportError:
    import json
ttl_time = 3600     # 钉钉告警的沉默时间


def voice_function():
    from src.api.voice_call import duty_poll_api
    print('start voice_call...')
    response = duty_poll_api.duty_handler('xxx')
    status = False
    result = json.loads(response)
    code = result['code']
    print(result, code)
    if code != 0:
        url = "https://cn.ops.yangege.cn/api/duty_poll"
        response = requests.get(url)
        result = json.loads(response.text)
        code = result['code']
        print(result, code)
        if code == 0:
            status = True
    else:
        status = True
    return status


def call_voice():
    # 检查已记录的告警状态，确认是否已经告警过
    key = 'cannon_voice_call_status'
    status = False  # 默认告警失败
    try:
        result = db_redis.RedisApi().check_exist_of_key(key)
    except:
        result = 1  # 查询不到，则默认存在，不告警，交给下次查询

    if result == 0:  # key不存在
        ret = voice_function()
        if ret:
            status = True
            ttl = 1800
            value = '{}'
            db_redis.RedisApi().set_key_with_ttl(key, value, ttl)
    return status


def query_oncall_owner():
    from src.api.voice_call import duty_poll_api
    result = duty_poll_api.query_duty_man()
    return result


def call_dingtalk(content, oncall, top_level):
    status = False
    ding_talk_api = "https://oapi.dingtalk.com/robot/send?access_token=522f14ab1a58de0443f574efdd035ffba3462b171b762cf96d665ff3fa039d17"
    headers = {
        'Content-Type': 'application/json',
    }
    values = {
        "msgtype": "markdown",
        "markdown": {
            "title": " 存在 [%s] 级别告警" % top_level,
            "text": content
        },
        "at": {
            "atMobiles": [
                oncall
            ],
            "isAtAll": False
        }
    }
    try:
        result = requests.post(ding_talk_api, data=json.dumps(values), headers=headers)
        print(result)
    except Exception:
        message = 'except'
        print(message)
    else:
        status = True
    return status


def query_redis_key_exist(key):
    status = True   # 默认key存在，不做任何处理
    try:
        result = db_redis.RedisApi().check_exist_of_key(key)
    except:
        print('except')  # 查询不到，则默认存在，不告警，交给下次查询
    else:
        status = True
        if result == 0:  # key不存在，可以写入
            status = False
    return status   # true表示key存在，false表示key不存在


def check_redis_key_content(value, key):
    status = False  # 默认内容不一致

    list_in_redis = json.loads(db_redis.RedisApi().get_value_of_string(key))['alert_id_list']

    print(value, list_in_redis)
    if len(value) == len(list_in_redis):
        if value == list_in_redis:
            status = True
            print('数据一致，跳过')
    return status


def set_redis_key(key, ttl, value):
    status = False  # 默认设置key不成功
    try:
        result = db_redis.RedisApi().set_key_with_ttl(key, value, ttl)
    except:
        print('except')
    else:
        status = True
    return status


def alert_listen(task_id=None):
    mysql_conn = db_mysql.MyPymysqlPool()
    status = False

    # 查出所有zabbix的未恢复告警
    sql = "select * from %s where current_state = 'ALARM' and alert_from = 'zabbix' order by start_time desc" %(alert_conf.table_name)
    try:
        db_result = mysql_conn.select(sql)
    except:
        print('except')
    else:
        if not db_result:
            status = True
            return status

        detail_all = ""
        top_level = '严重'    # 默认最高级别是为严重
        tmp_content = {}
        alert_id_list = []

        # 查询redis，判断是否处于沉默状态
        key = "cannon_zabbix_alert_status"

        for record in db_result:
            alert_id = record[0]
            alert_id_list.append(alert_id)
        tmp_content['alert_id_list'] = alert_id_list
        alert_num = len(alert_id_list)
        redis_key_content = json.dumps(tmp_content, ensure_ascii=False)
        print(redis_key_content)

        # 检查key是否存在
        result = query_redis_key_exist(key)
        if result:  # key存在
            result = check_redis_key_content(alert_id_list, key)
            # 检查内容是否一致
            if result:  # 内容一致，跳过本次告警检查
                status = True
                return status

        for record in db_result:
            alert_from = record[1]
            resource = record[4]
            alert_detail = record[6]
            start_time = record[9]

            if record[11] == 1:
                level = '灾难'
                top_level = '灾难'

                # 暂时屏蔽电话告警的功能
                # 触发电话告警
                # voice_call_result = call_voice()

            elif record[11] == 2:
                level = '严重'
            if alert_from == 'zabbix':
                alert_url = 'https://cannon-test.ops.yangege.cn/#/alert'
                tmp_detail = "> * Host: %s \n\n>[%s] %s [%s] \n\n" % (resource, level, alert_detail, start_time)
                detail_all += tmp_detail

        # 获取值班人信息
        result = query_oncall_owner()
        oncall = result['number']

        dingtalk_content = "告警总数: %s &emsp; 最高告警级别: %s  \n %s \n @%s \n 点击[告警中心](%s)查看告警详情" % \
                           (alert_num, top_level, detail_all, oncall, alert_url)
        print(dingtalk_content)

        result = call_dingtalk(dingtalk_content, oncall, top_level)
        result = set_redis_key(key, ttl_time, redis_key_content)
        if result:
            status = True
    mysql_conn.dispose()
    return status


if __name__ == "__main__":
    alert_listen()
