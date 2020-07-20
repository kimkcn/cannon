#!/usr/bin/env python3
# -*- coding: utf-8 -*-

table_name = 'alert_list'      # 告警信息存储的数据库
#table_name = 'alert_info_test_new'      # 告警信息存储的数据库
black_list = ['rds', 'kvstore', 'drds', 'kafka', 'streamcompute', 'event_sys']
zabbix_switch_table = 'host_zabbix_status'      # zabbix监控启停记录表
alert_list_limit = 50

# 阿里云，采集最后多少小时的告警数据
last_hours = 4

# zabbix 配置
zabbix_min_severity = 2     # 采集的最低级别