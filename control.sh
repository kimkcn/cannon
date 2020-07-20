#!/bin/bash

CANNON_PORT=8081
APP_NAME=cannon
RUN_USER=app
OWN_PATH=(/opt /logs)
LOG_PATH=/opt/outlog
APPCHECK_URL="http://127.0.0.1:8081/admin"
PIPBASE='http://mirrors.aliyun.com/pypi/simple/'
PY=`which python3`

function Init() {
    #创建app用户，相关目录授权
    id -u ${RUN_USER} > /dev/null 2>&1
    if [ $? -ne 0 ];then
        /usr/sbin/useradd  -s /sbin/nologin $RUN_USER >/dev/null 2>&1
        if [ $? -ne 0 ];then
            echo "add user:$RUN_USER failed"
            exit 1
        fi
    fi

    mkdir -p ${OWN_PATH[@]} $LOG_PATH && chmod 744 -R ${OWN_PATH[@]} || exit 1
    chown $RUN_USER.$RUN_USER -R ${OWN_PATH[@]}

    if [ "${DEPLOYENV}_x" = "test_x" ];then
        env_init
    fi
}

function env_init() {
    echo > ${LOG_PATH}/pip.log
    if [[ -f "/opt/${APP_NAME}/requirements.txt" ]];then
        rm -f /opt/${APP_NAME}/requirements.txt
    fi

    pigar=`which pigar`
    if [[ $? -ne 0 ]];then
        if [[ -e "/usr/local/python3/bin/pigar" ]];then
            pigar=/usr/local/python3/bin/pigar
        else
            echo "`date +%Y_%m_%d-%H:%M:%S` pip3 install pigar" >> ${LOG_PATH}/pip.log 2>&1
            pip3 install pigar >> ${LOG_PATH}/pip.log 2>&1
            pigar=/usr/local/python3/bin/pigar
        fi
    fi

    (echo 'y';sleep 1) |$pigar -p /opt/${APP_NAME}/requirements.txt -P /opt/${APP_NAME}/
    if [[ $? -eq 0 ]];then
        echo "`date +%Y_%m_%d-%H:%M:%S`  第三方依赖包清单文件生成成功，/opt/${APP_NAME}/requirements.txt" >> ${LOG_PATH}/pip.log 2>&1
    else
        echo "`date +%Y_%m_%d-%H:%M:%S`  第三方依赖包清单文件生成失败，请检查原因" >> ${LOG_PATH}/pip.log 2>&1
    fi

    #删除错乱行
    sed -i "/^dd-/d" requirements.txt
    sed -i "/^src/d" requirements.txt
    pip3 install -r requirements.txt -i ${PIPBASE} --trusted-host mirrors.aliyun.com >> ${LOG_PATH}/pip.log 2>&1
}

function doStop() {
    #local zabbix_action=0
    #local action_name=stop
    #doZabbix_monitor
    getpid
    if [[ -z ${pid} ]];then
        echo  "process is not exist,ignore"
    else
        echo -e "\nkill java process"
        kill ${pid} &>/dev/null

        listenCheck
        if [[ $listenstatus = 1 ]];then
            echo "tcp connection release failed,will doForcestop"
            doForcestop
        else
            echo "tcp connection release success"
        fi

        getpid
        if [ -z "${pid}" ] ; then
           echo "process stop success"
        else
           doForcestop
        fi
        return 0
    fi
}

function doForcestop() {
    local zabbix_action=0
    local action_name=stop
    doZabbix_monitor

    getpid
    if [  -z $pid ];then
        echo  "process is not exist"
    else
        echo "kill -9 ${APP_NAME} process"
        kill -9 $pid &>/dev/null
        sleep 3

        listenCheck
        if [[ $listenstatus = 1 ]];then
            echo -e "tcp connection release failed"
            exit 1
        else
            echo -e "tcp connection release success"
        fi

        getpid
        if [ -z "${pid}" ];then
            echo "process stop success"
        else
            echo "process stop failed"
            exit 1
        fi
    fi
}

function doStart() {
    Init
    getpid
    if [[ -z ${pid} ]];then
        rm -f $LOG_PATH/out.log >/dev/null 2>&1
        su -s /bin/bash -c "exec ${PY} /opt/${APP_NAME}/${APP_NAME}_manage.py runserver 0.0.0.0:${CANNON_PORT} >/opt/outlog/server.log 2>&1" $RUN_USER

        for i in {1..5}
        do
            sleep 1
            getpid
            if [[ ! -z ${pid} ]];then
                break
            fi
        done

        local process_info=`ps -ef | grep -w ${APP_NAME} | grep -v 'grep'`
        if [[ -z ${pid} ]];then
            echo -e "process start failed"
            exit 1
        else
            echo "process start success"
            echo ${process_info}
        fi
    else
        echo "The process already exist"
        exit 1
    fi

#    local zabbix_action=1
#    local action_name=start
#    doZabbix_monitor
}

function listenCheck() {
    #根据netstat命令输出检查是否有pid相关python进程的端口在监听
    for i in {1..5}
    do
        netstat -lntp |grep "$pid/python" >/dev/null 2>&1
        if [ $? -eq 0 ];then
            listenstatus=1
            echo -e "\nretry ${i}th times(2s) for TCP connection release"
            sleep 2
        else
            listenstatus=0
            break
        fi
    done
}

function doRestart() {
    doStop
    if [ $? -eq 0 ];then
        doStart
    else
        echo "process stop failed"
        exit 1
    fi
}

function doCheckPid() {
    getpid
    if [ -z $pid ];then
        echo "process start failed"
        exit 1
    else
        echo "process start success,java pid is ${pid}"
    fi
}

function doCheckFunc() {
    getpid
    if [[ -z "${pid}" ]]; then
        echo "找不到进程号"
        exit 1
    fi

    for i in $(seq 1 5)
    do
        local appcheck_result=$(curl -m 5 -sL -w "%{http_code}" -o /dev/null ${APPCHECK_URL})
        if [ "x_$appcheck_result" = "x_200" ]; then
            APP_HEALTH="ok"
            break
        else
            APP_HEALTH="problem"
            echo "retry check ${i}th times(5s),process is Unhealthy"
            sleep 2
        fi
    done

    if [[ "x_$APP_HEALTH" == x_ok ]];then
        echo "process is healthy"
    else
        echo "process is Unhealthy"
        exit 1
    fi
}

function appServiceInfo() {
    getpid

    PROCESS_USER=`ps -ef |grep $pid |grep -v 'grep' |awk '{printf $1}'`

    echo "--------------------------------------------------------------------------------------------"
    printf "%-25s %-10s %-10s %-10s %-15s \n" appName user pid appHealth
    echo "--------------------------------------------------------------------------------------------"
    printf "%-25s %-10s %-10s %-10s %-15s \n" ${APP_NAME} ${PROCESS_USER} ${pid} ${APP_HEALTH}
    echo "--------------------------------------------------------------------------------------------"
}

function doZabbix_monitor {
    zabbix_api='http://oc.ops.yangege.cn/api/monitor/switch'
    zabbix_ak='1d42ee7b99a7d92bdbdaccc3edc30a9f'
    private_ip=`ifconfig eth0 | grep inet | awk '{print $2}'`

    #action=0关闭，action=1开启
    param="ak=${zabbix_ak}&privateIp=${private_ip}&action=${zabbix_action}"
    #兜底后台执行命令方式，即使失败不会阻塞其他步骤的执行
    nohup curl --connect-timeout 3 -m 2 -s -w "`date +%Y_%m_%d-%H:%M:%S`\n" "${zabbix_api}?${param}" >> ${LOG_PATH}/zabbix_monitor.log 2>&1
    if [[ $? -eq 0 ]];then
        echo "${action_name} zabbix_monitor success"
    else
        echo "${action_name} zabbix_monitor failed"
    fi
    return 0
}

if [ $# -eq 1 ];then
    case $1 in
        -start|start)
          doStart
          ;;
        -stop|stop)
          doStop
          ;;
        -forcestop|forcestop|kill)
          doForcestop
          ;;
        -restart|restart)
          doRestart
          ;;
        -checkfunc|checkfunc)
          doCheckFunc
          ;;
        -checkpid|checkpid)
          doCheckPid
          ;;
        -h|--help|-help|help)
          echo "use dump or -dump for ..."
          echo "use start or -start for ..."
          echo "use stop or -stop for ..."
          echo "use forcestop or -forestop for ..."
          echo "use h or help or -h or -help for ..."
          ;;
        *)
          echo "参数异常,可执行-h查看脚本使用说明"
          exit 1 ;;
    esac
elif [ $# -eq 0 ] ; then
    doCheckFunc
    appServiceInfo
else
    echo "usage: no more than one action"
    exit 1
fi
