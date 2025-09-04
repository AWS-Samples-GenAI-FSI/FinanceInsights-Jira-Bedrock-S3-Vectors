import boto3
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

def create_working_kb():
    """Create new working KB from scratch"""
    
    region = os.getenv('AWS_REGION', 'us-east-1')
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    iam = boto3.client('iam')
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    s3 = boto3.client('s3')
    
    timestamp = str(int(time.time()))[-6:]
    role_name = f'BedrockKB-{timestamp}'
    bucket_name = f'jira-kb-{timestamp}'
    
    print(f"Creating working KB with bucket: {bucket_name}")
    
    # 1. Create S3 bucket
    s3.create_bucket(Bucket=bucket_name)
    
    # 2. Upload simple data
    sample_data = """Title: Frontend Performance Issue
Description: Dashboard loading slowly due to large bundle sizes
Priority: High
Component: Frontend
Status: Open"""
    
    s3.put_object(Bucket=bucket_name, Key='ticket1.txt', Body=sample_data)
    print("✅ Created bucket and uploaded data")
    
    # 3. Create role
    iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Principal": {"Service": "bedrock.amazonaws.com"}, "Action": "sts:AssumeRole"}]
        })
    )
    
    iam.put_role_policy(
        RoleName=role_name,
        PolicyName='BedrockPolicy',
        PolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": ["bedrock:InvokeModel"], "Resource": f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1"},
                {"Effect": "Allow", "Action": ["s3:GetObject", "s3:ListBucket"], "Resource": [f"arn:aws:s3:::{bucket_name}", f"arn:aws:s3:::{bucket_name}/*"]}
            ]
        })
    )
    
    print("✅ Created role")
    time.sleep(20)
    
    # 4. Create KB with RDS (simpler than OpenSearch)
    try:
        kb_response = bedrock_agent.create_knowledge_base(
            name=f'jira-working-{timestamp}',
            roleArn=f'arn:aws:iam::{account_id}:role/{role_name}',
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f'arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1'
                }
            },
            storageConfiguration={'type': 'RDS'}
        )
        
        kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
        print(f"✅ Created KB: {kb_id}")
        
        # 5. Create data source
        ds_response = bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name='jira-data',
            dataSourceConfiguration={'type': 'S3', 's3Configuration': {'bucketArn': f'arn:aws:s3:::{bucket_name}'}}
        )
        
        bedrock_agent.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_response['dataSource']['dataSourceId'])
        print("✅ Started ingestion")
        
        # Update .env
        with open('.env', 'w') as f:
            f.write(f'AWS_REGION={region}\n')
            f.write(f'KNOWLEDGE_BASE_ID={kb_id}\n')
        
        print(f"🎉 Working KB created: {kb_id}")
        return kb_id
        
    except Exception as e:
        print(f"❌ RDS KB failed: {e}")
        return None

if __name__ == "__main__":
    create_working_kb()