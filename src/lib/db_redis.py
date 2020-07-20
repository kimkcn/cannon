#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import redis
import os
import configparser
from cannon_manage import env

env_conf_file = "../../conf/env-%s.conf" % env


class RedisApi:
    def __init__(self):
        file_path = os.path.join(os.path.dirname(__file__), env_conf_file)
        cf = configparser.ConfigParser()
        cf.read(file_path)
        ak_section = "redis"
        redis_host = cf.get(ak_section, 'redis_host')
        redis_port = cf.get(ak_section, 'redis_port')
        redis_passwd = cf.get(ak_section, 'redis_passwd')
        self.conn = redis.Redis(host=redis_host, port=redis_port, password=redis_passwd, decode_responses=True)

    def get_value_of_string(self, key):
        result = self.conn.get(key)
        return result

    def check_exist_of_key(self, key):
        # 0: key不存在； 1: key存在
        result = self.conn.exists(key)
        return result

    def set_key_with_ttl(self, key, value, ttl):
        ret = self.conn.set(key, value, ex=ttl)
        if ret:
            return True
        else:
            return False

    def set_key(self, key, value):
        ret = self.conn.set(key, value)
        if ret:
            return True
        else:
            return False

    def delete_key(self, key):
        ret = self.conn.delete(key)
        if ret:
            return True
        else:
            return False


if __name__ == "__main__":
    r = RedisApi()
    #key_name = 'cannon_voice_call_status'
    #print(r.check_exist_of_key(key_name))

    key = 'cannon_task_manager_lock'
    import socket
    value = socket.gethostbyname(socket.getfqdn(socket.gethostname()))
    #value = '192.168.60.73'
    #r.set_key_with_ttl(key, value, 60)

    print(r.get_value_of_string(key))
    print(type(r.get_value_of_string(key)))

    #r.delete_key(key)
