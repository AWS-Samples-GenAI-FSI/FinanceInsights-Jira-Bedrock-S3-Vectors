#!/usr/bin/env python3

import boto3
import json
import time
from src.s3_vector.s3_vector_store import S3VectorStore

def setup_s3_vector_knowledge_base():
    """Complete setup for S3 Vector Store + Bedrock Knowledge Base"""
    
    # Configuration
    BUCKET_NAME = "lendingtree-jira-s3-vectors"
    KB_NAME = "LendingInsights-S3-Vectors"
    REGION = "us-east-1"
    
    print("🚀 Setting up S3 Vector Store + Bedrock Knowledge Base")
    
    # Initialize clients
    s3_client = boto3.client('s3', region_name=REGION)
    iam_client = boto3.client('iam', region_name=REGION)
    
    # Step 1: Create S3 bucket
    print("\n📦 Step 1: Creating S3 bucket...")
    try:
        s3_client.create_bucket(Bucket=BUCKET_NAME)
        print(f"✅ Bucket created: {BUCKET_NAME}")
    except Exception as e:
        if "BucketAlreadyExists" in str(e):
            print(f"✅ Bucket already exists: {BUCKET_NAME}")
        else:
            print(f"❌ Error creating bucket: {e}")
            return
    
    # Step 2: Enable S3 Vector Engine
    print("\n🔍 Step 2: Enabling S3 Vector Engine...")
    vector_store = S3VectorStore(BUCKET_NAME, REGION)
    vector_store.create_vector_store("LendingInsights-Vectors")
    
    # Step 3: Create IAM role for Bedrock
    print("\n🔐 Step 3: Creating IAM role...")
    role_name = "BedrockS3VectorRole"
    
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
    
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:PutObject",
                    "s3:DeleteObject"
                ],
                "Resource": [
                    f"arn:aws:s3:::{BUCKET_NAME}",
                    f"arn:aws:s3:::{BUCKET_NAME}/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel"
                ],
                "Resource": "*"
            }
        ]
    }
    
    try:
        # Create role
        role_response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for Bedrock to access S3 Vector Store"
        )
        role_arn = role_response['Role']['Arn']
        
        # Attach policy
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="S3VectorAccess",
            PolicyDocument=json.dumps(policy_document)
        )
        
        print(f"✅ IAM role created: {role_arn}")
        
    except Exception as e:
        if "EntityAlreadyExists" in str(e):
            role_arn = f"arn:aws:iam::{boto3.client('sts').get_caller_identity()['Account']}:role/{role_name}"
            print(f"✅ IAM role already exists: {role_arn}")
        else:
            print(f"❌ Error creating IAM role: {e}")
            return
    
    # Wait for IAM propagation
    print("⏳ Waiting for IAM propagation...")
    time.sleep(30)
    
    # Step 4: Create Knowledge Base
    print("\n🧠 Step 4: Creating Bedrock Knowledge Base...")
    kb_response = vector_store.create_knowledge_base_with_s3_vectors(KB_NAME, role_arn)
    
    if kb_response:
        kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
        print(f"✅ Knowledge Base created: {kb_id}")
        
        # Save configuration
        config = {
            "BUCKET_NAME": BUCKET_NAME,
            "KNOWLEDGE_BASE_ID": kb_id,
            "ROLE_ARN": role_arn,
            "REGION": REGION
        }
        
        with open('.env.s3vectors', 'w') as f:
            for key, value in config.items():
                f.write(f"{key}={value}\n")
        
        print(f"\n✅ Setup complete! Configuration saved to .env.s3vectors")
        print(f"📋 Knowledge Base ID: {kb_id}")
        print(f"🪣 S3 Bucket: {BUCKET_NAME}")
        
        return kb_id
    else:
        print("❌ Failed to create Knowledge Base")
        return None

if __name__ == "__main__":
    setup_s3_vector_knowledge_base()