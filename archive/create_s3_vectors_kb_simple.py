#!/usr/bin/env python3

import boto3
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

def create_s3_vectors_kb():
    """Create S3 Vectors Knowledge Base - Simplified approach"""
    
    print("🚀 Creating S3 Vectors Knowledge Base")
    
    # Configuration
    REGION = os.getenv("AWS_REGION", "us-east-1")
    VECTOR_BUCKET = "lendingtree-jira-vectors"
    INDEX_NAME = "jira-tickets-index"
    KB_NAME = "LendingInsights-S3-Vectors"
    
    # Initialize clients
    bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)
    iam_client = boto3.client('iam', region_name=REGION)
    sts_client = boto3.client('sts', region_name=REGION)
    
    account_id = sts_client.get_caller_identity()['Account']
    
    print(f"📋 Account: {account_id}")
    print(f"🌍 Region: {REGION}")
    print(f"🪣 Vector Bucket: {VECTOR_BUCKET}")
    
    # Step 1: Create IAM role for Bedrock
    print("\n🔐 Step 1: Creating IAM role...")
    role_name = "BedrockS3VectorRole"
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "bedrock.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    s3_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3vectors:*"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel"],
                "Resource": "*"
            }
        ]
    }
    
    try:
        # Create role
        iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for Bedrock S3 Vector Store access"
        )
        
        # Attach inline policy
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="S3VectorAccess",
            PolicyDocument=json.dumps(s3_policy)
        )
        
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        print(f"✅ IAM role created: {role_arn}")
        
    except Exception as e:
        if "EntityAlreadyExists" in str(e):
            role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
            print(f"✅ IAM role already exists: {role_arn}")
        else:
            print(f"❌ Error creating IAM role: {e}")
            return False
    
    # Step 2: Create Knowledge Base with S3 Vectors (minimal config)
    print("\n🧠 Step 2: Creating Bedrock Knowledge Base...")
    
    try:
        kb_response = bedrock_agent.create_knowledge_base(
            name=KB_NAME,
            description="LendingInsights with S3 Vector Store",
            roleArn=role_arn,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f'arn:aws:bedrock:{REGION}::foundation-model/amazon.titan-embed-text-v1'
                }
            },
            storageConfiguration={
                'type': 'S3',
                's3VectorsConfiguration': {
                    'vectorBucketArn': f'arn:aws:s3vectors::{account_id}:bucket/{VECTOR_BUCKET}',
                    'indexName': INDEX_NAME
                }
            }
        )
        
        kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
        print(f"✅ Knowledge Base created: {kb_id}")
        
    except Exception as e:
        print(f"❌ Error creating Knowledge Base: {e}")
        print(f"Error details: {str(e)}")
        
        # Try alternative approach - use existing OpenSearch for now
        print("\n🔄 S3 Vectors not available, keeping existing OpenSearch KB")
        return False
    
    # Step 3: Update environment configuration
    print("\n⚙️ Step 3: Updating configuration...")
    
    # Update .env file
    env_content = f"""AWS_REGION={REGION}
KNOWLEDGE_BASE_ID={kb_id}
VECTOR_BUCKET={VECTOR_BUCKET}
INDEX_NAME={INDEX_NAME}
ROLE_ARN={role_arn}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print(f"✅ Configuration updated in .env")
    
    print(f"\n🎉 S3 Vectors KB Setup Complete!")
    print(f"📋 Knowledge Base ID: {kb_id}")
    print(f"🪣 Vector Bucket: {VECTOR_BUCKET}")
    print(f"📊 Index Name: {INDEX_NAME}")
    
    return True

if __name__ == "__main__":
    success = create_s3_vectors_kb()
    if not success:
        print("\n⚠️ S3 Vectors setup failed - keeping existing OpenSearch KB")
        print("💡 S3 Vectors is in preview and may not be available in all regions")