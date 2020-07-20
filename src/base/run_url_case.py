#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author by 闪马, @20200407

""" url验证集合，基于Django urls.py中所有url的结果验证
    对每个url发起get或post请求验证，并根据返回的json内容，确认http请求是否成功
    用于开发或部署完的结果验证
"""

import requests
from django.urls.resolvers import URLResolver, URLPattern
try:
    import simplejson as json
except ImportError:
    import json


def get_all_url(pattern, urlconf_name):
    exec('import %s' %urlconf_name)
    urlmod = eval(urlconf_name)
    urlpatterns = urlmod.urlpatterns
    url_all = []

    for urlpattern in urlpatterns:
        url_path = {}
        try:
            path = str(urlpattern).split('\'')[1].replace('^', '').replace('$', '')
        except:
            continue
        if path.startswith('api'):
            local_domain = 'http://127.0.0.1:8081/'
            url = local_domain + path
            if path == 'api/monitor/switch':
                parm = '?ak=1d42ee7b99a7d92bdbdaccc3edc30a9f&privateIp=192.168.104.191&action=0'
                url = local_domain + path + parm
            if path == 'api/duty_poll':
                continue

            url_path['path'] = path
            url_path['url'] = url
            url_all.append(url_path)
        '''
        newpattern = pattern+urlpattern.regex.pattern[1:]
        if hasattr(urlpattern, 'urlconf_name'): # 存在urls子模块，递归该方法
            url_all.extend(urlAll(newpattern, urlpattern.urlconf_name))
        else:
            url_all.append(newpattern)
        '''
    print(url_all)
    return url_all


def run_url_case():
    url_all = get_all_url('^', 'cannon.urls')
    for url_dict in url_all:
        success = False
        data = {}
        message = ''
        url = url_dict['url']
        path = url_dict['path']
        if path == 'api/voice-call':
            values = {'appname': 'sre', 'content': '告警测试', 'number': '15356140835', 'token': 'xaYXNsTg2aiVhNIyC'}
            try:
                r = requests.post(url, data=json.dumps(values))
                success = json.loads(r.text)['success']
                message = json.loads(r.text)['message']
            except Exception:
                message = 'except'
            else:
                if success:
                    data = json.loads(r.text)['data']
            print('[success: %s] url: %s, message: %s, content: %s' % (success, url, message, data))
        else:
            try:
                r = requests.get(url)
                success = json.loads(r.text)['success']
                message = json.loads(r.text)['message']
            except:
                message = 'except'
            else:
                if success:
                    try:
                        data = json.loads(r.text)['data'][0]
                    except:
                        data = {}
            print('[success: %s] url: %s, message: %s, content: %s' % (success, url, message, data))
    return True


if __name__ == "__main__":
    from src.lib import django_api
    django_api.DjangoApi().os_environ_update()
    run_url_case()
