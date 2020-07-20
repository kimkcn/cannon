#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author by 闪马, @20200407

""" 前端的登录接口，获取数据库中的用户名密码，返回用户的uuid/token等，供前端渲染
"""

from django.http import HttpResponse
import requests
try:
    import simplejson as json
except ImportError:
    import json
from src.lib import db_mysql
mysql_conn = db_mysql.MyPymysqlPool()
from src.lib import django_api
django_api.DjangoApi().os_environ_update()


def create_random_str():
    import random, string
    src = string.ascii_letters + string.digits
    list_passwds = []
    list_passwd_all = random.sample(src, 21)  # 从字母和数字中随机取5位
    list_passwd_all.extend(random.sample(string.digits, 1))  # 让密码中一定包含数字
    list_passwd_all.extend(random.sample(string.ascii_lowercase, 1))  # 让密码中一定包含小写字母
    list_passwd_all.extend(random.sample(string.ascii_uppercase, 1))  # 让密码中一定包含大写字母
    random.shuffle(list_passwd_all)  # 打乱列表顺序
    str_passwd = ''.join(list_passwd_all)  # 将列表转化为字符串
    if str_passwd not in list_passwds:  # 判断是否生成重复密码
        list_passwds.append(str_passwd)
    print(list_passwds)


def login(request):
    print('login')
    code = 500
    success = False
    data_list = {}
    result_dict = {}
    if request.method == 'POST':  # 当提交表单时
        print(request.body.decode())
        username = json.loads(request.body.decode()).get('username')
        password = json.loads(request.body.decode()).get('password')

        # 验证用户名和密码
        sql = "select username from cannon_user where username = '%s' and pwd = '%s' limit 1" % (username, password)
        print(sql)
        result = mysql_conn.select(sql)
        print(result)
        if result:
            sql = "select cannon_user.id,cannon_user.displayName,auth_user_login_token.token from cannon_user," \
                  "auth_user_login_token where cannon_user.username = auth_user_login_token.username and " \
                  "cannon_user.username = '%s'" % username
            print(sql)
            try:
                tmp_result = mysql_conn.select(sql)
            except:
                print('except')
            else:
                code = 0
                success = True
                if tmp_result:
                    data_list['name'] = tmp_result[0][1]
                    data_list['uuid'] = tmp_result[0][0]
                    data_list['token'] = tmp_result[0][2]
        result_dict['message'] = ''
    else:
        result_dict['message'] = '请求方法错误'

    result_dict['code'] = code
    result_dict['success'] = success
    result_dict['data'] = data_list
    result_json = json.dumps(result_dict, ensure_ascii=False)
    print(result_json)
    return HttpResponse(result_json, content_type="application/json,charset=utf-8")


if __name__ == "__main__":
    url = 'http://127.0.0.1:8081/api/login'
    values = {'username': 'shanma', 'password': 'eA1nohKBbHmuBGEtCioQ'}
    r = requests.post(url, data=json.dumps(values))
    print(json.loads(r.text))
