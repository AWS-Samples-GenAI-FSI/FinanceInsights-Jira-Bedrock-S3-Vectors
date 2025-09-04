import boto3
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

def create_opensearch_working():
    """Create OpenSearch KB following AWS sample pattern"""
    
    region = os.getenv('AWS_REGION', 'us-east-1')
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    aoss = boto3.client('opensearchserverless', region_name=region)
    iam = boto3.client('iam')
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    
    collection_name = f'jira-kb-{int(time.time())}'
    role_name = f'AmazonBedrockExecutionRoleForKnowledgeBase_{collection_name}'
    
    # 1. Create encryption policy
    encryption_policy = {
        "Rules": [
            {
                "Resource": [f"collection/{collection_name}"],
                "ResourceType": "collection"
            }
        ],
        "AWSOwnedKey": True
    }
    
    aoss.create_security_policy(
        name=f"{collection_name}-encryption",
        type='encryption',
        policy=json.dumps(encryption_policy)
    )
    
    # 2. Create network policy  
    network_policy = [
        {
            "Rules": [
                {
                    "Resource": [f"collection/{collection_name}"],
                    "ResourceType": "collection"
                }
            ],
            "AllowFromPublic": True
        }
    ]
    
    aoss.create_security_policy(
        name=f"{collection_name}-network", 
        type='network',
        policy=json.dumps(network_policy)
    )
    
    # 3. Create collection
    collection_response = aoss.create_collection(
        name=collection_name,
        type='VECTORSEARCH'
    )
    print(f"✅ Created collection: {collection_name}")
    
    # Wait for collection to be active
    while True:
        status = aoss.batch_get_collection(names=[collection_name])
        if status['collectionDetails'][0]['status'] == 'ACTIVE':
            break
        time.sleep(10)
    
    collection_id = status['collectionDetails'][0]['id']
    collection_arn = f"arn:aws:aoss:{region}:{account_id}:collection/{collection_id}"
    
    # 4. Create IAM role
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description='Execution role for Bedrock Knowledge Base'
    )
    
    # 5. Create inline policy for role
    inline_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel"
                ],
                "Resource": f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1"
            },
            {
                "Effect": "Allow", 
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::jira-tickets-s3-kb",
                    "arn:aws:s3:::jira-tickets-s3-kb/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "aoss:APIAccessAll"
                ],
                "Resource": collection_arn
            }
        ]
    }
    
    iam.put_role_policy(
        RoleName=role_name,
        PolicyName='BedrockKnowledgeBasePolicy',
        PolicyDocument=json.dumps(inline_policy)
    )
    
    # 6. Create data access policy
    data_access_policy = [
        {
            "Rules": [
                {
                    "Resource": [f"collection/{collection_name}"],
                    "Permission": [
                        "aoss:CreateCollectionItems",
                        "aoss:DeleteCollectionItems",
                        "aoss:UpdateCollectionItems",
                        "aoss:DescribeCollectionItems"
                    ],
                    "ResourceType": "collection"
                },
                {
                    "Resource": [f"index/{collection_name}/*"],
                    "Permission": [
                        "aoss:CreateIndex",
                        "aoss:DeleteIndex", 
                        "aoss:UpdateIndex",
                        "aoss:DescribeIndex",
                        "aoss:ReadDocument",
                        "aoss:WriteDocument"
                    ],
                    "ResourceType": "index"
                }
            ],
            "Principal": [
                f"arn:aws:iam::{account_id}:role/{role_name}",
                f"arn:aws:iam::{account_id}:root"
            ]
        }
    ]
    
    aoss.create_access_policy(
        name=f"{collection_name}-access",
        type='data',
        policy=json.dumps(data_access_policy)
    )
    
    print("✅ Created policies and role")
    
    # Wait for IAM propagation
    time.sleep(30)
    
    # 7. Create index
    import requests
    from requests_aws4auth import AWS4Auth
    
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'aoss', session_token=credentials.token)
    
    host = f"{collection_id}.{region}.aoss.amazonaws.com"
    index_url = f"https://{host}/bedrock-knowledge-base-default-index"
    
    index_mapping = {
        "settings": {
            "index": {
                "knn": True
            }
        },
        "mappings": {
            "properties": {
                "bedrock-knowledge-base-default-vector": {
                    "type": "knn_vector",
                    "dimension": 1536,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "nmslib"
                    }
                },
                "AMAZON_BEDROCK_TEXT_CHUNK": {
                    "type": "text"
                },
                "AMAZON_BEDROCK_METADATA": {
                    "type": "object"
                }
            }
        }
    }
    
    response = requests.put(index_url, auth=awsauth, json=index_mapping, headers={'Content-Type': 'application/json'})
    print(f"Index creation response: {response.status_code}")
    
    if response.status_code not in [200, 201]:
        print(f"Index creation failed: {response.text}")
        return None
    
    print("✅ Created index")
    time.sleep(10)
    
    # 8. Create Knowledge Base
    kb_config = {
        'name': f'jira-kb-{collection_name}',
        'description': 'Jira tickets knowledge base',
        'roleArn': f'arn:aws:iam::{account_id}:role/{role_name}',
        'knowledgeBaseConfiguration': {
            'type': 'VECTOR',
            'vectorKnowledgeBaseConfiguration': {
                'embeddingModelArn': f'arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1'
            }
        },
        'storageConfiguration': {
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
    }
    
    kb_response = bedrock_agent.create_knowledge_base(**kb_config)
    kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
    print(f"✅ Created Knowledge Base: {kb_id}")
    
    # 9. Create data source
    ds_config = {
        'knowledgeBaseId': kb_id,
        'name': 'jira-tickets-datasource',
        'dataSourceConfiguration': {
            'type': 'S3',
            's3Configuration': {
                'bucketArn': 'arn:aws:s3:::jira-tickets-s3-kb'
            }
        }
    }
    
    ds_response = bedrock_agent.create_data_source(**ds_config)
    ds_id = ds_response['dataSource']['dataSourceId']
    print(f"✅ Created data source: {ds_id}")
    
    # 10. Start ingestion
    bedrock_agent.start_ingestion_job(
        knowledgeBaseId=kb_id,
        dataSourceId=ds_id
    )
    print("✅ Started ingestion job")
    
    # Save to .env
    with open('.env', 'a') as f:
        f.write(f'\nKNOWLEDGE_BASE_ID={kb_id}\n')
    
    print(f"🎉 Setup complete! KB ID: {kb_id}")
    return kb_id

if __name__ == "__main__":
    create_opensearch_working()