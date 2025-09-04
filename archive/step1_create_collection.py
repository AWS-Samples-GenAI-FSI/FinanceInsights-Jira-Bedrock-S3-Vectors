import boto3
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

def step1_create_collection():
    """Step 1: Create OpenSearch Serverless collection only"""
    
    region = os.getenv('AWS_REGION', 'us-east-1')
    aoss = boto3.client('opensearchserverless', region_name=region)
    
    timestamp = str(int(time.time()))[-6:]
    collection_name = f'jira-{timestamp}'
    
    print(f"Step 1: Creating collection {collection_name}")
    
    # Encryption policy
    aoss.create_security_policy(
        name=f"{collection_name}-enc",
        type='encryption',
        policy=json.dumps({
            "Rules": [{"Resource": [f"collection/{collection_name}"], "ResourceType": "collection"}],
            "AWSOwnedKey": True
        })
    )
    
    # Network policy
    aoss.create_security_policy(
        name=f"{collection_name}-net",
        type='network',
        policy=json.dumps([{
            "Rules": [{"Resource": [f"collection/{collection_name}"], "ResourceType": "collection"}],
            "AllowFromPublic": True
        }])
    )
    
    # Create collection
    aoss.create_collection(name=collection_name, type='VECTORSEARCH')
    print("✅ Collection creation started")
    
    # Wait for active
    while True:
        status = aoss.batch_get_collection(names=[collection_name])
        if status['collectionDetails'][0]['status'] == 'ACTIVE':
            break
        print("⏳ Waiting...")
        time.sleep(15)
    
    collection_id = status['collectionDetails'][0]['id']
    print(f"✅ Collection active: {collection_id}")
    
    # Save details
    with open('collection_details.txt', 'w') as f:
        f.write(f"COLLECTION_NAME={collection_name}\n")
        f.write(f"COLLECTION_ID={collection_id}\n")
    
    print(f"✅ Step 1 complete. Run step2_create_role.py next")
    return collection_name, collection_id

if __name__ == "__main__":
    step1_create_collection()