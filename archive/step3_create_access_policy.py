import boto3
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

def step3_create_access_policy():
    """Step 3: Create data access policy"""
    
    region = os.getenv('AWS_REGION', 'us-east-1')
    account_id = boto3.client('sts').get_caller_identity()['Account']
    aoss = boto3.client('opensearchserverless', region_name=region)
    
    # Read details
    with open('collection_details.txt', 'r') as f:
        lines = f.readlines()
        collection_name = lines[0].strip().split('=')[1]
        role_name = lines[2].strip().split('=')[1]
    
    print(f"Step 3: Creating access policy for {collection_name}")
    
    # Data access policy
    aoss.create_access_policy(
        name=f"{collection_name}-data",
        type='data',
        policy=json.dumps([{
            "Rules": [
                {"Resource": [f"collection/{collection_name}"], "Permission": ["aoss:CreateCollectionItems", "aoss:UpdateCollectionItems", "aoss:DescribeCollectionItems"], "ResourceType": "collection"},
                {"Resource": [f"index/{collection_name}/*"], "Permission": ["aoss:CreateIndex", "aoss:UpdateIndex", "aoss:DescribeIndex", "aoss:ReadDocument", "aoss:WriteDocument"], "ResourceType": "index"}
            ],
            "Principal": [
                f"arn:aws:iam::{account_id}:role/{role_name}",
                f"arn:aws:iam::{account_id}:root"
            ]
        }])
    )
    
    print("✅ Access policy created")
    print("⏳ Waiting 60 seconds for policy propagation...")
    time.sleep(60)
    print("✅ Step 3 complete. Run step4_create_index.py next")

if __name__ == "__main__":
    step3_create_access_policy()