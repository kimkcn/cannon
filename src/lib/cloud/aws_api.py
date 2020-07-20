#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import configparser
try:
    import simplejson as json
except ImportError:
    import json

file_path = os.path.join(os.path.dirname(__file__), "../../../conf/key.conf")
cf = configparser.ConfigParser()
cf.read(file_path)
ak_section = 'aws'    # 默认a k
default_accessid = cf.get(ak_section, 'AccessKeyId')
default_accesssecret = cf.get(ak_section, 'AccessKeySecret')
default_regionid = cf.get(ak_section, 'DefaultRegionId')


class AwsApi:
    def __init__(self, accessid=default_accessid, accesssecret=default_accesssecret, regionid=default_regionid):
        import boto3
        self.bill = boto3.client('ce', aws_access_key_id=accessid, aws_secret_access_key=accesssecret,
                            region_name=regionid)

    def get_cost_and_usage(self, month_start, month_end):
        try:
            response = self.bill.get_cost_and_usage(
                TimePeriod={
                    "Start": month_start,
                    "End": month_end
                },
                Granularity="MONTHLY",
                Metrics=[
                    "BlendedCost"
                ],
                GroupBy=[
                    {
                        "Type": "DIMENSION",
                        "Key": "SERVICE"
                    }
                ]
            )
        except Exception as e:
            print(e)
            result_total = False
        else:
            result_total = json.loads(json.dumps(response))
        return result_total


if __name__ == "__main__":
    #print(TencentCloudApi().query_account_balance())
    print(TencentCloudApi().query_product_bill())