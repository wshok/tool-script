#!/bin/bash

echo -e "\e[34m 开始发布 \e[0m"

project=$1
deploytag=$2

projects=(
yfos
iggm
mmowts
)

if [ $project = "" ]
then
    echo -e "\e[34m 发布    ---- \e[0m\e[41m 失败(项目参数错误) \e[0m"
    exit 0
fi

if [[ ${projects[@]/${project}/} = ${projects[@]} ]];then
    echo -e "\e[34m 发布    ---- \e[0m\e[41m 失败(项目参数错误) \e[0m"
    exit 0
fi


if [[ $deploytag = "" ]]
then
    echo -e "\e[34m 发布    ---- \e[0m\e[41m 失败(tag号参数错误) \e[0m"
    exit 0
fi

i=false
if [ -e '/home/www/tool/deploy.txt' ]
then
    history=`cat /home/www/tool/deploy.txt | awk -F '----' '{print $1}'`
    (echo $history | grep -w $project"--"$deploytag >/dev/null) && i=true
fi

if [[ $i = true ]]
then
    echo -e "\e[34m 发布    ---- \e[0m\e[41m 失败(该版本已发布) \e[0m"
    exit 0
fi

repo='git@127.0.0.1:/home/git/repo/'$project'.git'
branch='master'
if [ $project = 'iggm' -o $project = 'yfos' ]
then
    branch='develop'
fi
tmpath='/tmp/deploy-'$project'/'

if [ -d $tmpath ]
then 
    rm -rf $tmpath
fi

git clone -b $branch $repo $tmpath >/dev/null 2>&1

cd $tmpath

git pull >/dev/null 

echo -e "\e[34m 拉取    ---- \e[0m\e[42m 成功 \e[0m"

lasttag=`git ls-remote --tags origin | awk '{sub("refs/tags/", ""); print $2"----"$1}' |sort -k1 -Vr | head -1`
pretag=`git ls-remote --tags origin | awk '{sub("refs/tags/", ""); print $2"----"$1}' |sort -k1 -Vr | head -2 | tail -1`

newtag=`echo $lasttag | awk -F'----' '{print $1}'`

if [[ $deploytag != $newtag ]]
then
    echo -e "\e[34m 发布    ---- \e[0m\e[41m 失败(tag号错误) \e[0m"
    exit 0
fi

newtagid=`echo $lasttag | awk -F'----' '{print $2}'`
pretagid=`echo $pretag | awk -F'----' '{print $2}'`

if [ $newtagid = $pretagid -o $newtagid = "" -o $pretagid = "" ]
then
    echo -e "\e[34m 发布    ---- \e[0m\e[41m 失败(tag号错误) \e[0m"
    exit 0
fi


if [ ! -d $tmpath"tar/" ]
then
    mkdir $tmpath"tar/"
fi


tarname=$tmpath"tar/"$project"-"$newtag".tar.gz"
git diff $pretagid $newtagid --name-only | xargs tar -czf $tarname

echo -e "\e[34m 打包    ---- \e[0m\e[42m 成功 \e[0m"

if [ -e $tarname ]
then
    scp -i ~/.ssh/www.pem $tarname www@18.204.211.115:~  >/dev/null

    echo -e "\e[34m 推送    ---- \e[0m\e[42m 成功 \e[0m"

    ssh -i ~/.ssh/www.pem www@18.204.211.115 >/dev/null 2>&1 << eeooff

    cd ~

    if [ -e /home/www/$project-$newtag".tar.gz" ]
    then
        tar -zxf /home/www/$project-$newtag".tar.gz" -C /home/www/webroot/$project/ >/dev/null
        rm -f /home/www/$project-$newtag".tar.gz"
    fi
    if [ $project = 'yfos' ]
    then
        cp -f /home/www/webroot/$project/public/index.html /home/www/webroot/$project/public/611c54d66a4e8514.html
        echo > /home/www/webroot/$project/public/index.html
    fi

    exit

eeooff

echo -e "\e[34m 解压    ---- \e[0m\e[42m 成功 \e[0m"

else
    echo -e "\e[34m 发布    ---- \e[0m\e[41m 失败(打包错误) \e[0m"
    exit 0

fi

rm -rf $tmpath

echo -e "\e[34m 发布    ---- \e[0m\e[42m 成功 \e[0m"
echo -e "\e[42m 发布完成 \e[0m"
echo $project--$newtag ---- `date +%Y-%m-%d\ %H:%M:%S` >> /home/www/tool/deploy.txt
