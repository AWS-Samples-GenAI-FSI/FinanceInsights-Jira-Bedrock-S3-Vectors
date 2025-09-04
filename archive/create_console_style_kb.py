import boto3
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

def create_console_style_kb():
    """Create KB using console-style approach"""
    
    region = os.getenv('AWS_REGION', 'us-east-1')
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    iam = boto3.client('iam')
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    
    timestamp = str(int(time.time()))[-6:]
    role_name = f'AmazonBedrockExecutionRoleForKnowledgeBase_{timestamp}'
    
    # Create role exactly like console does
    iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "bedrock.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        })
    )
    
    # Attach managed policy like console
    try:
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
        )
    except:
        pass
    
    # Add S3 permissions
    iam.put_role_policy(
        RoleName=role_name,
        PolicyName='S3Access',
        PolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:ListBucket"],
                "Resource": ["arn:aws:s3:::jira-tickets-s3-kb", "arn:aws:s3:::jira-tickets-s3-kb/*"]
            }]
        })
    )
    
    print("✅ Created console-style role")
    time.sleep(30)
    
    # Create KB with RDS (managed by AWS)
    kb_response = bedrock_agent.create_knowledge_base(
        name=f'jira-console-{timestamp}',
        roleArn=f'arn:aws:iam::{account_id}:role/{role_name}',
        knowledgeBaseConfiguration={
            'type': 'VECTOR',
            'vectorKnowledgeBaseConfiguration': {
                'embeddingModelArn': f'arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1'
            }
        }
        # No storageConfiguration = uses managed RDS
    )
    
    kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
    print(f"✅ Created managed KB: {kb_id}")
    
    # Create data source
    ds_response = bedrock_agent.create_data_source(
        knowledgeBaseId=kb_id,
        name='jira-datasource',
        dataSourceConfiguration={'type': 'S3', 's3Configuration': {'bucketArn': 'arn:aws:s3:::jira-tickets-s3-kb'}}
    )
    
    # Start ingestion
    bedrock_agent.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_response['dataSource']['dataSourceId'])
    print("✅ Started ingestion")
    
    # Update .env
    with open('.env', 'w') as f:
        f.write(f'AWS_REGION={region}\n')
        f.write(f'KNOWLEDGE_BASE_ID={kb_id}\n')
    
    print(f"🎉 Console-style KB created: {kb_id}")
    print("⏳ Wait 3 minutes for ingestion")

if __name__ == "__main__":
    create_console_style_kb()