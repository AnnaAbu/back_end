#!/bin/sh



DB_USER="root"
DB_PASS="13313288898lzt"
DB_HOST="localhost"
DB_NAME="yuanshuting"

# Others vars
BIN_DIR="/usr/bin"            #the mysql bin path
BCK_DIR="/opt/tiger/mysql_backup"    #the backup file directory
DATE=`date +%F`

# TODO
#/usr/bin/mysqldump --opt -u -pbatsingpw -hlocalhost timepusher > /mnt/mysqlBackup/db_`date +%F`.sql
$BIN_DIR/mysqldump --opt -u$DB_USER -p$DB_PASS -h$DB_HOST $DB_NAME| gzip > $BCK_DIR/db_$DATE.sql.gz

find $BCK_DIR/* -mtime +30 -exec -rm {} \;

