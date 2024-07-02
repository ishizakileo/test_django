#!/bin/bash

# CSVヘッダーを出力
echo "関数名,変数名,変数値"

# Lambda関数の一覧を取得
functions=$(aws lambda list-functions --query 'Functions[*].FunctionName' --output text)

# 各関数に対して処理
for func in $functions
do
    # 関数の環境変数を取得
    env_vars=$(aws lambda get-function-configuration --function-name $func --query 'Environment.Variables' --output json)
    
    # 環境変数が存在する場合
    if [ "$env_vars" != "null" ]; then
        # 環境変数をパースしてCSV形式で出力
        echo $env_vars | jq -r 'to_entries[] | ["'"$func"'", .key, .value] | @csv'
    else
        # 環境変数が存在しない場合
        echo "$func,N/A,N/A"
    fi
done
