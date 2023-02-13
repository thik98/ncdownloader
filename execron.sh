#!/bin/sh
printenv | awk '{print "export " $1}' > /env.sh
/usr/sbin/cron -f