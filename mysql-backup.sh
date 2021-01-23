#!/bin/sh

db_user="yfos911"
db_passwd="2YmDM/TPPbiYetul"
db_host="localhost"
db_name="yfos"

backup_dir="/home/ec2-user/mysql-backup"
time="$(date +"%y%m%d%H%M%S")"
MYSQL="/usr/bin/mysql"
MYSQLDUMP="/usr/bin/mysqldump"

MKDIR="/bin/mkdir"
RM="/bin/rm"
MV="/bin/mv"
GZIP="/bin/gzip"

test ! -w $backup_dir && echo "Error: $backup_dir is un-writeable." && exit 0
test ! -d "$backup_dir/$time/" && $MKDIR "$backup_dir/$time"

$MYSQLDUMP -u $db_user -h $db_host -p$db_passwd  --skip-lock-tables $db_name | $GZIP -9 > "$backup_dir/$time/$db_name.tar.gz"

# all_db="$($MYSQL -u $db_user -h $db_host -p$db_passwd -Bse 'show databases')"
# for db in $all_db
# do
# $MYSQLDUMP -u $db_user -h $db_host -p$db_passwd  --skip-lock-tables $db | $GZIP -9 > "$backup_dir/$time/$db.tar.gz"
# done

# test -d "$backup_dir/backup.5/" && $RM -rf "$backup_dir/backup.5"

# for int in 4 3 2 1 0
# do
# if(test -d "$backup_dir"/backup."$int")
# then
# next_int='expr $int + 1'
# fi
# done

echo "The backup is complete"
find $backup_dir/*  -mtime +1|xargs rm -rf
find $backup_dir/ -type d -empty -exec rmdir {} \; >/dev/null 2>&1
exit 0;
