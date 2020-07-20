#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import threading
import pymysql
import DBUtils.PooledDB

connargs = {"host": "rm-bp15in4n827sceu6j8o.mysql.rds.aliyuncs.com", "user": "cannon_test", "passwd": "fJzVL&cc7OPaUpBu", "db": "cannon-test"}


def test(conn):
    try:
        cursor = conn.cursor()
        count = cursor.execute("select * from alert_list where production = 'ecs' limit 1")
        rows = cursor.fetchall()
        for r in rows:
            #print(rows)
            pass
    finally:
        conn.close()


def testloop():
    print("testloop")
    for i in range(50):
        conn = pymysql.connect(**connargs)
        test(conn)


def testpool():
    print("testpool")
    #pooled = DBUtils.PooledDB.PooledDB(pymysql, mincached=5, maxcached=100, maxconnections=50000, blocking=False, **connargs)
    pooled = DBUtils.PooledDB.PooledDB(pymysql, **connargs)
    for i in range(100):
        conn = pooled.connection()
        test(conn)


def main():
    t = testloop if len(sys.argv) == 1 else testpool
    for i in range(200):
        threading.Thread(target=t).start()


if __name__ == "__main__":
    main()
