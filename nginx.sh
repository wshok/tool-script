#!/bin/bash

## nginx log 4xx 5xx

cur_date=$(date "+%Y-%m-%d")
source_log='/var/log/nginx/iggm.access-'$cur_date'.log'
tmp_log='/tmp/nginx-watcher'
url='https://oapi.dingtalk.com/robot/send?access_token='
if [ -f $source_log ];then
    tail -n 100 $source_log | awk '{if($13>400)print $13, $4, $5, $11}' > $tmp_log
    err_num=`cat $tmp_log | wc -l`

    if [ $err_num -ge 10 ];then 
        err_lines=`tail -n 5 $tmp_log`
        curl -s -o /dev/null -d '{"msgtype":"text","text":{"content":"warning：\u8bbf\u95ee\u5f02\u5e38 \r\n '"$err_lines"' "}}' $url -H 'Content-Type: application/json'
    fi
fi
