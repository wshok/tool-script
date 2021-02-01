#!/bin/bash

#date="/var/scripts/`date +%Y%m%d`"
#echo -e "--------- `date '+%Y-%m-%d %H:%M:%S'` ---------" >> $date.txt
#echo -e "--mem" >> $date.txt
#ps auxw|head -1 >> ${date}.txt;
#ps auxw|sort -rn -k4|head -20 >> ${date}.txt;
#sleep 2s
#echo -e "--cpu" >> $date.txt
#ps auxw|head -1 >> ${date}.txt;
#ps auxw|sort -rn -k3|head -20 >> ${date}.txt;
#echo -e "--top" >> $date.txt
#top -n 1 -b | head -5 >> $date.txt
#sleep 1s

freemem=`free -m | grep -i mem| awk '{print int($4/$2*100)}'`
usecpu=`top -n 1 -d 1 -b | grep Cpu | awk '{print int($2)}'`
echo "freemem: $freemem, usecpu: $usecpu"
if [ $freemem -le 20 -o $usecpu -ge 80 ] ;then
    curl -s -o /dev/null  -d '{"msgtype":"text","text":{"content":"warning：cpu-used: '$usecpu'%, free-mem: '$freemem'%. "},"at":{"isAtAll":true}}' 'https://oapi.dingtalk.com/robot/send?access_token=' -H 'Content-Type: application/json'
fi
