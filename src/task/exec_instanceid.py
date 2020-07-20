#!/usr/bin/env python3
# coding:utf-8
from datetime import datetime, timedelta
import math
import json

#项目的lib
from src.lib.cloud import aliyun_api


def get_intance_info(task_id=False):
    status = False
    status_slb = get_slb_instance_info()
    status_ecs = get_ecs_instance_info()
    if status_slb is True and status_ecs is True:
        status = True
    return status


def get_slb_instance_id():
    # 获取slb总数
    format = 'json'
    page = 1
    limit = 20

    response = aliyun_api.AliyunApi().get_slbinstance_id(format, page, limit)
    result = json.loads(response, encoding='utf-8')
    total_count = result['TotalCount']  # slb总数

    #查询所有slb的instance_id
    page = 1
    limit = 20
    total_page = math.ceil(total_count/limit) # 获取告警事件的总条数
    instance_id_list = []
    while page <= total_page:
        response = aliyun_api.AliyunApi().get_slbinstance_id(format, page, limit)
        result = json.loads(response, encoding='utf-8')
        for instance in result['LoadBalancers']['LoadBalancer']:
            instance_id = instance['LoadBalancerId']
            instance_id_list.append(instance_id)
        page += 1
    return instance_id_list


def get_slb_instance_info():
    status = False
    try:
        instance_id_list = get_slb_instance_id()
    except Exception as e:
        print('获取slb的instance_id失败：%s' % e)
        return status
    for instance_id in instance_id_list:
        product_type = 'slb'
        public_ip = ''
        private_ip = ''
        try:
            response = aliyun_api.AliyunApi().get_slbinstance_info(format, instance_id)
            result = json.loads(response, encoding='utf-8')
        except Exception as e:
            print('阿里云接口调用失败：%s' % e)
            return status
        try:
            instance_name = result['LoadBalancerName']
        except:
            instance_name = None
        address_type = result['AddressType']
        if address_type == 'intranet':
            private_ip = result['Address']
        if address_type == 'internet':
            public_ip = result['Address']
        create_time = datetime.fromtimestamp(float(result['CreateTimeStamp']/1000))
        end_time = datetime.fromtimestamp(float(result['EndTimeStamp']/1000))
        region_id = result['MasterZoneId']
        pay_type = result['PayType']
        try:
            status = update_sql(instance_id, instance_name, product_type, public_ip, private_ip, create_time, end_time, region_id, pay_type)
        except Exception as e:
            print('更新数据表失败：%s' % e)
            return status
    status = True
    return status

def update_sql(instance_id, instance_name, product_type, public_ip, private_ip, create_time, end_time, region_id, pay_type):
    status = False
    from src.lib import db_mysql
    mysql_conn = db_mysql.MyPymysqlPool()
    sql = "select count(*) from %s where instance_id = '%s'" % ('global_instance', instance_id)
    sql_result = mysql_conn.select(sql)
    instance_count = sql_result[0][0]
    if instance_count == 0:
        try:
            sql = "insert into %s(instance_id, instance_name, product_type, public_ip, private_ip, create_time, end_time, " \
                  "region_id, pay_type) values('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
                  ('global_instance', instance_id, instance_name, product_type, public_ip, private_ip, create_time, end_time, region_id, pay_type)
            mysql_conn.insert(sql)
        except Exception as e:
            print('数据表插入数据失败：%s' % e)
            return status
    elif instance_count == 1:
        try:
            sql = "select instance_name, product_type, public_ip, private_ip, end_time from %s where instance_id = '%s'" \
                  %('global_instance', instance_id)
            sql_result = mysql_conn.select(sql)
        except Exception as e:
            print('搜索数据表失败：%s' % e)
            return status
        old_instance_name = sql_result[0][0]
        old_product_type = sql_result[0][1]
        old_public_ip = sql_result[0][2]
        old_private_ip = sql_result[0][3]
        old_end_time = sql_result[0][4]
        if old_instance_name != instance_name or old_public_ip != public_ip or old_private_ip != private_ip or\
                old_end_time != end_time or old_product_type != product_type:
            try:
                sql = "update %s set instance_name = '%s', product_type = '%s', public_ip = '%s', private_ip = '%s', " \
                      "end_time = '%s' where instance_id = '%s';" % ('global_instance', instance_name, product_type,
                                                                     public_ip, private_ip, end_time, instance_id)
                mysql_conn.update(sql)
            except Exception as e:
                print('更新数据表失败：%s' % e)
                return status
    else:
        print("event_id 大于1，请查询数据库数据准确性")
        return status
    mysql_conn.dispose()
    status = True
    return status

def get_ecs_total_count():
    status = False
    # 获取ecs总数
    format = 'json'
    page = 1
    limit = 20
    try:
        response = aliyun_api.AliyunApi().get_ecsinstances_info(format, page, limit)
        result = json.loads(response, encoding='utf-8')
    except Exception as e:
        print('阿里云接口调用失败：%s' % e)
        return status
    total_count = result['TotalCount']  # ecs总数
    return total_count


def get_ecs_instance_info():
    status = False
    try:
        total_count = get_ecs_total_count()
    except Exception as e:
        print('获取ecs总数失败：%s' % e)
        return status
    if total_count is False:
        return status
    # 查询所有slb的instance_id
    page = 1
    limit = 20
    total_page = math.ceil(total_count / limit)  # 获取总页数
    while page <= total_page:
        response = aliyun_api.AliyunApi().get_ecsinstances_info(format, page, limit)
        result = json.loads(response, encoding='utf-8')

        instance = result['Instances']['Instance']
        for ecs in instance:
            product_type = 'ecs'
            instance_id = ecs['InstanceId']
            instance_name = ecs['InstanceName']
            try:
                public_ip = ecs['PublicIpAddress']['IpAddress'][0]
            except:
                public_ip = ''
            try:
                private_ip = ecs['NetworkInterfaces']['NetworkInterface'][0]['PrimaryIpAddress']
            except:
                private_ip = ecs['InnerIpAddress']['IpAddress'][0]
            creationtime = ecs['CreationTime']
            create_time = datetime.strptime(str(datetime.strftime(
                (datetime.strptime(creationtime, "%Y-%m-%dT%H:%MZ") + timedelta(hours=8)),
                '%Y-%m-%d %H:%M:%S')), '%Y-%m-%d %H:%M:%S')
            expiredtime = ecs['ExpiredTime']
            end_time = datetime.strptime(expiredtime, "%Y-%m-%dT%H:%MZ") + timedelta(hours=8)
            region_id = ecs['ZoneId']
            pay_type = ecs['InstanceChargeType']
            try:
                update_sql(instance_id, instance_name, product_type, public_ip, private_ip, create_time, end_time, region_id, pay_type)
            except Exception as e:
                print('更新数据表失败：%s' % e)
                return status
        page += 1
    status = True
    return status


def del_old_ecs():
    status = False
    from src.lib import db_mysql
    mysql_conn = db_mysql.MyPymysqlPool()
    try:
        sql = "select instance_id from {} where product_type = 'ecs';".format('global_instance')
        sql_result = mysql_conn.select(sql)
    except Exception as e:
        print('sql 执行失败：%s' % e)
        return status

    ecs_intance_list = list()
    for i in sql_result:
        intance_id = i[0]
        ecs_intance_list.append(intance_id)

    for ecs_intanceid in ecs_intance_list:
        # 获取ecs总数
        format = 'json'
        page = 1
        limit = 20

        response = aliyun_api.AliyunApi().get_ecsinstance_info(format, page, limit, ecs_intanceid)
        result = json.loads(response, encoding='utf-8')
        instance_count = result['TotalCount']  # ecs总数

        if instance_count == 0:  # 如果在阿里云中查不到相关instance的ecs，在表中删除该instance响应数据
            try:
                del_sql = "delete from %s where instance_id = '%s'" % ('global_instance', ecs_intanceid)
                mysql_conn.delete(del_sql)
            except Exception as e:
                print('sql 执行失败：%s' % e)
                return status
    mysql_conn.dispose()
    status = True
    return status


def del_old_slb():
    status = False
    from src.lib import db_mysql
    mysql_conn = db_mysql.MyPymysqlPool()
    try:
        sql = "select instance_id from {} where product_type = 'slb';".format('global_instance')
        sql_result = mysql_conn.select(sql)
    except Exception as e:
        print('sql 执行失败：%s' % e)
        return status
    slb_intance_list = list()
    for i in sql_result:
        intance_id = i[0]
        slb_intance_list.append(intance_id)

    for slb_intanceid in slb_intance_list:
        # 获取slb个数
        format = 'json'
        response = aliyun_api.AliyunApi().get_slbinstance_count(format, slb_intanceid)
        result = json.loads(response, encoding='utf-8')
        instance_count = result['TotalCount']  # ecs总数

        if instance_count == 0:  # 如果在阿里云中查不到相关instance的ecs，在表中删除该instance响应数据
            try:
                del_sql = "delete from %s where instance_id = '%s'" % ('global_instance', slb_intanceid)
                mysql_conn.delete(del_sql)
            except Exception as e:
                print('sql 执行失败：%s' % e)
    mysql_conn.dispose()
    status = True
    return status


if __name__ == "__main__":
    get_intance_info()
