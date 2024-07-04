import boto3
import csv
from time import sleep
import json

# AWS クライアントの初期化
cf_client = boto3.client('cloudformation')
lambda_client = boto3.client('lambda')

def get_all_stacks():
    """すべてのCloudFormationスタックを取得する"""
    stacks = []
    paginator = cf_client.get_paginator('list_stacks')
    for page in paginator.paginate(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE']):
        stacks.extend(page['StackSummaries'])
    return [stack['StackName'] for stack in stacks]

def detect_drift(stack_name):
    """指定されたスタックのドリフト検出を実行し、結果を返す"""
    response = cf_client.detect_stack-drift(StackName=stack_name)
    detection_id = response['StackDriftDetectionId']
    
    while True:
        status = cf_client.describe_stack_drift_detection_status(StackDriftDetectionId=detection_id)
        if status['DetectionStatus'] != 'DETECTION_IN_PROGRESS':
            return status
        sleep(5)

def get_drifted_resources(stack_name):
    """ドリフトしたリソースの詳細を取得する"""
    paginator = cf_client.get_paginator('describe_stack_resource_drifts')
    drifted_resources = []
    for page in paginator.paginate(StackName=stack_name):
        drifted_resources.extend([res for res in page['StackResourceDrifts'] if res['StackResourceDriftStatus'] != 'IN_SYNC'])
    return drifted_resources

def get_lambda_env_var_changes(resource):
    """Lambda関数の環境変数の変更を取得する"""
    if resource['ResourceType'] != 'AWS::Lambda::Function':
        return "Not a Lambda function"
    
    changes = []
    for diff in resource.get('PropertyDifferences', []):
        if diff['PropertyPath'] == '/Environment/Variables':
            # 環境変数の差分を詳細に解析
            expected = json.loads(diff['ExpectedValue'])
            actual = json.loads(diff['ActualValue'])
            
            # 追加された環境変数
            for key in actual.keys() - expected.keys():
                changes.append(f"Added: {key}={actual[key]}")
            
            # 削除された環境変数
            for key in expected.keys() - actual.keys():
                changes.append(f"Removed: {key}")
            
            # 変更された環境変数
            for key in expected.keys() & actual.keys():
                if expected[key] != actual[key]:
                    changes.append(f"Changed: {key} from '{expected[key]}' to '{actual[key]}'")
    
    return '; '.join(changes) if changes else "No changes in environment variables"

def main():
    stacks = get_all_stacks()
    
    with open('lambda_drift_report.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['StackName', 'ResourceId', 'ResourceType', 'DriftStatus', 'EnvironmentVariableChanges'])

        for stack in stacks:
            print(f"Checking drift for stack: {stack}")
            drift_status = detect_drift(stack)
            
            if drift_status['StackDriftStatus'] == 'DRIFTED':
                drifted_resources = get_drifted_resources(stack)
                
                for resource in drifted_resources:
                    env_var_changes = get_lambda_env_var_changes(resource)
                    writer.writerow([
                        stack,
                        resource['LogicalResourceId'],
                        resource['ResourceType'],
                        resource['StackResourceDriftStatus'],
                        env_var_changes
                    ])
            else:
                writer.writerow([stack, 'N/A', 'N/A', drift_status['StackDriftStatus'], 'N/A'])

    print("Lambda drift report generated: lambda_drift_report.csv")

if __name__ == "__main__":
    main()
