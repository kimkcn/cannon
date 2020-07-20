#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.billing.v20180709 import billing_client, models
import configparser

file_path = os.path.join(os.path.dirname(__file__), "../../../conf/key.conf")
cf = configparser.ConfigParser()
cf.read(file_path)
ak_section = 'tencentcloud'    # 默认a k
default_accessid = cf.get(ak_section, 'AccessKeyId')
default_accesssecret = cf.get(ak_section, 'AccessKeySecret')
default_regionid = cf.get(ak_section, 'DefaultRegionId')


class TencentCloudApi:
    def __init__(self, accessid=default_accessid, accesssecret=default_accesssecret, regionid=default_regionid):
        from tencentcloud.common import credential
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile
        from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

        accessid = accessid
        accesssecret = accesssecret
        self.regionid = regionid
        self.cred = credential.Credential(accessid, accesssecret)
        self.clientProfile = ClientProfile()
        self.httpProfile = HttpProfile()
        self.clientProfile.httpProfile = self.httpProfile

    def query_account_balance(self):    # 账户余额
        from tencentcloud.billing.v20180709 import billing_client, models
        self.httpProfile.endpoint = "billing.tencentcloudapi.com"
        try:
            client = billing_client.BillingClient(self.cred, self.regionid, self.clientProfile)
            req = models.DescribeAccountBalanceRequest()
            params = '{}'
            req.from_json_string(params)
            resp = client.DescribeAccountBalance(req)
        except TencentCloudSDKException as err:
            print(err)
            return False
        else:
            return resp.to_json_string()

    def query_product_bill(self, start_time, end_time):   # 产品级别的账单
        from tencentcloud.billing.v20180709 import billing_client, models
        self.httpProfile.endpoint = "billing.tencentcloudapi.com"
        PayerUin = "100013454040"

        try:
            client = billing_client.BillingClient(self.cred, self.regionid, self.clientProfile)
            req = models.DescribeBillSummaryByProductRequest()
            params = '{\"PayerUin\":\"%s\",\"BeginTime\":\"%s\",\"EndTime\":\"%s\"}' % (PayerUin, start_time, end_time)
            req.from_json_string(params)
            resp = client.DescribeBillSummaryByProduct(req)
        except TencentCloudSDKException as err:
            print(err)
            return False
        else:
            print(resp.to_json_string())
            return resp.to_json_string()

if __name__ == "__main__":
    #print(TencentCloudApi().query_account_balance())
    print(TencentCloudApi().query_product_bill())