#!/bin/bash
yum install httpd -y
yum upgrade -y
if [ ! -d /var/www/html ]; then
    mkdir -p /var/www/html
fi
echo "healthcheck" > /var/www/html/healthcheck.html
service httpd on
chkconfig --levels 345 httpd on
