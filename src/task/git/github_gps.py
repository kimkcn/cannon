#!/usr/bin/env python 
# coding:utf-8
import os
import configparser
import datetime
import time
from src.task.git import git
from src.lib import db_mysql
mysql_conn = db_mysql.MyPymysqlPoolDict()

# 从配置文件里读取github的用户名密码
file_path = os.path.join(os.path.dirname(__file__), "../../../conf/key.conf")
cf = configparser.ConfigParser()
cf.read(file_path)
section = 'github'
user_name = cf.get(section, 'user')
password = cf.get(section, 'password')
api_token = cf.get(section, 'token')


def get_ak_list():  # 获取ak列表，依赖于ram的信息采集任务
    sql = "select access_key from {}".format('ram_user_info')
    result = mysql_conn.select(sql)
    ak_list = list()
    for i in result:
        info = i['access_key']
        if info != 'NULL':
            info_list = eval(info)
            for ak_info in info_list:
                if ak_info['ak_status'] == 'Active':
                    ak_list.append(ak_info['ak_id'])
    print('成功获取可用ak列表 %s' % ak_list)
    return ak_list


def exec_github(task_id=False):
    git_host = 'github.com'
    git_api_host = 'api.github.com'
    status = exec_search(git_host, git_api_host)
    return status


def exec_search(git_host, git_api_host):  # 通过ak_id调用git.py搜索ak的匹配结果
    status = False
    git_host = git_host
    git_api_host = git_api_host
    ak_list = get_ak_list()
    now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    from src.lib import db_mysql
    mysql_conn = db_mysql.MyPymysqlPool()
    for ak in ak_list:
        attempts = 0
        leak_list = list()
        while attempts < 3:
            try:
                leak_list = git.GithubCrawl(git_host, git_api_host, user_name, password, ak, api_token).login()
                break
            except Exception as e:
                attempts += 1
                print("获取失败: %s," % e, "重试三次")
                time.sleep(10)
                if attempts == 3:
                    break
        if len(leak_list) > 0:
            print('查询到有%s的匹配记录' % ak)
            project_url_list = list()
            for i in leak_list:
                project_url = i['project_url']
                project_url_list.append(project_url)
                file_path_list = i['file_path_list']
                match_num = i['match_num']
                user = i['user']
                start_time = now_time
                sql = "select count(id) from %s where ak = '%s' and project_url = '%s' and match_num != 0;" % \
                      ('safe_ak_leak', ak, i['project_url'])
                old_count = mysql_conn.select(sql)[0][0]

                if old_count == 0:
                    try:
                        sql = 'insert into %s(ak, project_url, file_path_list, match_num, user, start_time) ' \
                              'values("%s", "%s", "%s", "%s", "%s", "%s");' % \
                              ("safe_ak_leak", ak, project_url, file_path_list, match_num, user, start_time)
                        mysql_conn.insert(sql)
                    except Exception as e:
                        print('sql 执行失败：%s' % e)
                if old_count > 0:
                    try:
                        sql = 'update %s set ak = "%s",  project_url = "%s", file_path_list = "%s", match_num = "%s", ' \
                              'user = "%s", update_time = "%s";' % \
                              ('safe_ak_leak', ak, project_url, file_path_list, match_num, user, start_time)
                        mysql_conn.update(sql)
                    except Exception as e:
                        print('sql 执行失败：%s' % e)

            # 删除已经没有泄漏的sql记录
            sql = "select project_url from %s where ak = '%s' and  match_num != 0;" % ('safe_ak_leak', ak)
            result = mysql_conn.select(sql)
            sql_project_url_list = []
            for s in result:
                sql_project_url_list.append(s[0])
            del_list = [y for y in sql_project_url_list if y not in project_url_list]
            for del_project_url in del_list:
                sql = "delete from %s where ak = '%s' and project_url = '%s'" % ('safe_ak_leak', ak, del_project_url)
                mysql_conn.delete(sql)

        if len(leak_list) == 0:
            print('本次查询没有%s的匹配记录' % ak)
            sql = "select count(id) from %s where ak = '%s' and match_num != 0;" % ('safe_ak_leak', ak)
            old_count = mysql_conn.select(sql)[0][0]
            if old_count > 0:
                try:
                    sql = "update %s set match_num = 0 where ak = '%s';" % ('safe_ak_leak', ak)
                    mysql_conn.update(sql)
                except Exception as e:
                    print('sql 执行失败：%s' % e)

    # 删除不在ak列表的原始数据
    try:  # 搜索ak_leak原始数据表的ak信息，组成列表
        sql = "select ak from {} where match_num > 0;".format('safe_ak_leak')
        result = mysql_conn.select(sql)
    except Exception as e:
        print('sql 执行失败：%s' % e)
        return status
    else:
        sql_ak_list = list()
        if result is not False and len(result) > 0:
            for m in result:
                sql_ak = m[0]
                sql_ak_list.append(sql_ak)
    del_list = [ak for ak in sql_ak_list if ak not in ak_list]  # 需要在ak泄漏数据表中删除的ak列表

    if len(del_list) > 0:
        print('%s中ak已经不存在，即将删除ak泄漏表中相关数据' % del_list)
        for del_ak in del_list:
            try:
                sql = "delete from %s where ak = '%s' and match_num > 0" % ('safe_ak_leak', del_ak)
                mysql_conn.delete(sql)
            except Exception as e:
                print('sql 执行失败 删除老数据失败：%s' % e)
                return status
    status = True
    mysql_conn.dispose()
    return status


if __name__ == "__main__":
    exec_github()



