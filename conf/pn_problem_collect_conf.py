
#主机ip列表
hostip_list=['192.168.10.71','192.168.10.90','172.17.32.185','172.17.33.53']
#hostip_list=['192.168.10.71']

#专线节点列表
pn_master_list=['VBR-master','ali-Z1-master','aws-A1-master','aws-DX-master']
pn_backup_list=['VBR-backup','ali-Z2-backup','aws-A2-backup','aws-DX-backup']
pn_aws_list=['aws-template-3','proxy-aws.zabbix.ops.yangege.cn']
pn_aliyun_list=['opscloud-1','opscloud-2']
pn_node_list=['VBR-backup-ping','VBR-master-ping','ali-Z1-master-ping','ali-Z2-backu-ping','aws-A1-master-ping',
           'aws-A2-backu-ping','aws-DX-backup-ping','aws-DX-master-ping','aws-template-3-ping',
'proxy-aws.zabbix.ops.yangege.cn-ping', 'opscloud-1', 'opscloud-2']

#触发器列表
trigger_delay=['VBR-master monitor delay',
               'VBR-backup monitor delay',
               'aws-DX-master monitor delay',
               'aws-DX-backup monitor delay',
               'aws-A2-backup monitor delay',
               'aws-A1-master monitor delay',
               'ali-Z2-backup monitor delay',
               'ali-Z1-master monitor delay',
               'aws-template-3 monitor delay',
               'opscloud-1 monitor delay']

trigger_block=['VBR-master monitor block',
               'VBR-backup monitor block',
               'aws-DX-master monitor block',
               'aws-DX-backup monitor block',
               'aws-A2-backup monitor block',
               'aws-A1-master monitor block',
               'ali-Z2-backup monitor block',
               'ali-Z1-master monitor block',
               'aws-template-3 monitor block',
               'opscloud-1 monitor block',
               'aliyun-mark monitor block',
               'aws-mark monitor block']

trigger_telnet=['zabbix-server telnet is down','aws-zabbix-proxy telnet is down']

item_name_delay = ['ali-Z1-master-ping',
                   'ali-Z2-backup-ping',
                   'aws-A1-master-ping',
                   'aws-A2-backup-ping',
                   'aws-DX-backup-ping',
                   'aws-DX-master-ping',
                   'aws-template-3-ping',
                   'opscloud-1-ping',
                   'opscloud-2-ping',
                   'proxy-aws.zabbix.ops.yangege.cn-ping',
                   'VBR-backup-ping',
                   'VBR-master-ping']

#专线监控模板
template_name = 'Template private network'
#template_name = 'Template TELNET CUSTOM'