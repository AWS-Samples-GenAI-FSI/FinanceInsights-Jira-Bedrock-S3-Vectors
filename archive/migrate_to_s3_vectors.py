#!/usr/bin/env python3

import boto3
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

def migrate_to_s3_vectors():
    """Complete migration from OpenSearch to S3 Vectors"""
    
    print("🚀 Migrating LendingInsights to S3 Vector Store")
    
    # Configuration
    REGION = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET = "lendingtree-jira-s3-vectors"
    KB_NAME = "LendingInsights-S3-Vectors"
    
    # Initialize clients
    s3_client = boto3.client('s3', region_name=REGION)
    bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)
    iam_client = boto3.client('iam', region_name=REGION)
    sts_client = boto3.client('sts', region_name=REGION)
    
    account_id = sts_client.get_caller_identity()['Account']
    
    print(f"📋 Account: {account_id}")
    print(f"🌍 Region: {REGION}")
    print(f"🪣 S3 Bucket: {S3_BUCKET}")
    
    # Step 1: Create S3 bucket
    print("\n📦 Step 1: Creating S3 bucket...")
    try:
        if REGION == 'us-east-1':
            s3_client.create_bucket(Bucket=S3_BUCKET)
        else:
            s3_client.create_bucket(
                Bucket=S3_BUCKET,
                CreateBucketConfiguration={'LocationConstraint': REGION}
            )
        print(f"✅ S3 bucket created: {S3_BUCKET}")
    except Exception as e:
        if "BucketAlreadyExists" in str(e) or "BucketAlreadyOwnedByYou" in str(e):
            print(f"✅ S3 bucket already exists: {S3_BUCKET}")
        else:
            print(f"❌ Error creating bucket: {e}")
            return False
    
    # Step 2: Create IAM role for Bedrock
    print("\n🔐 Step 2: Creating IAM role...")
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
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:PutObject",
                    "s3:DeleteObject"
                ],
                "Resource": [
                    f"arn:aws:s3:::{S3_BUCKET}",
                    f"arn:aws:s3:::{S3_BUCKET}/*"
                ]
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
    
    # Step 3: Create Knowledge Base with S3 Vector Store
    print("\n🧠 Step 3: Creating Bedrock Knowledge Base with S3 Vectors...")
    
    try:
        kb_response = bedrock_agent.create_knowledge_base(
            name=KB_NAME,
            description="LendingInsights Jira Ticket Analysis with S3 Vector Store",
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
                    'bucketArn': f'arn:aws:s3:::{S3_BUCKET}',
                    'inclusionPrefixes': ['tickets/'],
                    'fieldMapping': {
                        'vectorField': 'bedrock-knowledge-base-default-vector',
                        'textField': 'AMAZON_BEDROCK_TEXT_CHUNK',
                        'metadataField': 'AMAZON_BEDROCK_METADATA'
                    }
                }
            }
        )
        
        kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
        print(f"✅ Knowledge Base created: {kb_id}")
        
    except Exception as e:
        print(f"❌ Error creating Knowledge Base: {e}")
        return False
    
    # Step 4: Create Data Source
    print("\n📊 Step 4: Creating Data Source...")
    
    try:
        ds_response = bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name="JiraTicketsDataSource",
            description="Jira tickets from S3",
            dataSourceConfiguration={
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': f'arn:aws:s3:::{S3_BUCKET}',
                    'inclusionPrefixes': ['tickets/']
                }
            }
        )
        
        ds_id = ds_response['dataSource']['dataSourceId']
        print(f"✅ Data Source created: {ds_id}")
        
    except Exception as e:
        print(f"❌ Error creating Data Source: {e}")
        return False
    
    # Step 5: Update environment configuration
    print("\n⚙️ Step 5: Updating configuration...")
    
    # Update .env file
    env_content = f"""AWS_REGION={REGION}
KNOWLEDGE_BASE_ID={kb_id}
DATA_SOURCE_ID={ds_id}
S3_BUCKET={S3_BUCKET}
ROLE_ARN={role_arn}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print(f"✅ Configuration updated in .env")
    
    # Step 6: Copy existing sample data to new bucket
    print("\n📋 Step 6: Copying sample data...")
    
    try:
        # Check if sample data exists in old location
        old_bucket = "jira-tickets-s3-kb"
        
        try:
            # List objects in old bucket
            response = s3_client.list_objects_v2(Bucket=old_bucket, Prefix='tickets/')
            
            if 'Contents' in response:
                print(f"📦 Found {len(response['Contents'])} files to copy")
                
                # Copy files to new bucket
                for obj in response['Contents']:
                    copy_source = {'Bucket': old_bucket, 'Key': obj['Key']}
                    s3_client.copy_object(
                        CopySource=copy_source,
                        Bucket=S3_BUCKET,
                        Key=obj['Key']
                    )
                
                print(f"✅ Copied {len(response['Contents'])} files to new S3 bucket")
            else:
                print("ℹ️ No existing sample data found")
                
        except Exception as e:
            print(f"ℹ️ Old bucket not accessible: {e}")
            print("ℹ️ Will use fresh data generation")
    
    except Exception as e:
        print(f"⚠️ Error copying data: {e}")
    
    print(f"\n🎉 Migration Complete!")
    print(f"📋 Knowledge Base ID: {kb_id}")
    print(f"📊 Data Source ID: {ds_id}")
    print(f"🪣 S3 Bucket: {S3_BUCKET}")
    print(f"\n▶️ Next steps:")
    print(f"   1. Run: python generate_sample_jira_data.py")
    print(f"   2. Start ingestion in AWS Console")
    print(f"   3. Run: streamlit run app.py")
    
    return True

if __name__ == "__main__":
    migrate_to_s3_vectors()