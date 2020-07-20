#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 监听db中的告警数据，判断是否需要电话告警

from conf import alert_conf
from src.lib import db_redis
from src.lib import db_mysql
try:
    import simplejson as json
except ImportError:
    import json


def voice_call():
    from src.api.voice_call import duty_poll_api
    status = False

    print('start voice_call...')
    #url = "https://cn.ops.yangege.cn/api/duty_poll"
    #response = requests.get(url)
    #print(response.text)

    try:
        response = duty_poll_api.duty_handler_local()
        result = json.loads(response)
        print(result)
        code = result['code']
    except Exception as e:
        print('exception: %s' % e)
    else:
        if code == 200:
            status = True
    return status


def disaster_alert_listen(task_id=None):
    mysql_conn = db_mysql.MyPymysqlPool()
    # 告警统一聚合和过滤，如果有灾难级别报警，则发出电话告警
    sql = "select * from %s where current_state = 'ALARM' and priority = 1 limit 1" %(alert_conf.table_name)
    print(sql)
    #sql = "select * from %s where current_state = 'ALARM' limit 1" %(alert_conf.table_name)

    try:
        result = mysql_conn.select(sql)
    except:
        result = False

    if result:  # 检测到处于alarm状态的灾难告警
        # 检查已记录的告警状态，确认是否已经告警过
        key = 'cannon_voice_call_status'
        try:
            result = db_redis.RedisApi().check_exist_of_key(key)
        except:
            result = 1  # 查询不到，则默认存在，不告警，交给下次查询

        if result == 0:  # key不存在
            ret = voice_call()
            if ret:
                ttl = 1800
                value = '{}'
                db_redis.RedisApi().set_key_with_ttl(key, value, ttl)
    mysql_conn.dispose()
    return True


if __name__ == "__main__":
    voice_call()
    #disaster_alert_listen()
