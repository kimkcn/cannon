#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging


def record_info_log(logfile, message):
    LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"  #配置输出日志格式
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'  #配置输出时间的格式，注意月份和天数不要搞乱了
    logging.basicConfig(level=logging.INFO,
                        format=LOG_FORMAT,
                        datefmt=DATE_FORMAT,
                        filemode='a',
                        filename=logfile
                        )
    logging.info(message)
    return True


def record_error_log(logfile, message):
    LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"  #配置输出日志格式
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'  #配置输出时间的格式，注意月份和天数不要搞乱了
    logging.basicConfig(level=logging.ERROR,
                        format=LOG_FORMAT,
                        datefmt=DATE_FORMAT,
                        filename=logfile,
                        filemode='a'
                        )
    logging.error(message)
    return True


def record_debug_log(logfile, message):
    LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"  #配置输出日志格式
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'  #配置输出时间的格式，注意月份和天数不要搞乱了
    logging.basicConfig(level=logging.DEBUG,
                        format=LOG_FORMAT,
                        datefmt=DATE_FORMAT,
                        filemode='a',
                        filename=logfile
                        )
    logging.debug(message)
    return True


if __name__ == "__main__":
    show_alert_list('xxx')