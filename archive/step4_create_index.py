import boto3
import requests
from requests_aws4auth import AWS4Auth
import json
import os
from dotenv import load_dotenv

load_dotenv()

def step4_create_index():
    """Step 4: Create OpenSearch index"""
    
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    # Read details
    with open('collection_details.txt', 'r') as f:
        lines = f.readlines()
        collection_id = lines[1].strip().split('=')[1]
    
    print(f"Step 4: Creating index in collection {collection_id}")
    
    # Setup auth
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'aoss', session_token=credentials.token)
    
    host = f"{collection_id}.{region}.aoss.amazonaws.com"
    index_name = "bedrock-knowledge-base-default-index"
    index_url = f"https://{host}/{index_name}"
    
    # Index mapping
    index_mapping = {
        "settings": {"index": {"knn": True}},
        "mappings": {
            "properties": {
                "bedrock-knowledge-base-default-vector": {
                    "type": "knn_vector",
                    "dimension": 1536,
                    "method": {"name": "hnsw", "space_type": "cosinesimil", "engine": "nmslib"}
                },
                "AMAZON_BEDROCK_TEXT_CHUNK": {"type": "text"},
                "AMAZON_BEDROCK_METADATA": {"type": "object"}
            }
        }
    }
    
    response = requests.put(index_url, auth=awsauth, json=index_mapping, headers={'Content-Type': 'application/json'})
    
    if response.status_code in [200, 201]:
        print("✅ Index created successfully")
        
        # Update details file
        with open('collection_details.txt', 'a') as f:
            f.write(f"INDEX_NAME={index_name}\n")
        
        print("✅ Step 4 complete. Run step5_create_kb.py next")
        return True
    else:
        print(f"❌ Index creation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    step4_create_index()