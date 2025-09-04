#!/usr/bin/env python3
"""
Final automated S3 Vectors Knowledge Base setup
"""

import boto3
import json
import os
import sys
import time
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.jira.jira_client import JiraClient

load_dotenv()

def create_knowledge_base_with_s3_vectors():
    """Create Knowledge Base with S3 Vectors - fully automated"""
    
    region = os.getenv("AWS_REGION", "us-east-1")
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    s3vectors = boto3.client('s3vectors', region_name=region)
    s3 = boto3.client('s3', region_name=region)
    iam = boto3.client('iam', region_name=region)
    
    data_bucket = os.getenv("S3_VECTOR_BUCKET", "my-jira-vector-store")
    vector_bucket = "jira-kb-vectors"
    vector_index = "jira-index"
    kb_name = "jira-s3-vectors-kb"
    role_name = "BedrockS3VectorsRole"
    
    print("🚀 Creating Knowledge Base with S3 Vectors...")
    
    try:
        # Step 1: Upload Jira data
        print("📥 Uploading Jira tickets...")
        jira_client = JiraClient(
            os.getenv("JIRA_URL"),
            os.getenv("JIRA_EMAIL"), 
            os.getenv("JIRA_API_TOKEN")
        )
        tickets = jira_client.fetch_recent_tickets(limit=50, days_back=90)
        
        # Create data bucket
        try:
            s3.create_bucket(Bucket=data_bucket)
        except:
            pass  # Already exists
        
        # Upload tickets
        for i, ticket in enumerate(tickets):
            content = f"""Title: {ticket.get('summary', 'No title')}
Key: {ticket.get('key', 'Unknown')}
Status: {ticket.get('status', 'Unknown')}
Priority: {ticket.get('priority', 'Unknown')}

Description:
{ticket.get('description', 'No description')}"""
            
            s3.put_object(
                Bucket=data_bucket,
                Key=f"jira-tickets/ticket_{i}.txt",
                Body=content.encode('utf-8')
            )
        
        print(f"✅ Uploaded {len(tickets)} tickets")
        
        # Step 2: Create S3 Vector bucket and index
        print("🪣 Creating S3 Vector store...")
        try:
            s3vectors.create_vector_bucket(vectorBucketName=vector_bucket)
        except:
            pass  # Already exists
        
        try:
            s3vectors.create_index(
                vectorBucketName=vector_bucket,
                indexName=vector_index,
                dimension=1024,  # Titan v2
                distanceMetric="cosine",
                dataType="float32",
                metadataConfiguration={
                    "nonFilterableMetadataKeys": ["AMAZON_BEDROCK_TEXT"]
                }
            )
        except:
            pass  # Already exists
        
        print("✅ S3 Vector store ready")
        
        # Step 3: Create IAM role
        print("🔐 Creating IAM role...")
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "bedrock.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }
        
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["bedrock:InvokeModel"],
                    "Resource": f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v2:0"
                },
                {
                    "Effect": "Allow",
                    "Action": ["s3:GetObject", "s3:ListBucket"],
                    "Resource": [f"arn:aws:s3:::{data_bucket}", f"arn:aws:s3:::{data_bucket}/*"]
                },
                {
                    "Effect": "Allow",
                    "Action": ["s3vectors:*"],
                    "Resource": f"arn:aws:s3vectors:{region}:{account_id}:bucket/{vector_bucket}/index/{vector_index}"
                }
            ]
        }
        
        try:
            iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy)
            )
            iam.put_role_policy(
                RoleName=role_name,
                PolicyName="S3VectorsPolicy",
                PolicyDocument=json.dumps(policy)
            )
            time.sleep(10)
        except:
            pass  # Already exists
        
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        print("✅ IAM role ready")
        
        # Step 4: Create Knowledge Base
        print("🧠 Creating Knowledge Base...")
        response = bedrock_agent.create_knowledge_base(
            name=kb_name,
            description="Jira tickets with S3 Vectors",
            roleArn=role_arn,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f'arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v2:0'
                }
            },
            storageConfiguration={
                'type': 'S3_VECTORS',
                's3VectorsConfiguration': {
                    'indexArn': f'arn:aws:s3vectors:{region}:{account_id}:bucket/{vector_bucket}/index/{vector_index}'
                }
            }
        )
        
        kb_id = response['knowledgeBase']['knowledgeBaseId']
        print(f"✅ Knowledge Base created: {kb_id}")
        
        # Step 5: Create data source
        print("📊 Creating data source...")
        ds_response = bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name="jira-source",
            dataSourceConfiguration={
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': f'arn:aws:s3:::{data_bucket}',
                    'inclusionPrefixes': ['jira-tickets/']
                }
            },
            vectorIngestionConfiguration={
                'chunkingConfiguration': {
                    'chunkingStrategy': 'FIXED_SIZE',
                    'fixedSizeChunkingConfiguration': {
                        'maxTokens': 300,
                        'overlapPercentage': 20
                    }
                }
            }
        )
        
        ds_id = ds_response['dataSource']['dataSourceId']
        print(f"✅ Data source created: {ds_id}")
        
        # Step 6: Start ingestion
        print("⚙️ Starting ingestion...")
        bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id
        )
        
        print("\n" + "="*50)
        print("🎉 SUCCESS! Knowledge Base with S3 Vectors created!")
        print("="*50)
        print(f"🧠 Knowledge Base ID: {kb_id}")
        print(f"📊 Data Source ID: {ds_id}")
        print(f"🪣 Vector Bucket: {vector_bucket}")
        print(f"📇 Vector Index: {vector_index}")
        print(f"📁 Data: s3://{data_bucket}/jira-tickets/")
        
        print(f"\n✅ Update your app:")
        print(f"   src/knowledge_base/bedrock_kb.py")
        print(f"   Replace 'YOUR_KB_ID' with: {kb_id}")
        
        return kb_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    create_knowledge_base_with_s3_vectors()