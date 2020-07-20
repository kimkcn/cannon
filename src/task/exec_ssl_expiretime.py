#!/usr/bin/env python3
# coding:utf-8
# 引入数据处理，请求，nmap等模块
import re
import nmap
import datetime
import subprocess as sp
import threading
# 项目的lib
from src.lib.cloud import aliyun_api
from src.lib import db_mysql

# 加载配置文件,读取表明等
import os
import configparser

try:
    import simplejson as json
except ImportError:
    import json


def get_domain_list():  # 获取域名列表
    # 获取一级域名列表
    format = 'json'
    page = 1
    limit = 500
    response = aliyun_api.AliyunApi().get_domain_list(format, page, limit)
    result = json.loads(response, encoding='utf-8')
    domain_list = list()
    for i in result['Data']['Domain']:
        domain = i['DomainName'] # 拿到全域名
        domain_list.append(domain)
    return domain_list


def get_domain_dict():  # 获取全域名和对应的domain的字典
    domain_list = get_domain_list()
    domain_name_list = list()
    domain_name_dict = dict()
    # 每个一级域名一个循环
    for domain in domain_list:
        format = 'json'
        page = 1
        limit = 500
        describe_name_response = aliyun_api.AliyunApi().get_dns_domain(format, page, limit, domain)
        describe_name_result = json.loads(describe_name_response, encoding='utf-8')
        for n in describe_name_result['DomainRecords']['Record']:
            rr = n['RR']
            # 去除@，*，_等特殊域名
            matched = re.match(r'@|_|\*', rr, re.M | re.I)
            if matched:
                continue
            rrr = rr
            domain = n['DomainName']
            domain_name = rrr+'.'+domain
            domain_name_dict[domain_name] = domain
            domain_name_list.append(domain_name)
    return domain_name_dict


def get_real_name():  # 16个线程耗时35秒左右，8个线程耗时60秒左右； 获取开启443的域名和对应的domain的字典
    domain_name_dict = get_domain_dict()
    real_name_dict = dict()
    domain_name_list = list(domain_name_dict)
    max_threads = threading.Semaphore(value=16)  # 设置最大线程数
    threads = list()
    lock = threading.Lock()
    for domain_name in domain_name_list:
        t = threading.Thread(target=do_nm, args=(domain_name, domain_name_dict[domain_name], real_name_dict, lock, max_threads))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return real_name_dict


def do_nm(domain_name, domain, real_name_dict, lock, max_threads):  # 使用nmap探测端口开启状态
    max_threads.acquire()  # 达到限制最大线程数时上锁
    nm = nmap.PortScanner()
    sss = nm.scan(domain_name, '443', '-sT')
    for m in sss['scan']:
        status = (nm[m]['tcp'][443]['state'])
        if status == 'open':
            if lock.acquire():  # 当写real_name_dict数据时锁住此对象
                real_name_dict[domain_name] = domain
                lock.release()  # 写完后释放锁
        else:
            pass
    max_threads.release()  # 释放锁


def exec_ssl(task_id=False):  # 获取所有开启443端口域名的证书信息，更新数据库
    job_id = 'get_sslexpiretime'
    # 从conf里的table配置文件里读取表名
    file_path = os.path.join(os.path.dirname(__file__), "../../conf/table.conf")
    cf = configparser.ConfigParser()
    cf.read(file_path)
    table_section = 'table_name'  # 读取表的名称
    ssl_table = cf.get(table_section, 'ssl_table')
    
    start_time = str(datetime.datetime.now())
    status = False
    real_name_dict = get_real_name()
    real_domain_list = list(real_name_dict)
    mysql_conn = db_mysql.MyPymysqlPool()
    calculate_data_list = list()
    for domainnames in real_domain_list:
        calculate_data_dict = dict()
        domain = real_name_dict[domainnames]
        try:  # curl命令获取域名详情
            cmd = "curl --connect-timeout 2 -m 2 -lkvs https://{}/ |grep -E '^*'".format(domainnames)
            curl_result = sp.getstatusoutput(cmd)
        except Exception as e:
            print('%s %s' % (e, domainnames))
            continue
        else:  # 获取到域名详情后
            curl_result_str = str(curl_result)
            try:  # 从域名详情内容匹配查找证书的关键信息
                m = re.search(r"start date: (.*?)\\n.*?expire date: (.*?)\\n.*? ", curl_result_str)  # 获取证书开始时间和截止时间信息
                if not m:
                    continue
                gmt_format = '%b %d %H:%M:%S %Y GMT'
                expire_time = str(datetime.datetime.strptime(m.group(2), gmt_format))  # 格式转化为str
                cn_result = re.search(r"subject:.*?CN=(\*?.*?\..*?)\\n.\*?", curl_result_str)
                cn = cn_result.group(1)
                match_status = str(domain in cn)
            except Exception as e:
                print('%s' % e)
                continue
            else:
                # 将数据格式化，加入列表，再调用抽象化接口，将数据写入统一表
                if task_id:
                    calculate_data_dict['task_id'] = task_id
                else:
                    calculate_data_dict['job_id'] = job_id
                calculate_data_dict['object_filed'] = 'domain_name'
                calculate_data_dict['object_value'] = domainnames
                metric_dict = dict()
                metric_dict['ssl_expire_time'] = expire_time
                metric_dict['match_status'] = match_status
                calculate_data_dict['metric_dict'] = str(metric_dict)
                calculate_data_list.append(calculate_data_dict)

                try:  # 判断是否是新增的域名，如果是插入一条新数据，不是则从表中读取数据
                    select_sql = "select count(*) from %s where domain_name = '%s'" % (ssl_table, domainnames)
                    sql_result = mysql_conn.select(select_sql)
                except Exception as e:
                    print('%s' % e)
                    continue
                else:
                    if sql_result:
                        domain_data_count = sql_result[0][0]
                    else:
                        continue
                    update_time = datetime.datetime.now()  # 判断执行的时间
                    if domain_data_count == 0:
                        try:
                            insert_sql = "insert into %s(domain, domain_name, expire_date, cn, match_status, update_time) values" \
                                  "('%s', '%s', '%s', '%s', '%s', '%s')" % (ssl_table, domain, domainnames,
                                                                            expire_time, cn, match_status, update_time)
                            mysql_conn.insert(insert_sql)
                        except Exception as e:
                            print(' %s:插入原始数据失败, 失败的域名为 %s' % (e, domainnames))
                            continue
                        else:
                            status = True
                    else:
                        # 从表中读取相关域名的证书有效期信息
                        try:
                            ssl_sql = "select CAST(expire_date AS CHAR) AS expire_date, cn, match_status, update_time from %s" \
                                  " where domain_name = '%s'" % (ssl_table, domainnames)
                            ssl_result = mysql_conn.select(ssl_sql)
                        except Exception as e:
                            print(' %s:查询数据表失败, 失败的域名为 %s' % (e, domainnames))
                            continue
                        else:
                            if not ssl_result:  # 如果搜索不到该域名的数据，那么插入该数据
                                try:
                                    sql = "insert into %s(domain, domain_name, expire_date, cn, match_status, update_time) " \
                                          "values('%s', '%s', '%s', '%s', '%s', '%s)" \
                                          % (ssl_table, domain, domainnames, expire_time, cn, match_status, update_time)
                                    mysql_conn.insert(sql)
                                except Exception as e:
                                    print(' %s:插入数据表失败, 失败的域名为 %s' % (e, domainnames))
                                    continue
                                else:
                                    status = True
                            elif ssl_result:
                                old_expire_time = ssl_result[0][0]  # 将从sql中查询的结果取str类型的过期时间
                                old_cn = ssl_result[0][1]
                                old_match_status = ssl_result[0][2]
                                old_time = ssl_result[0][3]
                                if expire_time != old_expire_time or cn != old_cn or match_status != old_match_status or update_time != old_time:
                                    try:  # 如果原始数据和新数据不一致，则更新数据
                                        sql = "update %s set expire_date = '%s', cn = '%s', match_status = '%s', update_time = '%s' " \
                                              "where domain_name = '%s';" % (ssl_table, expire_time, cn, match_status,
                                                                             update_time, domainnames)
                                        mysql_conn.update(sql)
                                    except Exception as e:
                                        print(' %s:更新数据表失败, 失败的域名为 %s' % (e, domainnames))
                                        continue
                                    else:
                                        status = True
        if status is False:
            mysql_conn.dispose()
            return status
    mysql_conn.dispose()

    from src.judge import data_calculate
    try:  # 将抽象化数据列表传参到抽象化数据处理函数返回结果
        print(calculate_data_list)
        calculate_status = data_calculate.BecomeCalculate(calculate_data_list,).exec_data_list()
    except Exception as e:
        print('%s 抽象化处理数据失败' % e)
    else:
        if calculate_status:
            print('抽象化数据处理成功')
        else:
            status = False
            return status

    mysql_conn = db_mysql.MyPymysqlPool()
    # delete已经删除的域名在数据库的row
    try:
        sql_cmd = "select domain_name from ssl_expire_date"
        result = mysql_conn.select(sql_cmd)
    except Exception as e:
        print(' %s:查询数据表失败, 失败的域名为 %s' % e)
        status = False
        return status
    else:
        if not result:
            print('表中无数据')
        else:
            sql_domainname_list = []
            for s in result:
                sql_domainname_list.append(s[0])
            del_list = [y for y in sql_domainname_list if y not in real_domain_list]
            for del_domainname in del_list:
                try:
                    sql = "delete from %s where domain_name = '%s'" % (ssl_table, del_domainname)
                    mysql_conn.delete(sql)
                except Exception as e:
                    print(' %s:删除数据失败, 失败的域名为 %s' % e)
                    status = False
                    return status
    stop_time = str(datetime.datetime.now())
    message = '开始时间:'+start_time+'  结束时间:'+stop_time
    mysql_conn.dispose()
    return status, message


if __name__ == "__main__":
    exec_ssl()
