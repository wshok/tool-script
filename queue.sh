#!/bin/bash

url='https://oapi.dingtalk.com/robot/send?access_token=
6'
max=100

for k in email-send-queue order-notice-queue;
do
    n=`redis-cli -h 127.0.0.1 -p 6379 -n 0 llen $k`

    if [ $n -ge $max ];then
       curl -s -o /dev/null -d '{"msgtype":"text","text":{"content":"warning：queue cumulate: '"$k: $n"' "}}' $url -H 'Content-Type: application/json'
    fi
done
