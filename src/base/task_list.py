#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def task_list():
    # 监听是否触发电话告警
    from src.task.test import test
    #add_job(func=test.test_1, job_id='test1')
    #add_job(func=test.test_2, job_id='test2')
    #add_job(func=test.test_3, job_id='test3')
    #add_job(func=test.test_4, job_id='test4')
    scheduler.add_job(func=test.test_1, id='test1', trigger='cron', jitter=2, minute='*/1')




