"""cannon URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
import sys
sys.path.append("..")
from django.conf.urls import url
from django.contrib import admin
from src.base import task_thread
from src.api.monitor import monitor_switch, show_alert
from src.api.gps import get_ssl_expiretime,get_ram_userinfo
from src.api.gps.safe import get_sas_alert,get_sas_akleak,get_sas_vul
from src.api.voice_call import voice_notification_api,duty_poll_api
from src.api.cost import query_total_cost, query_account_balance, query_bill_overview, query_resource_package
from src.api.cost import query_product_renew
from src.api.task import task
from src.api import login, status
from src.judge import problem_search, all_judge, rules
from src.api.pn_problem import pn_problem_api
from src.api.pn_problem import pn_problem_delay_api

urlpatterns = [
    # 公共部分接口，勿动
    url(r'^admin/', admin.site.urls),
    url(r'^api/login$', login.login),
    url(r'^api/status$', status.query_status),

    # 任务框架相关接口
    url(r'^api/task/schedule_event$', task.show_task_schedule),
    url(r'^api/task/job_config$', task.query_task_job_config),
    url(r'^api/task/job_config/add$', task.add_task_job_config),
    url(r'^api/task/job_config/update$', task.update_task_job_config),
    url(r'^api/task/job_config/del$', task.delete_task_job_config),

    # 告警相关接口
    url(r'^api/alert$', show_alert.get_alert_list),
    url(r'^api/monitor/switch$', monitor_switch.zabbix_monitor_switch),
    url(r'^api/voice-call$', voice_notification_api.call_up),
    url(r'^api/duty_poll$', duty_poll_api.duty_handler),

    # 巡检相关接口
    url(r'^api/gps/showssl$',get_ssl_expiretime.get_sslexpiretime),
    url(r'^api/gps/safe/alert$',get_sas_alert.get_sas_alert),
    url(r'^api/gps/safe/akleak$',get_sas_akleak.get_sas_akleak),
    url(r'^api/gps/safe/vul_count$',get_sas_vul.get_sas_vul_count),
    url(r'^api/gps/safe/vul_list$',get_sas_vul.get_sas_vul_list),
    url(r'^api/gps/ram$', get_ram_userinfo.get_ram_userinfo),
    url(r'^api/gps/problem$', problem_search.get_problem_data),
    url(r'^api/pn_problem', pn_problem_api.pn_status),

    # 巡检规则相关接口
    url(r'^api/rule/add$', rules.add_rules),
    url(r'^api/rule/del$', rules.delete_rules),
    url(r'^api/rule/select$', rules.select_rules),
    url(r'^api/rule/update', rules.update_rules),

    # 异常判定接口
    url(r'^api/judge/all', all_judge.do_all_judge),

    # 费用相关接口
    url(r'^api/cost/query_balance$', query_account_balance.query_account_balance),
    url(r'^api/cost/query_bill_overview$', query_bill_overview.query_bill_overview),
    url(r'^api/cost/query_resource_package$', query_resource_package.query_resource_package),
    url(r'^api/cost/query_month_cost$', query_total_cost.get_month_total_cost_web),
    url(r'^api/cost/query_item_cost$', query_total_cost.query_item_cost),
    url(r'^api/cost/query_month_cost_range$', query_total_cost.get_month_cost_range_list),
    url(r'^api/cost/query_product_renew$', query_product_renew.query_product_renew),

    # 专线质量分析接口
    url(r'^api/pn/pn_block_problem', pn_problem_delay_api.pn_status),
    url(r'^api/pn/pn_delay_problem', pn_problem_delay_api.pn_delay_status),

]


# 以线程方式启动任务调度
task_thread.calling_task_with_thread()
