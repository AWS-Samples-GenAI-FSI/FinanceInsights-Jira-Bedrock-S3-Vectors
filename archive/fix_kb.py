import boto3
import requests
from requests_aws4auth import AWS4Auth
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

def fix_kb():
    """Fix KB by recreating index with correct mapping"""
    
    region = os.getenv('AWS_REGION', 'us-east-1')
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    
    # Read collection details
    with open('collection_details.txt', 'r') as f:
        lines = f.readlines()
        collection_id = lines[1].strip().split('=')[1]
    
    # Setup auth
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'aoss', session_token=credentials.token)
    
    host = f"{collection_id}.{region}.aoss.amazonaws.com"
    
    # Delete old index
    old_index_url = f"https://{host}/bedrock-kb-faiss-index"
    requests.delete(old_index_url, auth=awsauth)
    print("✅ Deleted old index")
    
    time.sleep(5)
    
    # Create new index with minimal mapping
    new_index_url = f"https://{host}/bedrock-knowledge-base-default-index"
    
    index_mapping = {
        "settings": {"index": {"knn": True}},
        "mappings": {
            "properties": {
                "bedrock-knowledge-base-default-vector": {
                    "type": "knn_vector",
                    "dimension": 1536,
                    "method": {"name": "hnsw", "space_type": "cosinesimil", "engine": "faiss"}
                },
                "AMAZON_BEDROCK_TEXT_CHUNK": {"type": "text"},
                "AMAZON_BEDROCK_METADATA": {"type": "text"}
            }
        }
    }
    
    response = requests.put(new_index_url, auth=awsauth, json=index_mapping, headers={'Content-Type': 'application/json'})
    
    if response.status_code in [200, 201]:
        print("✅ Created new index")
        
        # Restart ingestion
        kb_id = 'ICK71UCFE6'
        ds_response = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
        ds_id = ds_response['dataSourceSummaries'][0]['dataSourceId']
        bedrock_agent.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id)
        print("✅ Restarted ingestion")
        print("⏳ Wait 3 minutes then test")
        
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    fix_kb()