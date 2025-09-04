import boto3
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

def create_kb_final():
    """Final attempt - let Bedrock create the index automatically"""
    
    region = os.getenv('AWS_REGION', 'us-east-1')
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    aoss = boto3.client('opensearchserverless', region_name=region)
    iam = boto3.client('iam')
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    
    timestamp = str(int(time.time()))[-6:]
    collection_name = f'jira-{timestamp}'
    role_name = f'BedrockKB-{timestamp}'
    
    print(f"Creating KB: {collection_name}")
    
    # 1. Create policies
    aoss.create_security_policy(
        name=f"{collection_name}-enc",
        type='encryption',
        policy=json.dumps({"Rules": [{"Resource": [f"collection/{collection_name}"], "ResourceType": "collection"}], "AWSOwnedKey": True})
    )
    
    aoss.create_security_policy(
        name=f"{collection_name}-net",
        type='network',
        policy=json.dumps([{"Rules": [{"Resource": [f"collection/{collection_name}"], "ResourceType": "collection"}], "AllowFromPublic": True}])
    )
    
    # 2. Create collection
    aoss.create_collection(name=collection_name, type='VECTORSEARCH')
    print("✅ Collection created")
    
    # Wait for active
    while True:
        status = aoss.batch_get_collection(names=[collection_name])
        if status['collectionDetails'][0]['status'] == 'ACTIVE':
            break
        time.sleep(15)
    
    collection_id = status['collectionDetails'][0]['id']
    collection_arn = f"arn:aws:aoss:{region}:{account_id}:collection/{collection_id}"
    print("✅ Collection active")
    
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
        PolicyName='BedrockKBPolicy',
        PolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": ["bedrock:InvokeModel"], "Resource": f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1"},
                {"Effect": "Allow", "Action": ["s3:GetObject", "s3:ListBucket"], "Resource": ["arn:aws:s3:::jira-tickets-s3-kb", "arn:aws:s3:::jira-tickets-s3-kb/*"]},
                {"Effect": "Allow", "Action": ["aoss:APIAccessAll"], "Resource": collection_arn}
            ]
        })
    )
    
    # 4. Data access policy - only for Bedrock role
    aoss.create_access_policy(
        name=f"{collection_name}-data",
        type='data',
        policy=json.dumps([{
            "Rules": [
                {"Resource": [f"collection/{collection_name}"], "Permission": ["aoss:CreateCollectionItems", "aoss:UpdateCollectionItems", "aoss:DescribeCollectionItems"], "ResourceType": "collection"},
                {"Resource": [f"index/{collection_name}/*"], "Permission": ["aoss:CreateIndex", "aoss:UpdateIndex", "aoss:DescribeIndex", "aoss:ReadDocument", "aoss:WriteDocument"], "ResourceType": "index"}
            ],
            "Principal": [f"arn:aws:iam::{account_id}:role/{role_name}"]
        }])
    )
    
    print("✅ Created role and policies")
    
    # 5. Wait longer for propagation
    print("⏳ Waiting for IAM propagation...")
    time.sleep(60)
    
    # 6. Create KB - let Bedrock handle index creation
    try:
        kb_response = bedrock_agent.create_knowledge_base(
            name=f'jira-kb-{timestamp}',
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
                    'vectorIndexName': 'bedrock-knowledge-base-default-index',
                    'fieldMapping': {
                        'vectorField': 'bedrock-knowledge-base-default-vector',
                        'textField': 'AMAZON_BEDROCK_TEXT_CHUNK',
                        'metadataField': 'AMAZON_BEDROCK_METADATA'
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
        
        print(f"🎉 SUCCESS! KB created: {kb_id}")
        return kb_id
        
    except Exception as e:
        print(f"❌ KB creation failed: {e}")
        return None

if __name__ == "__main__":
    create_kb_final()