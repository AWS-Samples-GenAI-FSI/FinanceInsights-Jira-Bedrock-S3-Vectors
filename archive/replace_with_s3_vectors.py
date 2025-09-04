import boto3
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

def replace_with_s3_vectors():
    """Replace OpenSearch KB with S3 Vectors KB"""
    
    region = os.getenv('AWS_REGION', 'us-east-1')
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    iam = boto3.client('iam')
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    
    timestamp = str(int(time.time()))[-6:]
    role_name = f'BedrockS3Vectors-{timestamp}'
    
    print("Creating S3 Vectors Knowledge Base...")
    
    # 1. Create IAM role for S3 Vectors
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
    
    # 2. Add S3 Vectors permissions
    iam.put_role_policy(
        RoleName=role_name,
        PolicyName='S3VectorsPolicy',
        PolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": ["bedrock:InvokeModel"], "Resource": f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1"},
                {"Effect": "Allow", "Action": ["s3:GetObject", "s3:ListBucket"], "Resource": ["arn:aws:s3:::jira-tickets-s3-kb", "arn:aws:s3:::jira-tickets-s3-kb/*"]},
                {"Effect": "Allow", "Action": ["s3:*"], "Resource": "*"}
            ]
        })
    )
    
    print("✅ Created role with S3 permissions")
    time.sleep(30)  # IAM propagation
    
    # 3. Create S3 Vectors KB
    kb_response = bedrock_agent.create_knowledge_base(
        name=f'jira-s3vectors-{timestamp}',
        roleArn=f'arn:aws:iam::{account_id}:role/{role_name}',
        knowledgeBaseConfiguration={
            'type': 'VECTOR',
            'vectorKnowledgeBaseConfiguration': {
                'embeddingModelArn': f'arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1'
            }
        },
        storageConfiguration={
            'type': 'S3_VECTORS',
            's3VectorsConfiguration': {}
        }
    )
    
    kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
    print(f"✅ Created S3 Vectors KB: {kb_id}")
    
    # 4. Create data source
    ds_response = bedrock_agent.create_data_source(
        knowledgeBaseId=kb_id,
        name='jira-s3vectors-datasource',
        dataSourceConfiguration={
            'type': 'S3',
            's3Configuration': {
                'bucketArn': 'arn:aws:s3:::jira-tickets-s3-kb'
            }
        }
    )
    
    # 5. Start ingestion
    bedrock_agent.start_ingestion_job(
        knowledgeBaseId=kb_id,
        dataSourceId=ds_response['dataSource']['dataSourceId']
    )
    
    print("✅ Started S3 Vectors ingestion")
    
    # 6. Update .env with new KB
    with open('.env', 'r') as f:
        content = f.read()
    
    # Replace old KB ID
    content = content.replace('KNOWLEDGE_BASE_ID=ICK71UCFE6', f'KNOWLEDGE_BASE_ID={kb_id}')
    
    with open('.env', 'w') as f:
        f.write(content)
    
    print(f"🎉 Replaced with S3 Vectors KB: {kb_id}")
    print("✅ 100% AWS native - no FAISS, no OpenSearch!")
    
    return kb_id

if __name__ == "__main__":
    replace_with_s3_vectors()