import boto3
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

def create_simple_opensearch():
    """Create OpenSearch KB without pre-creating index"""
    
    region = os.getenv('AWS_REGION', 'us-east-1')
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    aoss = boto3.client('opensearchserverless', region_name=region)
    iam = boto3.client('iam')
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    
    collection_name = f'jira-{int(time.time())}'
    role_name = f'BedrockKB-{int(time.time())}'
    
    # Create policies
    aoss.create_security_policy(
        name=f"{collection_name}-encryption",
        type='encryption',
        policy=json.dumps({"Rules": [{"Resource": [f"collection/{collection_name}"], "ResourceType": "collection"}], "AWSOwnedKey": True})
    )
    
    aoss.create_security_policy(
        name=f"{collection_name}-network",
        type='network', 
        policy=json.dumps([{"Rules": [{"Resource": [f"collection/{collection_name}"], "ResourceType": "collection"}], "AllowFromPublic": True}])
    )
    
    # Create collection
    aoss.create_collection(name=collection_name, type='VECTORSEARCH')
    print(f"✅ Created collection: {collection_name}")
    
    # Wait for active
    while True:
        status = aoss.batch_get_collection(names=[collection_name])
        if status['collectionDetails'][0]['status'] == 'ACTIVE':
            break
        time.sleep(10)
    
    collection_id = status['collectionDetails'][0]['id']
    collection_arn = f"arn:aws:aoss:{region}:{account_id}:collection/{collection_id}"
    
    # Create role
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
                {"Effect": "Allow", "Action": ["s3:GetObject", "s3:ListBucket"], "Resource": ["arn:aws:s3:::jira-tickets-s3-kb", "arn:aws:s3:::jira-tickets-s3-kb/*"]},
                {"Effect": "Allow", "Action": ["aoss:APIAccessAll"], "Resource": collection_arn}
            ]
        })
    )
    
    # Data access policy
    aoss.create_access_policy(
        name=f"{collection_name}-access",
        type='data',
        policy=json.dumps([{
            "Rules": [
                {"Resource": [f"collection/{collection_name}"], "Permission": ["aoss:CreateCollectionItems", "aoss:UpdateCollectionItems", "aoss:DescribeCollectionItems"], "ResourceType": "collection"},
                {"Resource": [f"index/{collection_name}/*"], "Permission": ["aoss:CreateIndex", "aoss:UpdateIndex", "aoss:DescribeIndex", "aoss:ReadDocument", "aoss:WriteDocument"], "ResourceType": "index"}
            ],
            "Principal": [f"arn:aws:iam::{account_id}:role/{role_name}"]
        }])
    )
    
    time.sleep(20)
    
    # Create KB - let Bedrock create the index
    kb_response = bedrock_agent.create_knowledge_base(
        name=f'jira-opensearch-kb-{int(time.time())}',
        roleArn=f'arn:aws:iam::{account_id}:role/{role_name}',
        knowledgeBaseConfiguration={
            'type': 'VECTOR',
            'vectorKnowledgeBaseConfiguration': {
                'embeddingModelArn': f'arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1'
            }
        },
        storageConfiguration={
            'type': 'OPENSEARCH_SERVERLESS',
            'opensearchServerlessConfiguration': {
                'collectionArn': collection_arn,
                'vectorIndexName': f'{collection_name}-index',
                'fieldMapping': {
                    'vectorField': 'vector',
                    'textField': 'text', 
                    'metadataField': 'metadata'
                }
            }
        }
    )
    
    kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
    print(f"✅ Created KB: {kb_id}")
    
    # Create data source
    ds_response = bedrock_agent.create_data_source(
        knowledgeBaseId=kb_id,
        name='jira-datasource',
        dataSourceConfiguration={'type': 'S3', 's3Configuration': {'bucketArn': 'arn:aws:s3:::jira-tickets-s3-kb'}}
    )
    
    bedrock_agent.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_response['dataSource']['dataSourceId'])
    print("✅ Started ingestion")
    
    with open('.env', 'a') as f:
        f.write(f'\nKNOWLEDGE_BASE_ID={kb_id}\n')
    
    print(f"🎉 Created programmatically: {kb_id}")
    return kb_id

if __name__ == "__main__":
    create_simple_opensearch()