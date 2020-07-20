#!/usr/bin/env python
#coding=utf-8

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException

import os, configparser

file_path = os.path.join(os.path.dirname(__file__), "../../../conf/key.conf")
cf = configparser.ConfigParser()
cf.read(file_path)
ak_section = 'aliyun_master'    # 默认用阿里云主账号的a k
default_accessid = cf.get(ak_section, 'AccessKeyId')
default_accesssecret = cf.get(ak_section, 'AccessKeySecret')
default_regionid = cf.get(ak_section, 'DefaultRegionId')


class AliyunApi:
    def __init__(self, accessid=default_accessid, accesssecret=default_accesssecret, regionid=default_regionid):
        accessid = accessid
        accesssecret = accesssecret
        regionid = regionid
        self.client = AcsClient(accessid, accesssecret, regionid)

    def query_account_balance(self):    # 账号余额
        from aliyunsdkbssopenapi.request.v20171214.QueryAccountBalanceRequest import QueryAccountBalanceRequest
        request = QueryAccountBalanceRequest()
        request.set_accept_format('json')
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        else:
            return response

    def query_resource_package(self):   # 资源包
        from aliyunsdkbssopenapi.request.v20171214.QueryResourcePackageInstancesRequest import QueryResourcePackageInstancesRequest
        request = QueryResourcePackageInstancesRequest()
        request.set_accept_format('json')
        request.set_PageSize(100)
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        else:
            return str(response, encoding='utf-8')

    def query_bill_overview(self, billingcycle):    # 账单总览
        from aliyunsdkbssopenapi.request.v20171214.QueryBillOverviewRequest import QueryBillOverviewRequest
        request = QueryBillOverviewRequest()
        request.set_accept_format('json')
        request.set_BillingCycle(billingcycle)
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        else:
            return str(response, encoding='utf-8')

    def query_available_instance(self, end_time_start, end_time_end, page=1, limit=100):     # 有效实例查询，所有产品，包含时间等信息
        from aliyunsdkbssopenapi.request.v20171214.QueryAvailableInstancesRequest import QueryAvailableInstancesRequest

        request = QueryAvailableInstancesRequest()
        request.set_accept_format('json')
        request.set_PageNum(page)
        request.set_PageSize(limit)
        request.set_SubscriptionType("Subscription")
        request.set_RenewStatus("ManualRenewal")
        request.set_EndTimeStart(end_time_start)
        request.set_EndTimeEnd(end_time_end)

        try:
            response = self.client.do_action_with_exception(request)
        except Exception as e:
            return False
        else:
            return response

    def describe_vul_list(self, format, vul_type, dealed, page, limit):
        from aliyunsdksas.request.v20181203.DescribeVulListRequest import DescribeVulListRequest
        request = DescribeVulListRequest()

        request.set_accept_format(format)
        request.set_Type(vul_type)
        request.set_Dealed(dealed)
        request.set_CurrentPage(page)
        request.set_PageSize(limit)
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        return response

    def describe_alarmevent_list(self, format, page, limit, From):
        from aliyunsdksas.request.v20181203.DescribeAlarmEventListRequest import DescribeAlarmEventListRequest
        request = DescribeAlarmEventListRequest()

        request.set_accept_format(format)
        request.set__From(From)
        request.set_CurrentPage(page)
        request.set_PageSize(limit)
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        return response

    def list_users(self, format, marker):
        from aliyunsdkram.request.v20150501.ListUsersRequest import ListUsersRequest
        request = ListUsersRequest()
        request.set_accept_format(format)
        if marker :
            request.set_Marker(marker)
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        return response

    def get_user_lastlogintime(self, format, username):
        from aliyunsdkram.request.v20150501.GetUserRequest import GetUserRequest
        request = GetUserRequest()
        request.set_accept_format(format)
        request.set_UserName(username)
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        return response

    def get_user_loginprofile(self, format, username):
        from aliyunsdkram.request.v20150501.GetLoginProfileRequest import GetLoginProfileRequest
        request = GetLoginProfileRequest()
        request.set_accept_format(format)
        request.set_UserName(username)
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        return response

    def get_user_policies(self, format, username):
        from aliyunsdkram.request.v20150501.ListPoliciesForUserRequest import ListPoliciesForUserRequest
        request = ListPoliciesForUserRequest()
        request.set_accept_format(format)
        request.set_UserName(username)
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        return response

    def get_user_ak(self, format, username):  # 获取用户所有的ak信息
        from aliyunsdkram.request.v20150501.ListAccessKeysRequest import ListAccessKeysRequest
        request = ListAccessKeysRequest()
        request.set_accept_format(format)
        request.set_UserName(username)
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        return response

    def get_last_useak_time(self, format, eventrw, ak_id):
        from aliyunsdkactiontrail.request.v20171204.LookupEventsRequest import LookupEventsRequest
        request = LookupEventsRequest()
        request.set_accept_format(format)

        request.set_EventRW(eventrw)
        request.set_EventAccessKeyId(ak_id)
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        return response

    def get_domain_list(self, format, page, limit):
        from aliyunsdkdomain.request.v20180129.QueryDomainListRequest import QueryDomainListRequest
        request = QueryDomainListRequest()

        request.set_accept_format(format)
        request.set_PageNum(page)
        request.set_PageSize(limit)
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        return response

    def get_dns_domain(self, format, page, limit, domain):
        from aliyunsdkalidns.request.v20150109.DescribeDomainRecordsRequest import DescribeDomainRecordsRequest
        request = DescribeDomainRecordsRequest()

        request.set_accept_format(format)
        request.set_DomainName(domain)
        request.set_PageNumber(page)
        request.set_PageSize(limit)
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        return response

    def get_slbinstance_id(self, format, page, limit):
        from aliyunsdkslb.request.v20140515.DescribeLoadBalancersRequest import DescribeLoadBalancersRequest
        request = DescribeLoadBalancersRequest()

        request.set_accept_format(format)
        request.set_PageNumber(page)
        request.set_PageSize(limit)
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        return response

    def get_slbinstance_info(self, format, instance_id):
        from aliyunsdkslb.request.v20140515.DescribeLoadBalancerAttributeRequest import DescribeLoadBalancerAttributeRequest
        request = DescribeLoadBalancerAttributeRequest()

        request.set_accept_format(format)
        request.set_LoadBalancerId(instance_id)
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        return response

    def get_slbinstance_count(self, format, instance_id):
        from aliyunsdkslb.request.v20140515.DescribeLoadBalancersRequest import DescribeLoadBalancersRequest
        request = DescribeLoadBalancersRequest()

        request.set_accept_format(format)
        request.set_LoadBalancerId(instance_id)
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        return response

    def get_ecsinstances_info(self, format, page, limit):
        from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
        request = DescribeInstancesRequest()

        request.set_accept_format(format)
        request.set_PageNumber(page)
        request.set_PageSize(limit)
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        return response

    def get_ecsinstance_info(self, format, page, limit, instanceid):
        from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
        request = DescribeInstancesRequest()

        request.set_accept_format(format)
        request.set_InstanceIds([instanceid])
        request.set_PageNumber(page)
        request.set_PageSize(limit)
        try:
            response = self.client.do_action_with_exception(request)
        except:
            return False
        return response


if __name__ == "__main__":
    result = AliyunApi().query_account_balance()
    print(result)
