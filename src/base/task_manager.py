#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
import sys, time, logging, datetime
from src.lib.log import record_info_log, record_debug_log
from src.lib import db_mysql, db_redis
from conf import cannon_conf
import random

# init
executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}
scheduler = BackgroundScheduler(executors=executors)
task_log_file = cannon_conf.task_manage_log
task_error_file = cannon_conf.task_error_log
task_debug_file = cannon_conf.task_debug_log
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename=task_log_file,
                    filemode='a')
key = "cannon_task_manager_lock"
table_name = "task_scheduler"
error_job_dict = {}
max_job_fail_times = 3
loop_interval = 60  # 循环的间隔时间(s)，用于一些事件处理，不影响任务调度
# init end


def exit_scheduler(message):
    print(message)
    record_info_log(task_log_file, message)
    scheduler.shutdown()
    sys.exit()


def get_local_hostname():
    import socket
    local_hostname = socket.gethostname()
    return local_hostname


def query_redis_key_exist(key):
    status = True   # 默认key存在，不做任何处理
    # noinspection PyBroadException
    try:
        result = db_redis.RedisApi().check_exist_of_key(key)
    except Exception as e:
        message = "查询锁失败，原因: %s" % e
        print(message)  # 查询不到，则默认存在，不告警，交给下次查询
        record_info_log(task_log_file, message)
    else:
        if result == 0:  # key不存在，可以写入
            status = False
    return status   # true表示key存在，false表示key不存在


def print_func(message):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    print("%s %s" % (current_time, message))
    return True


def now():
    now_time = datetime.datetime.now() + datetime.timedelta(seconds=random.uniform(5, 30))  # 加随机时间，解决立刻调度会miss的问题
    return now_time


def miss_listener(event):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    message = "%s miss at %s" % (event.job_id, current_time)
    record_info_log(task_log_file, message)


def flush_job_info_to_mysql():  # 定时刷新数据到数据库，避免数据库压力过大
    global job_event_status_dict
    status = False
    mysql_conn = db_mysql.MyPymysqlPoolDict()

    for job_id in list(job_event_status_dict):
        if not job_id:
            continue
        sql = "select id, job_id from %s where job_id = '%s';" % (table_name, job_id)
        try:
            job_id_result = mysql_conn.select(sql)
            print(sql, job_id_result)
        except Exception as e:
            print(e)
        else:
            job_name = job_event_status_dict[job_id]['job_name']
            job_status = job_event_status_dict[job_id]['job_status']
            job_trigger = job_event_status_dict[job_id]['job_trigger']
            last_schedule_starttime = job_event_status_dict[job_id]['last_schedule_starttime']
            last_schedule_endtime = job_event_status_dict[job_id]['last_schedule_endtime']
            last_schedule_status = job_event_status_dict[job_id]['last_schedule_status']

            if job_id_result:
                print('update sql')
                table_id = int(job_id_result[0]['id'])
                update_sql = "update %s set job_status = '%s', job_trigger = '%s', last_schedule_starttime = '%s', " \
                             "last_schedule_endtime = '%s', last_schedule_status = '%s' where id = %s;" % \
                             (table_name, job_status, job_trigger, last_schedule_starttime, last_schedule_endtime,
                              last_schedule_status, table_id)
                try:
                    mysql_conn.update(update_sql)
                except Exception as e:
                    print(e)
                else:
                    status = True
            else:
                insert_sql = "INSERT INTO %s(job_id, job_name, job_status, job_trigger, last_schedule_starttime, " \
                             "last_schedule_endtime, last_schedule_status) " \
                             "VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s');" % \
                             (table_name, job_id, job_name, job_status, job_trigger, last_schedule_starttime,
                              last_schedule_endtime, last_schedule_status)
                try:
                    mysql_conn.insert(insert_sql)
                except Exception as e:
                    print(e)
                else:
                    status = True
    job_event_status_dict = {}
    mysql_conn.dispose()
    return status


def job_listener(event):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    job_id = event.job_id
    job = scheduler.get_job(job_id)
    last_schedule_starttime = str(event.scheduled_run_time).split('+')[0].split('.')[0]
    last_schedule_endtime = current_time
    job_name = job.name
    job_trigger = str(job.trigger).replace("'", "")
    job_status = 'normal'
    pause_job = False

    print('job_id: %s, job.name: %s, job.args: %s, job.trigger: %s, event.exception: %s' % (event.job_id, job.name, job.args, job.trigger, event.exception))

    if event.exception:
        last_schedule_status = 'exception'
        message = "任务执行失败! Job_id: %s, 开始时间：%s，结束时间：%s, 异常: %s, traceback: %s" % (
            event.job_id, last_schedule_starttime, current_time, event.exception, event.traceback)
        record_info_log(task_log_file, message)

        # 单个任务累计失败多次，则停止调度
        if error_job_dict:
            if event.job_id in list(error_job_dict):
                error_job_dict[event.job_id] += 1
                if error_job_dict[event.job_id] >= max_job_fail_times:
                    pause_job = True
            else:
                error_job_dict[event.job_id] = 0
        else:
            error_job_dict[event.job_id] = 0
        print(error_job_dict)

        if pause_job is True:
            scheduler.pause_job('%s' % event.job_id)
            job_status = 'pause'
            message = "Job_id: %s 任务已停止调度，请处理后重启调度任务! " % event.job_id
            print(message)
            record_info_log(task_log_file, message)
    else:   # 执行成功
        ret = event.retval  # 返回状态值
        result = "无返回结果"    # 定义默认返回结果
        try:
            if ret is None:
                status = True
            elif ret in [True, False]:
                status = ret
            elif len(ret) == 2:
                status = ret[0]
                result = ret[1]
            else:
                status = False
        except TypeError:
            status = False
        last_schedule_status = status
        message = "任务执行成功. Job_id: %s, 开始时间：%s，结束时间：%s, 返回状态: %s" % \
                  (event.job_id, last_schedule_starttime, current_time, status)
        record_info_log(task_log_file, message)

    # 任务最后一次执行记录写入数据库
    # 性能优化，任务执行记录缓存于dict中，然后定期写入数据库
    global job_event_status_dict
    job_dict = {'job_name': job_name, 'job_status': job_status, 'job_trigger': job_trigger,
                'last_schedule_starttime': last_schedule_starttime, 'last_schedule_endtime': last_schedule_endtime,
                'last_schedule_status': last_schedule_status}
    job_event_status_dict[job_id] = job_dict


def get_job_config(job_id):
    result = False
    mysql_conn = db_mysql.MyPymysqlPoolDict()

    sql = "select * from task_job_config where job_id = '%s';" % job_id
    try:
        result = mysql_conn.select(sql)
    except Exception as e:
        print('Job_id: %s, get job config Error: %s!' % (job_id, e))

    mysql_conn.dispose()
    return result


def add_job(func=None, job_id=None):
    import re
    status = False

    # 查询job_id对应的配置信息
    result = get_job_config(job_id)

    if result:
        status = result[0]['enable']
        if status not in ['True', 'true']:
            print('job_id: %s, 配置不是启用状态，不参与调度!' % job_id)
            return status
    else:
        print('job_id: %s, 配置信息未找到，请检查!' % job_id)
        return status

    try:
        print(result)
        trigger = result[0]['trigger']
        trigger_args = result[0]['trigger_args']
        jitter = result[0]['jitter']
        run_at_startup = result[0]['run_at_startup']
    except Exception as e:
        print('job_id: %s, config parse error!' % job_id)
        return status

    if trigger == 'cron':
        interval = str(trigger_args.split('=')[1])
        try:
            if re.search('second', trigger_args):
                status = True
                if run_at_startup in ['True', 'true']:
                    scheduler.add_job(func=func, id=job_id, trigger=trigger, second=interval, jitter=jitter, next_run_time=now())
                else:
                    scheduler.add_job(func=func, id=job_id, trigger=trigger, second=interval, jitter=jitter)
            else:
                print('cron only support trigger_args: second', trigger_args, interval)
        except Exception as e:
            print('job_id: %s, trigger_args error: %s!' % (job_id, e))
        else:
            status = True
    elif trigger == 'crontab':
        if not trigger_args:
            print('%s trigger_args 不能为空' % job_id)
            return status
        values = trigger_args.split()
        if len(values) != 5:
            print('Wrong number of fields; got {}, expected 5'.format(len(values)))
            return status
        status = True
        if run_at_startup in ['True', 'true']:
            scheduler.add_job(func=func, id=job_id, trigger='cron', jitter=jitter, next_run_time=now(),
                              minute=values[0],hour=values[1],day=values[2],month=values[3],day_of_week=values[4])
        else:
            scheduler.add_job(func=func, id=job_id, trigger='cron', jitter=jitter,
                              minute=values[0], hour=values[1], day=values[2], month=values[3], day_of_week=values[4])
    else:
        print('job_id: %s only support trigger: cron/crontab' % job_id)

    return status

'''
增加定时任务的步骤：
1、import一个你自己写的计划任务模块，单独文件
2、在下方增加一条add_job，配置好参数
3、重启task_manager.py任务

参数说明：
1、定时任务模块，所有任务之间异步执行，互相不阻塞
2、trigger='interval' 表示循环执行，seconds表示间隔时间，也可以是minutes、hours、days；jitter表示浮动区间，比如每个小时执行，
但前后浮动10s，避免并发问题；next_run_time=now() 表示启动后立刻执行，不设定的话就正常调度
trigger = 'cron', month='6-8,11-12', day='3rd fri', hour='0-3'
------------ 定时任务 Start ------------'''


# 电话告警和钉钉告警的监听
try:
    from src.task.monitor import disaster_listen as d, alert_listen, get_aliyun_alert as a, get_zabbix_alert as z
except ModuleNotFoundError:
    record_info_log(task_log_file, error_message)
else:
    add_job(func=d.disaster_alert_listen, job_id='monitor_disaster_listen')
    add_job(func=alert_listen.alert_listen, job_id='monitor_dingtalk_listen')
    add_job(func=a.aliyun_alert_handler, job_id='monitor_get_aliyun_alert')
    add_job(func=z.zabbix_alert_handler, job_id='monitor_get_zabbix_alert')


# 定时巡检所有域名证书的过期时间，写入sql
try:
    from src.task import exec_ssl_expiretime
except ModuleNotFoundError:
    record_info_log(task_log_file, error_message)
else:
    add_job(func=exec_ssl_expiretime.exec_ssl, job_id='get_sslexpiretime')


# 云账号余额数据采集
try:
    from src.task.cost import query_account_balance, query_bill_overview, cycle_cost_calculate, collect_resource_package
    from src.task.cost import get_renew
except ModuleNotFoundError:
    record_info_log(task_log_file, error_message)
else:
    add_job(func=query_account_balance.query_account_balance, job_id='cost_collect_balance')
    add_job(func=query_bill_overview.query_bill_overview_handler, job_id='cost_collect_bill_overview')
    add_job(func=collect_resource_package.collect_aliyun_resource_package, job_id='cost_collect_resource_package')
    add_job(func=cycle_cost_calculate.calculate_handler, job_id='cost_calculate_cycle_cost')
    add_job(func=get_renew.query_renew_handler, job_id='get_product_renew')

# 阿里云instance采集
try:
    from src.task import exec_instanceid
except ModuleNotFoundError:
    record_info_log(task_log_file, error_message)
else:
    add_job(func=exec_instanceid.get_intance_info, job_id='get_intance_info')


# github扫描ak泄漏情况
try:
    from src.task.git import github_gps
except ModuleNotFoundError:
    record_info_log(task_log_file, error_message)
else:
    add_job(func=github_gps.exec_github, job_id='github_ak')

# 专线告警事件数据采集
try:
    from src.task import pn_problem_collect
except ModuleNotFoundError:
    record_info_log(task_log_file, error_message)
else:
    add_job(func=pn_problem_collect.get_pn_event, job_id='get_pn_event')


# 专线告警事件源数据采集
try:
    from src.task import pn_problem_source_data
except ModuleNotFoundError:
    record_info_log(task_log_file, error_message)
else:
    add_job(func=pn_problem_source_data.get_pn_event_source_data, job_id='get_pn_event_source_data')

# 专线延时数据分布采点分析采集
try:
    from src.task import pn_problem_delay
except ModuleNotFoundError:
    record_info_log(task_log_file, error_message)
else:
    add_job(func=pn_problem_delay.get_pn_event_delay_data, job_id='get_pn_event_delay_data')


# 异常判定每10分钟执行一次
try:
    from src.judge import all_judge
except ModuleNotFoundError:
    record_info_log(task_log_file, error_message)
else:
    add_job(func=all_judge.do_all_judge, job_id='do_all_judge')

# 报表发送每天执行一次(王炸暂定)
try:
    from src.reports import week_reports
except ModuleNotFoundError:
    record_info_log(task_log_file, error_message)
else:
    add_job(func=week_reports.report, job_id='week_reports')


# ------------ 定时任务 END ------------
# 定时任务内容写在上面
# 下面的不要动

scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
scheduler.add_listener(miss_listener, EVENT_JOB_MISSED)
scheduler._logger = logging


def query_task_status():
    scheduler.print_jobs()
    job_list = scheduler.get_jobs()
    for job in job_list:
        message = "任务状态展示: %s" % job
        print(message)
        record_info_log(task_log_file, message)


def scheduler_main():
    count = 1   # 计数，控制时间用
    task_startup = False    # 任务调度未启动，用于初次执行scheduler.start()
    lock_status = False     # 是否本机的锁
    ttl_time = 300  # 加锁的ttl值，也就是双活切换的时间
    global job_event_status_dict
    job_event_status_dict = {}
    query_redis_fail_count = 0  # 查询redis失败次数，次数范围内，可以重试；如果超过一定次数，则需要调度执行

    while True:
        # 查询锁，判断自己是否注册
        # noinspection PyBroadException
        try:
            result = query_redis_key_exist(key)
        except Exception as e:
            if query_redis_fail_count < 5:
                msg = "查询key失败，reason: %s, 暂时不调度!" % e
                print_func(msg)
                query_redis_fail_count += 1
                time.sleep(loop_interval)  # 这个时间不会影响任务调度的间隔
                count += 1
                continue
            else:
                result = False
                msg = "查询key失败超过一定次数，开始任务调度!"
                print_func(msg)
        else:
            query_redis_fail_count = 0  # 查询成功，数据清零
            msg = 'query redis key exist: %s' % result
            print_func(msg)

        local_hostname = get_local_hostname()  # 获取本机机器名
        if result is True:  # key存在, 检查内容和本机机器名是否一致
            try:
                hostname_in_redis = db_redis.RedisApi().get_value_of_string(key)
            except Exception as e:
                msg = 'query hostname from redis fail, reason: %s' % e
                print_func(msg)
            print_func('local_hostname: %s, hostname_in_redis: %s' % (local_hostname, hostname_in_redis))
            if local_hostname == hostname_in_redis:     # 是本机的锁
                msg = '锁内容一致，是本机的锁'
                print_func(msg)
                record_debug_log(task_debug_file, msg)
                lock_status = True
            else:   # 非本机的锁
                msg = "当前锁名称: %s, 和本机名称: %s 不同! 本轮不调度，等待下个周期继续抢锁..." % (hostname_in_redis, local_hostname)
                print_func(msg)
                record_info_log(task_log_file, msg)
        elif result is False:
            lock_status = True
            msg = '%s 锁不存在，开始执行!' % datetime.datetime.now()
            print_func(msg)
            record_info_log(task_log_file, msg)

        if lock_status:  # 是本机的锁，或锁不存在，则抢锁(或更新锁时间)，并向下继续调度任务
            msg = "开始加锁..."
            print_func(msg)
            record_debug_log(task_debug_file, msg)
            result = db_redis.RedisApi().set_key_with_ttl(key, local_hostname, ttl_time)
            result = True
            if result:
                msg = "加锁成功!"
                print_func(msg)
                record_debug_log(task_debug_file, msg)
            else:
                msg = "加锁失败，进入下个循环!"
                print_func(msg)
                time.sleep(5)
                continue
            if task_startup is False:
                try:
                    msg = '开始启动任务调度...'
                    print_func(msg)
                    record_info_log(task_log_file, msg)
                    scheduler.start()
                except Exception as e:
                    msg = '启动任务调度失败!'
                    print_func(msg)
                    db_redis.RedisApi().delete_key(key)
                    exit_scheduler(e)
                else:
                    task_startup = True
                    scheduler.print_jobs()
                    job_list = scheduler.get_jobs()
                    for job in job_list:
                        message = "任务状态展示: %s" % job
                        record_info_log(task_log_file, message)
            if count >= 60:     # 次数
                query_task_status()
                count = 1  # 控制展示状态一个小时展示一次

            if job_event_status_dict:
                status = flush_job_info_to_mysql()
                msg = 'MySQL commit success!'
                print_func(msg)
                record_info_log(task_log_file, msg)

        else:   # 非本机的锁，本机任务进入下一个周期，继续判断锁
            pass

        time.sleep(loop_interval)  # 这个时间不会影响任务调度的间隔
        count += 1


if __name__ == "__main__":
    scheduler_main()
