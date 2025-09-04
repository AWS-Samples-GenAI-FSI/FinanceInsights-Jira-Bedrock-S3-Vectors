import boto3
import requests
from requests_aws4auth import AWS4Auth
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

def fix_ingestion():
    """Fix ingestion by deleting and recreating KB with correct index"""
    
    region = os.getenv('AWS_REGION', 'us-east-1')
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    
    # Delete current KB
    try:
        bedrock_agent.delete_knowledge_base(knowledgeBaseId='ICK71UCFE6')
        print("✅ Deleted old KB")
        time.sleep(10)
    except:
        pass
    
    # Read collection details
    with open('collection_details.txt', 'r') as f:
        lines = f.readlines()
        collection_name = lines[0].strip().split('=')[1]
        collection_id = lines[1].strip().split('=')[1]
        role_arn = lines[3].strip().split('=')[1]
    
    collection_arn = f"arn:aws:aoss:{region}:{account_id}:collection/{collection_id}"
    
    # Delete all indices
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'aoss', session_token=credentials.token)
    host = f"{collection_id}.{region}.aoss.amazonaws.com"
    
    for index in ['bedrock-knowledge-base-default-index', 'bedrock-kb-faiss-index']:
        requests.delete(f"https://{host}/{index}", auth=awsauth)
    
    print("✅ Deleted indices")
    time.sleep(10)
    
    # Create simple index
    index_url = f"https://{host}/simple-index"
    simple_mapping = {
        "mappings": {
            "properties": {
                "vector": {"type": "knn_vector", "dimension": 1536, "method": {"name": "hnsw", "engine": "faiss"}},
                "text": {"type": "text"},
                "metadata": {"type": "text"}
            }
        }
    }
    
    response = requests.put(index_url, auth=awsauth, json=simple_mapping, headers={'Content-Type': 'application/json'})
    print(f"Index creation: {response.status_code}")
    
    # Create new KB
    kb_response = bedrock_agent.create_knowledge_base(
        name=f'jira-simple-{int(time.time())}',
        roleArn=role_arn,
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
                'vectorIndexName': 'simple-index',
                'fieldMapping': {
                    'vectorField': 'vector',
                    'textField': 'text',
                    'metadataField': 'metadata'
                }
            }
        }
    )
    
    kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
    print(f"✅ Created new KB: {kb_id}")
    
    # Create data source
    ds_response = bedrock_agent.create_data_source(
        knowledgeBaseId=kb_id,
        name='jira-data',
        dataSourceConfiguration={'type': 'S3', 's3Configuration': {'bucketArn': 'arn:aws:s3:::jira-tickets-s3-kb'}}
    )
    
    # Start ingestion
    bedrock_agent.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_response['dataSource']['dataSourceId'])
    print("✅ Started ingestion")
    
    # Update .env
    with open('.env', 'w') as f:
        f.write(f'AWS_REGION={region}\n')
        f.write(f'KNOWLEDGE_BASE_ID={kb_id}\n')
    
    print(f"🎉 Fixed KB: {kb_id}")
    print("⏳ Wait 3 minutes then test")

if __name__ == "__main__":
    fix_ingestion()