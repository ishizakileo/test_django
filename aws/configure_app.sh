#!/bin/bash
# 各種ディレクトリの権限設定
chown -R appuser:appgroup /var/www/html/
chown -R appuser:appgroup /opt/myapp/
chown -R appuser:appgroup /etc/myapp/

# 設定ファイルの環境変数置換
envsubst < /etc/myapp/prod.conf > /etc/myapp/prod.conf.tmp
mv /etc/myapp/prod.conf.tmp /etc/myapp/prod.conf
