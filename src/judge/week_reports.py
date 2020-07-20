#!/usr/bin/env python3
# coding:utf-8
import xlwt
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
# 项目的lib
from src.lib import db_mysql
mysql_conn = db_mysql.MyPymysqlPool()
problem_table = 'gps_problem'
methods_table = 'gps_judge_methods'
rules_table = 'gps_rules'
ssl_expire_method = 'ssl_expire_judge'


def set_style(name, height, bold=False, coller='white'):
    style = xlwt.XFStyle()  # 初始化样式

    font = xlwt.Font()  # 为样式创建字体
    font.name = name  # 'Times New Roman'
    font.bold = bold
    font.color_index = 4
    font.height = height
    style.font = font  # 设置字体

    al = xlwt.Alignment()
    al.horz = 0x02  # 设置水平居中
    al.vert = 0x01  # 设置垂直居中
    style.alignment = al  # 设置单元格对齐方式

    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = xlwt.Style.colour_map[coller]
    style.pattern = pattern  # 设置单元格背景色

    borders = xlwt.Borders()
    borders.left = 1
    borders.right = 1
    borders.top = 1
    borders.bottom = 1
    style.borders = borders  # 设置边框上下左右都为细实现；细实线:1，小粗实线:2，细虚线:3，中细虚线:4，大粗实线:5，双线:6，细点虚线:7
    return style


def build_excel_sheet(file_path):
    # 新建一个工作薄对象
    report = xlwt.Workbook(encoding='utf-8')
    # 激活一个新的sheet
    sheet1 = report.add_sheet(u'sheet1', cell_overwrite_ok=True)
    first_col = sheet1.col(0)
    sec_col = sheet1.col(1)
    third_col = sheet1.col(2)
    firth_col = sheet1.col(3)
    first_col.width = 256 * 25
    sec_col.width = 256 * 10
    third_col.width = 256 * 50
    firth_col.width = 256 * 20
    # 给sheet创建列名行名
    row0 = [u'事件', u'数量', u'对象', u'值']
    # 获取规则id对应异常数量的dict
    all_count_dict = get_method_count()
    # 将方法列为列表
    column0 = list(all_count_dict)
    # 生成首行
    for m in range(0, len(row0)):
        sheet1.write(0, m, row0[m], set_style('Times New Roman', 360, True, 'green'))
    # 按类合并单元格的第0列和第1列
    line = 1
    for j in column0:
        k = 1
        sheet1.write_merge(line, int(all_count_dict[j])+line-1, 0, 0, j, set_style('Times New Roman', 300, False, 'yellow'))
        sheet1.write_merge(line, int(all_count_dict[j])+line-1, 1, 1, all_count_dict[j], set_style('Times New Roman', 300, False, 'white'))
        k += 1
        # 将数据写入表格
        sql = "select id from %s where expression_name = '%s'" % (rules_table, j)
        expression_id = mysql_conn.select(sql)[0][0]
        sql = "select gps_object, value from %s where expression_id = '%s' and status = 1" % (problem_table, expression_id)
        result = mysql_conn.select(sql)
        for bb in result:
            gps_object = bb[0]
            value = bb[1]
            sheet1.write(line, 2, gps_object, set_style('Times New Roman', 300, False, 'white'))
            sheet1.write(line, 3, value, set_style('Times New Roman', 300, False, 'white'))
            line += 1
    report.save(file_path)


def build_excel_html():
    from HTMLTable import HTMLTable
    # 生成表名
    table = HTMLTable(caption='运维巡检系统本周报表\n')
    # 生成首行
    table.append_header_rows((
        ('事件', '对象', '触发条件', '当前值'),
    ))
    # 获取规则id对应异常数量的dict
    all_count_dict = get_method_count()
    # 将方法列为列表
    column0 = list(all_count_dict)
    for j in column0:
        sql = "select id, method_name, reference_value, compare from %s where expression_name = '%s'" % (rules_table, j)
        expression_id = mysql_conn.select(sql)[0][0]
        method_name = mysql_conn.select(sql)[0][1]
        reference_value = mysql_conn.select(sql)[0][2]
        compare = mysql_conn.select(sql)[0][3]
        sql = "select comments from %s where name = '%s'" % (methods_table, method_name)
        comments = mysql_conn.select(sql)[0][0]
        sql = "select gps_object, value from %s where expression_id = '%s' and status = 1" % (problem_table, expression_id)
        result = mysql_conn.select(sql)
        for bb in range(0, all_count_dict[j]):
            gps_object = result[bb][0]
            value = result[bb][1]
            table.append_data_rows((
                (comments, gps_object, str(compare)+str(reference_value), value),
            ))
    # 标题样式
    table.caption.set_style({
        'font-size': '20px',
    })
    # 表格样式，即<table>标签样式
    table.set_style({
        'border-collapse': 'collapse',
        'word-break': 'keep-all',
        'white-space': 'nowrap',
        'font-size': '14px',
    })
    # 统一设置所有单元格样式，<td>或<th>
    table.set_cell_style({
        'border-color': '#000',
        'border-width': '1px',
        'border-style': 'solid',
        'padding': '5px',
        'text-align': 'center',  # 单元格居中
    })
    # 表头样式
    table.set_header_row_style({
        'color': '#fff',
        'background-color': '#48a6fb',
        'font-size': '18px',
    })

    # 覆盖表头单元格字体样式
    table.set_header_cell_style({
        'padding': '15px',
    })
    html = table.to_html()
    return html


def get_method_count():  # 查找所有判定方法，及其异常数据量，转化为字典
    count_dict = dict()
    expression_id_list = list()
    sql = "select id from gps_rules"
    result = mysql_conn.select(sql)
    for i in result:
        expression_id = i[0]
        expression_id_list.append(expression_id)

    for n in expression_id_list:
        sql = "select expression_name from %s where id = '%s'" % (rules_table, n)
        result = mysql_conn.select(sql)
        expression = result[0][0]
        sql = "select count(*) from %s where expression_id = '%s' and status = 1" % (problem_table, n)
        result = mysql_conn.select(sql)
        count = result[0][0]
        if count != 0:
            count_dict[expression] = count
    return count_dict


def create_email(email_from, from_name, email_to, to_name, email_subject, email_text, annex_path, annex_name):
    # 输入发件人昵称、收件人昵称、主题，正文，附件地址,附件名称生成一封邮件
    # 生成一个空的带附件的邮件实例
    message = MIMEMultipart()
    # # 将正文以text的形式插入邮件中
    message.attach(MIMEText(email_text, 'html', 'utf-8'))
    # 生成发件人名称（这个跟发送的邮件没有关系）
    message['From'] = from_name+'<'+email_from+'>'
    # 生成收件人名称（这个跟接收的邮件也没有关系）
    message['To'] = to_name+'<'+email_to+'>'
    # 生成邮件主题
    message['Subject'] = Header(email_subject, 'utf-8')
    # 读取附件的内容
    att1 = MIMEText(open(annex_path, 'rb').read(), 'base64', 'utf-8')
    att1["Content-Type"] = 'application/octet-stream'
    # 生成附件的名称
    att1["Content-Disposition"] = 'attachment; filename=' + annex_name
    # 将附件内容插入邮件中
    message.attach(att1)
    # 返回邮件
    return message


def send_email(sender, password, receiver, msg):
    # 一个输入邮箱、密码、收件人、邮件内容发送邮件的函数
    try:
        # 找到你的发送邮箱的服务器地址，已加密的形式发送
        server = smtplib.SMTP_SSL('smtp.exmail.qq.com', 465)  # 发件人邮箱中的SMTP服务器
        server.ehlo()
        # 登录你的账号
        server.login(sender, password)  # 括号中对应的是发件人邮箱账号、邮箱密码
        # 发送邮件
        server.sendmail(sender, receiver, msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号（是一个列表）、邮件内容
        print("邮件发送成功")
        server.quit()  # 关闭连接
    except Exception as e:
        print(e)
        print("邮件发送失败")


def delete_reportfile(file_path):
    if os.path.exists(file_path):  # 如果文件存在
        # 删除文件，可使用以下两种方法。
        os.remove(file_path)
        # os.unlink(file_path)
    else:
        print('no such file:%s' % file_path)  # 则返回文件不存在


def report(task_id=False):
    now = datetime.now()
    now_date = now.strftime('%Y-%m-%d')
    # 文件名称
    my_file_name = 'report_week-'+now_date+'.xlsx'
    # 文件路径
    file_path = './' + my_file_name
    # 生成excel
    build_excel_sheet(file_path)

    my_email_from = ""
    my_from_name = "ops"
    my_email_to = ""
    my_to_name = "sre"
    # 邮件标题
    my_email_subject = '运维巡检周报  ' + str(now_date)
    # 邮件正文
    # 先读取html文件
    # f = open("report-week.html", 'r', encoding='utf-8')
    msg = str(build_excel_html())

    # my_email_text = "Dear all,\n\t附件为巡检每周数据，请查收！\n\n运维团队 "
    content = msg
    # 附件地址
    my_annex_path = file_path
    # 附件名称
    my_annex_name = my_file_name
    # 生成邮件
    my_msg = create_email(my_email_from, my_from_name, my_email_to, my_to_name, my_email_subject,
                          content, my_annex_path, my_annex_name)
    my_sender = my_email_from
    my_password = ''
    my_receiver = [my_email_to]  # 接收人邮箱列表
    # 发送邮件
    send_email(my_sender, my_password, my_receiver, my_msg)

    delete_reportfile(file_path)


if __name__ == "__main__":
    report()
