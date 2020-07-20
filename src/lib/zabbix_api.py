#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from urllib.error import URLError
import urllib.request,urllib.error,urllib.parse
import requests
import socket
import sys, os
try:
    import simplejson as json
except ImportError:
    import json
sys.path.append("../../")
from conf import alert_conf
import configparser


def get_ip(domain):
    myaddr = socket.getaddrinfo(domain, 'http')
    ip = myaddr[0][4][0]
    return ip

class ZabbixApi:
    def __init__(self):
        file_path = os.path.join(os.path.dirname(__file__), "../../conf/key.conf")
        cf = configparser.ConfigParser()
        cf.read(file_path)
        ak_section = "zabbix"
        self.header = {"Content-Type":"application/json-rpc"}
        self.user = cf.get(ak_section, 'zabbix_cannon_user')
        self.passwd = cf.get(ak_section, 'zabbix_cannon_passwd')
        self.min_severity = alert_conf.zabbix_min_severity    # 最小采集级别
        self.table_name = alert_conf.table_name
        self.zabbix_api_url = cf.get(ak_section, 'zabbix_api_url')
        ip = get_ip(self.zabbix_api_url)
        if ip == '114.55.199.230':
            self.url = "https://zabbix.ops.yangege.cn/api_jsonrpc.php"
        elif ip == '192.168.10.88':
            self.url = "http://zabbix.ops.yangege.cn/api_jsonrpc.php"


    def user_login(self):
        data = json.dumps({
                           "jsonrpc": "2.0",
                           "method": "user.login",
                           "params": {
                                      "user": self.user,
                                      "password": self.passwd
                                      },
                           "id": 1,
                           })
        try:
            request = requests.post(url=self.url, headers=self.header, data=data)
        except URLError as e:
            print("Auth Failed, please Check your name and password:", e)
        else:
            response = json.loads(request.text)
            request.close()
            self.authID = response['result']
            return self.authID

    def get_trigger(self):
        data = json.dumps({
                        "jsonrpc": "2.0",
                        "method": "trigger.get",
                        "params": {
                            "output": "extend",
                            "sortfield": "lastchange",
                            "sortorder": "DESC",
                            "active": 1,   # 已启用触发器
                            "only_true": 1,   # 最近处于故障状态
                            "filter": {
                                "value": 1,  # 过滤问题触发器
                            },
                            "min_severity": self.min_severity,   # 最小报警级别
                            "monitored": 1,   # 已启用监控项
                            "expandDescription": 1,
                            "skipDependent": 1,   # 忽略所依赖的触发器告警
                            "selectHosts": ['host'],   # 返回触发器所属的主机
                            "selectGroups": ['name']   # 返回触发器所属的主机组
                        },
                        "auth": self.user_login(),
                        "id": 1
                    })
        try:
            request = requests.post(url=self.url, headers=self.header, data=data)
        except URLError as e:
            print("Error as ", e)
            response = {}
        except:
            response = {}
        else:
            response = json.loads(request.text)
            request.close()
        return response

    def get_hostid_with_hostip(self, hostip):
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "hostinterface.get",
            "params": {
                "output": "extend",
                "filter": {"ip": hostip}
            },
            "auth": self.user_login(),
            "id": 1
        })
        try:
            request = requests.post(url=self.url, headers=self.header, data=data)
        except URLError as e:
            if hasattr(e, 'reason'):
                print('We failed to reach a server.')
                print('Reason: ', e.reason)
            elif hasattr(e, 'code'):
                print('The server could not fulfill the request.')
                print('Error code: ', e.code)
        except:
            print("except")
        else:
            response = json.loads(request.text)
            request.close()

            if not len(response['result']):
                print("\033[041m hostid \033[0m is not exist")
                return False
            for hostid in response['result']:
                return hostid['hostid']

    def get_hostname_with_hostip(self, hostip):
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output": "extend",
                "filter": {"ip": hostip}
            },
            "auth": self.user_login(),
            "id": 1
        })
        try:
            request = requests.post(url=self.url, headers=self.header, data=data)
        except URLError as e:
            if hasattr(e, 'reason'):
                print('We failed to reach a server.')
                print('Reason: ', e.reason)
                return False
            elif hasattr(e, 'code'):
                print('The server could not fulfill the request.')
                print('Error code: ', e.code)
                return False
        else:
            response = json.loads(request.text)
            request.close()

            if not len(response['result']):
                print("hostId is not exist")
                return False

            for host in response['result']:
                host_name = host['name']

            return host_name

    def host_disable(self,hostip):
        ret = False
        hostid = self.get_hostid_with_hostip(hostip)
        if not hostid:
            return ret

        data=json.dumps({
                "jsonrpc": "2.0",
                "method": "host.update",
                "params": {
                "hostid": hostid,
                "status": 1
                },
                "auth": self.user_login(),
                "id": 1
                })
        try:
            request = requests.post(url=self.url, headers=self.header, data=data)
        except URLError as e:
            print("Error as ", e)
        except:
            print("Except")
        else:
            request.close()
            ret = True
        return ret

    def host_enable(self,hostip):
        ret = False
        hostid = self.get_hostid_with_hostip(hostip)
        if not hostid:
            return ret

        data=json.dumps({
            "jsonrpc": "2.0",
            "method": "host.update",
            "params": {
            "hostid": hostid,
            "status": 0
            },
            "auth": self.user_login(),
            "id": 1
            })
        try:
            request = requests.post(url=self.url, headers=self.header, data=data)
        except URLError as e:
            print("Error as ", e)
        except:
            print("Except")
        else:
            request.close()
            ret = True
        return ret

    def get_item(self,triggerid):
        ret = False
        #hostid = self.get_hostid_with_hostip(hostip)
        #print(hostid)
        #if not hostid:
        #    return ret
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "output": "extend",
                "triggerids": triggerid,
                "sortfield": "name",
                "search": {
                    "key_": "icmppingsec"
                }
            },
            "auth": self.user_login(),
            "id": 1
        })
        try:
            request = requests.post(url=self.url, headers=self.header, data=data)
            #print('123')
        except URLError as e:
            print("Error as ", e)
            response = {}
        except:
            print("Except")
            response = {}
        else:
            response = json.loads(request.text)
            request.close()
        return response

    def get_item_with_hostip(self,hostip):
        ret = False
        hostid = self.get_hostid_with_hostip(hostip)
        print('hostid',hostid)
        if not hostid:
            return ret
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "output": ["itemid","hostid","name","templateid"],
                "hostids": hostid,
                #"templateids": templateid,
                "sortfield": "name",
                #"templated": "true",
                "search": {
                    "key_": "icmppingsec"
                }
            },
            "auth": self.user_login(),
            "id": 1
        })
        try:
            request = requests.post(url=self.url, headers=self.header, data=data)
            #print('123')
        except URLError as e:
            print("Error as ", e)
            response = {}
        except:
            print("Except")
            response = {}
        else:
            response = json.loads(request.text)
            request.close()
        return response

    def get_problem(self,eventid):
        ret = False
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "problem.get",
            "params": {
                "output": ['eventid',
                            'clock',
                            'r_clock',
                            'name'],
                #"selectAcknowledges": "extend",
                #"selectTags": "extend",
                "eventids": eventid,
                "recent": "true",
                "sortfield": ["eventid"],
                "sortorder": "DESC",
                #"time_from": start,
                #"time_till": stop
            },
            "auth": self.user_login(),
            "id": 1
        })
        try:
            request = requests.post(url=self.url, headers=self.header, data=data)
            #print('123')
        except URLError as e:
            print("Error as ", e)
            response = {}
        except:
            print("Except")
            response = {}
        else:
            response = json.loads(request.text)
            request.close()
        return response

    def get_event(self,triggerid,start,stop):
        ret = False
        #hostid = self.get_hostid_with_hostip(hostip)
        #print(hostid)
        #if not hostid:
            #return ret
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "event.get",
            "params": {
                "output": "extend",
                "selectAcknowledges": "extend",
                "selectTags": "extend",
                #"hostids":hostid,
                "objectids": triggerid,
                "sortfield": ["clock"],
                "sortorder": "DESC",
                "time_from": start,
                "time_till": stop
            },
            "auth": self.user_login(),
            "id": 1
        })
        try:
            request = requests.post(url=self.url, headers=self.header, data=data)
        except URLError as e:
            print("Error as ", e)
            response = {}
        except:
            print("Except")
            response = {}
        else:
            response = json.loads(request.text)
            request.close()
        return response

    def get_template(self,template_name):
        ret = False
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "template.get",
            "params": {
                "output": "extend",
                "filter": {
                    "host": [
                        template_name
                    ]
                }
            },
            "auth": self.user_login(),
            "id": 1
        })
        try:
            request = requests.post(url=self.url, headers=self.header, data=data)
        except URLError as e:
            print("Error as ", e)
            response = {}
        except:
            print("Except")
            response = {}
        else:
            response = json.loads(request.text)
            request.close()
        return response

    def get_history(self,itemid,start,stop):
        #print('-------get history is start--------')
        ret = False
        limit = stop - start
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "history.get",
            "params": {
                "output": "extend",
                "history":0,
                "itemids": itemid,
                "sortfield": "clock",
                "sortorder": "DESC",
                "time_from": start,
                "time_till":stop,
                "limit": limit,
            },
            "auth": self.user_login(),
            "id": 1
        })
        #request = urllib3.Request(url=self.url, headers=self.header, data=data,method='POST')
        #result = urllib3.urlopen(request)

        try:
            request = urllib.request.Request(url=self.url, headers=self.header, data=data.encode('utf-8'))
            result = urllib.request.urlopen(request)
            #print('get history api is sucess')
        except URLError as e:
            print("Error as ", e)
            response = {}
        except:
            print("Except")
            response = {}
        else:
            response = json.loads(result.read().decode('utf-8'))
            #print('11111111111',response)
            ret = True
        return response

    def get_pn_trigger(self,hostip):
        ret = False
        hostid = self.get_hostid_with_hostip(hostip)
        if not hostid:
            return ret
        data = json.dumps({
                        "jsonrpc": "2.0",
                        "method": "trigger.get",
                        "params": {
                            "output": [
                                "triggerid",
                                "description",
                                "priority"
                            ],
                            "hostids": hostid,
                            #"templateids": templateid,
                            #"templated":"true",
                            "sortfield": "priority",
                            "sortorder": "DESC"
                        },
                        "auth": self.user_login(),
                        "id": 1
                    })
        try:
            request = requests.post(url=self.url, headers=self.header, data=data)
        except URLError as e:
            print("Error as ", e)
            response = {}
        except:
            response = {}
        else:
            response = json.loads(request.text)
            request.close()
        return response



if __name__ == "__main__":
    z = ZabbixApi()
    #z.get_trigger()
    hostip='192.168.104.191'
    result = z.host_disable(hostip)
    print(result)
