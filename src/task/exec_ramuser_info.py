#!/usr/bin/env python3
# coding:utf-8
import datetime
import json

# 项目的lib
from src.lib.cloud import aliyun_api
from src.lib import db_mysql
mysql_conn = db_mysql.MyPymysqlPool()


class GetRamInfo:
    username = ''

    def __init__(self):  # 获取ram中所有用户名
        self.status = False
        self.data_formart = 'json'

    def get_username_list(self):
        marker = ''
        response = aliyun_api.AliyunApi().list_users(self.data_formart, marker)
        result = json.loads(response, encoding='utf-8')

        self.username_list = []
        truncated = result['IsTruncated']

        for i in result['Users']['User']:
            username = i['UserName']
            self.username_list.append(username)

        while truncated:
            marker = result['Marker']
            response = aliyun_api.AliyunApi().list_users(self.data_formart, marker)

            # response = client.do_action_with_exception(request)
            result = json.loads(response, encoding='utf-8')
            truncated = result['IsTruncated']

            for i in result['Users']['User']:
                username = i['UserName']
                self.username_list.append(username)
        return self.username_list
        # for self.username in self.username_list:
        #     self.become_data()

    def get_last_login_time(self):
        username = self.username

        response = aliyun_api.AliyunApi().get_user_lastlogintime(self.data_formart, username)
        result = json.loads(response, encoding='utf-8')

        try:
            lastlogin_time_str = str(result['User']['LastLoginDate'])
            self.lastlogin_time = datetime.datetime.strftime((datetime.datetime.strptime(lastlogin_time_str, "%Y-%m-%dT%H:%M:%SZ") + datetime.timedelta(hours=8)) ,'%Y-%m-%d %H:%M:%S')
            return self.lastlogin_time
        except:
            self.lastlogin_time = 'NULL'
            pass

    def get_login_profile(self):  # 获取用户是否可以登陆控制台
        username = self.username
        try:
            response = aliyun_api.AliyunApi().get_user_loginprofile(self.data_formart, username)
            if response is not False:
                login_profile = json.loads(response, encoding='utf-8')
                i = login_profile['LoginProfile']
                if not i:
                    self.login_enable = "否"
                else:
                    self.login_enable = "是"
            else:
                self.login_enable = "否"
        except Exception as e:
            self.login_enable = "否"
            pass
        return self.login_enable

    def get_policies(self):  # 获取用户所拥有的权限
        username = self.username

        # 获取权限所有内容
        response = aliyun_api.AliyunApi().get_user_policies(self.data_formart, username)
        policies = json.loads(response, encoding='utf-8')

        # 获取权限信息
        police = policies['Policies']['Policy']
        if police:
            police_list = []
            for i in police:
                policyname = i['PolicyName']
                police_list.append(policyname)
                self.polices_json = json.dumps(police_list,sort_keys=True,separators=(',',':'))
        else:
            self.polices_json = 'NULL'
        return self.polices_json

    def get_ak(self):  # 获取用户所有的ak信息
        self.ak_id = ''
        self.ak_info_list = []
        username = self.username
        response = aliyun_api.AliyunApi().get_user_ak(self.data_formart, username)
        result = json.loads(response, encoding='utf-8')
        accesskey_info = result['AccessKeys']['AccessKey']

        # 获取用户ak信息

        if accesskey_info:  # 如果有ak的话，则accesskey_info非空
            self.akinfo_list_json = []
            for i in accesskey_info:
                self.ak_info = dict()
                self.ak_id = i['AccessKeyId']
                self.ak_status = i['Status']
                if self.ak_id and self.ak_status == 'Active':
                    self.last_useak_time()
                self.ak_info["ak_id"] = self.ak_id
                self.ak_info["ak_status"] = self.ak_status
                self.ak_info["last_use_time"] = self.real_lastuseak_time
                self.ak_info_list.append(self.ak_info)
            # self.ak_info = self.ak_info + '\n' + self.ak_id + ':' + self.ak_status + ':' + self.real_lastuseak_time
            self.akinfo_list_json = json.dumps(self.ak_info_list, sort_keys=True, separators=(',', ':'))
        else:
            self.akinfo_list_json = 'NULL'
        return self.akinfo_list_json

    def last_useak_time(self):
        eventrw = 'All'
        ak_id = self.ak_id
        response = aliyun_api.AliyunApi().get_last_useak_time(self.data_formart, eventrw, ak_id)
        result = json.loads(response, encoding='utf-8')

        try:
            last_event_time = result['Events'][0]['eventTime']
            self.real_lastuseak_time = datetime.datetime.strftime(
                (datetime.datetime.strptime(last_event_time, "%Y-%m-%dT%H:%M:%SZ") + datetime.timedelta(hours=8)),
                '%Y-%m-%d %H:%M:%S')
        except:
            self.real_lastuseak_time = 'NULL'
        return self.real_lastuseak_time

    def become_data(self, task_id=False):
        time = datetime.datetime.now()
        print(time)
        username_list = self.get_username_list()
        for self.username in username_list:
            self.get_login_profile()
            self.get_last_login_time()
            self.get_policies()
            self.get_ak()

            # 判断是否是新增的用户名，如果是插入一条新数据，不是则从表中读取数据
            sql = "select count(*) from %s where username = '%s'" % ('ram_user_info', self.username)
            result = mysql_conn.select(sql)
            username_count = result[0][0]

            if username_count == 0:
                sql = "insert into %s(username, login_enable, last_login_time, policies, access_key, update_time) values('%s', '%s', '%s', '%s', '%s', '%s')" % \
                      ('ram_user_info', self.username, self.login_enable, self.lastlogin_time, self.polices_json, self.akinfo_list_json, time)
                mysql_conn.insert(sql)
                mysql_conn.end()
            else:
                #sql = "select login_enable, CAST(last_login_time AS CHAR) AS last_login_time, policies, access_key from %s where username = '%s'" % ('ram_user_info', self.username)
                sql = "select login_enable, last_login_time, policies, access_key, update_time from %s where username = '%s'" \
                      % ('ram_user_info', self.username)
                result = mysql_conn.select(sql)
                login_enable_old = result[0][0]
                last_login_time_old = result[0][1]
                if last_login_time_old == None:
                    last_login_time_old = 'NULL'
                elif last_login_time_old == '0000-00-00 00:00:00':
                    last_login_time_old = 'NULL'
                else:
                    last_login_time_old = result[0][1].strftime("%Y-%m-%d %H:%M:%S")
                policies_old = result[0][2]
                access_key_old = result[0][3]
                try:
                    time_old = result[0][4].strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_old = None

                if self.login_enable != login_enable_old or self.lastlogin_time != last_login_time_old or self.polices_json != policies_old or self.akinfo_list_json != access_key_old or time != time_old:
                    sql = "update %s set login_enable = '%s',last_login_time = '%s', policies = '%s', " \
                          "access_key = '%s', update_time = '%s' where username = '%s';" % ('ram_user_info', self.login_enable, self.lastlogin_time, self.polices_json, self.akinfo_list_json, time, self.username)
                    mysql_conn.update(sql)
            mysql_conn.end()

            # delete已经删除的用户在数据库的row
            sql_cmd = "select username from %s" % ('ram_user_info')
            result = mysql_conn.select(sql_cmd)
            sql_username_list = []
            for s in result:
                sql_username_list.append(s[0])
            del_list = [y for y in sql_username_list if y not in self.username_list]
            for del_username in del_list:
                sql = "delete from %s where username = '%s'" % ('ram_user_info', del_username)
                mysql_conn.delete(sql)
            mysql_conn.end()
        self.status = True
        return self.status


if __name__ == "__main__":
    X = GetRamInfo()
    X.become_data()
