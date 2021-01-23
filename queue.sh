#!/bin/bash

url='https://oapi.dingtalk.com/robot/send?access_token=0bc0e6c67ed1ea6207cbd65eff058278568c1889c5f7361fb918367d3a70347
6'
max=100

for k in iggm-email-send-queue iggm-order-notice-queue mmowts-email-send-queue;
do
    n=`redis-cli -h 127.0.0.1 -p 6379 -n 0 llen $k`

    if [ $n -ge $max ];then
       curl -s -o /dev/null -d '{"msgtype":"text","text":{"content":"warning：IGGM queue cumulate: '"$k: $n"' "}}' $url -H 'Content-Type: application/json'
    fi
done
