#!/usr/bin/env python3
# coding=utf-8
import json
import time
import os
import urllib.request
import zipfile
import xlrd
from aliyunsdkcore.client import AcsClient
from aliyunsdksas.request.v20181203.ExportRecordRequest import ExportRecordRequest
from aliyunsdksas.request.v20181203.DescribeExportInfoRequest import DescribeExportInfoRequest

# 项目的lib
from src.lib import db_mysql
mysql_conn = db_mysql.MyPymysqlPool()

client = AcsClient('LTAI4G1bKTNKKAMav1N8q9bS', 'qfmg6D0Y0X5pxdYcMO7UMfQ40tjwil', 'cn-hangzhou')


def get_akleak_id():
    request = ExportRecordRequest()
    request.set_accept_format('json')

    request.set_ExportType("accessKey")

    response = client.do_action_with_exception(request)

    response_json = json.loads(response)
    akleak_id = response_json['Id']
    time.sleep(10)

    return akleak_id


def export_akleak_info():
    akleak_id = get_akleak_id()

    request = DescribeExportInfoRequest()
    request.set_accept_format('json')

    request.set_ExportId(akleak_id)

    response = client.do_action_with_exception(request)
    response_json = json.loads(response)

    leakinfo_link = response_json['Link']

    return leakinfo_link


def get_leakinfo_file():  # 下载leakinfo文件，并解压
    url = export_akleak_info()

    # 定义ak泄漏信息文件的下载存储路径
    dir = os.getcwd()
    leakinfo_file_path = os.path.join(dir,'tmp')
    if not os.path.exists(leakinfo_file_path):
        os.makedirs(leakinfo_file_path)

    filename = str(int(time.time()))+'.zip'  # 定义下载的文件名为时间戳加格式

    urllib.request.urlretrieve(url, leakinfo_file_path + '/' + filename)  # 下载文件到leakinfo_file_path的目录下

    # 将下载的.zip格式的文件解压
    zip_file = zipfile.ZipFile(leakinfo_file_path + '/' + filename, "r")
    zip_file.extractall(path=leakinfo_file_path + '/')
    leak_excel_file = zip_file.namelist()[0]

    zip_file.close()

    return leak_excel_file


def read_leakfile():
    dir = os.getcwd()
    leakinfo_file_path = os.path.join(dir, 'tmp')
    file_name = get_leakinfo_file()
    # 打开excel文件
    workBook = xlrd.open_workbook(leakinfo_file_path + '/' + file_name)

    # 按索引号获取sheet的名字
    sheet_name = workBook.sheet_names()[0]

    # 按sheet名字获取sheet内容，行数，列数
    sheet0_content = workBook.sheet_by_name(sheet_name)
    nrows= sheet0_content.nrows

    row = 1
    while row < nrows:
        ak_id = sheet0_content.cell_value(row, 0)
        code = str(sheet0_content.cell_value(row, 2))
        host = sheet0_content.cell_value(row, 6)
        fileurl = sheet0_content.cell_value(row, 7)
        repourl = sheet0_content.cell_value(row, 9)
        user = sheet0_content.cell_value(row, 10)
        filetype = sheet0_content.cell_value(row, 11)
        update_sql(ak_id, host, fileurl, repourl, user, filetype)
        row += 1


def update_sql(ak_id, host, fileurl, repourl, user, filetype):
    # 查找url相同
    sql = 'select count(id) from %s where ak_id = "%s" and fileurl = "%s";' % ("safe_sas_akleak", ak_id, fileurl)
    result = mysql_conn.select(sql)
    leak_count = result[0][0]

    if leak_count == 0:
        sql = 'insert into %s(ak_id, host, fileurl, repourl, user, filetype) ' \
              'values("%s", "%s", "%s", "%s", "%s", "%s")' % \
              ("safe_sas_akleak", ak_id, host, fileurl, repourl, user, filetype)
        mysql_conn.insert(sql)
        mysql_conn.end()


if __name__ == "__main__":
    read_leakfile()
