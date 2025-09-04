#!/usr/bin/env python3
"""
Automated S3 Vectors + Bedrock Knowledge Base setup based on AWS blog
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

class S3VectorsAutoSetup:
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.account_id = boto3.client('sts').get_caller_identity()['Account']
        
        # Clients
        self.s3vectors = boto3.client('s3vectors', region_name=self.region)
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=self.region)
        self.s3 = boto3.client('s3', region_name=self.region)
        self.iam = boto3.client('iam', region_name=self.region)
        
        # Configuration
        self.vector_bucket_name = "jira-vector-bucket"
        self.vector_index_name = "jira-vector-index"
        self.data_bucket_name = os.getenv("S3_VECTOR_BUCKET", "my-jira-vector-store")
        self.kb_name = "jira-tickets-kb"
        self.role_name = "BedrockKnowledgeBaseS3VectorsRole"
        
    def create_s3_vector_bucket(self):
        """Create S3 Vector bucket"""
        try:
            response = self.s3vectors.create_vector_bucket(
                vectorBucketName=self.vector_bucket_name
            )
            print(f"✅ Created S3 Vector bucket: {self.vector_bucket_name}")
            # Return constructed ARN since response format may vary
            return f"arn:aws:s3vectors:{self.region}:{self.account_id}:bucket/{self.vector_bucket_name}"
        except Exception as e:
            if 'already exists' in str(e).lower():
                print(f"✅ S3 Vector bucket already exists: {self.vector_bucket_name}")
                return f"arn:aws:s3vectors:{self.region}:{self.account_id}:bucket/{self.vector_bucket_name}"
            else:
                print(f"❌ Error creating S3 Vector bucket: {e}")
                raise
    
    def create_s3_vector_index(self):
        """Create S3 Vector index with proper metadata configuration"""
        try:
            response = self.s3vectors.create_index(
                vectorBucketName=self.vector_bucket_name,
                indexName=self.vector_index_name,
                dimension=1024,  # Titan v2 dimension
                distanceMetric="cosine",
                dataType="float32",
                metadataConfiguration={
                    "nonFilterableMetadataKeys": ["AMAZON_BEDROCK_TEXT"]
                }
            )
            print(f"✅ Created S3 Vector index: {self.vector_index_name}")
            # Return constructed ARN
            return f"arn:aws:s3vectors:{self.region}:{self.account_id}:bucket/{self.vector_bucket_name}/index/{self.vector_index_name}"
        except Exception as e:
            if 'already exists' in str(e).lower():
                print(f"✅ S3 Vector index already exists: {self.vector_index_name}")
                return f"arn:aws:s3vectors:{self.region}:{self.account_id}:bucket/{self.vector_bucket_name}/index/{self.vector_index_name}"
            else:
                print(f"❌ Error creating S3 Vector index: {e}")
                raise
    
    def create_iam_role(self):
        """Create IAM role with S3 Vectors permissions"""
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
        
        # Policy from AWS blog post
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "BedrockInvokeModelPermission",
                    "Effect": "Allow",
                    "Action": ["bedrock:InvokeModel"],
                    "Resource": [f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0"]
                },
                {
                    "Sid": "S3ListBucketPermission",
                    "Effect": "Allow",
                    "Action": ["s3:ListBucket"],
                    "Resource": [f"arn:aws:s3:::{self.data_bucket_name}"],
                    "Condition": {
                        "StringEquals": {"aws:ResourceAccount": [self.account_id]}
                    }
                },
                {
                    "Sid": "S3GetObjectPermission",
                    "Effect": "Allow",
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self.data_bucket_name}/jira-tickets/*"],
                    "Condition": {
                        "StringEquals": {"aws:ResourceAccount": [self.account_id]}
                    }
                },
                {
                    "Sid": "S3VectorsAccessPermission",
                    "Effect": "Allow",
                    "Action": [
                        "s3vectors:GetIndex",
                        "s3vectors:QueryVectors", 
                        "s3vectors:PutVectors",
                        "s3vectors:GetVectors",
                        "s3vectors:DeleteVectors"
                    ],
                    "Resource": f"arn:aws:s3vectors:{self.region}:{self.account_id}:bucket/{self.vector_bucket_name}/index/{self.vector_index_name}",
                    "Condition": {
                        "StringEquals": {"aws:ResourceAccount": self.account_id}
                    }
                }
            ]
        }
        
        try:
            # Create role
            self.iam.create_role(
                RoleName=self.role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Role for Bedrock Knowledge Base with S3 Vectors"
            )
            print(f"✅ Created IAM role: {self.role_name}")
            
            # Attach policy
            self.iam.put_role_policy(
                RoleName=self.role_name,
                PolicyName="S3VectorsKnowledgeBasePolicy",
                PolicyDocument=json.dumps(policy_document)
            )
            print("✅ Attached S3 Vectors policy to role")
            
            time.sleep(10)  # Wait for role propagation
            
        except Exception as e:
            if 'EntityAlreadyExists' in str(e):
                print(f"✅ IAM role already exists: {self.role_name}")
            else:
                print(f"❌ Error creating IAM role: {e}")
                raise
        
        return f"arn:aws:iam::{self.account_id}:role/{self.role_name}"
    
    def create_knowledge_base(self, role_arn, vector_index_arn):
        """Create Knowledge Base with S3 Vectors - exact API from blog"""
        try:
            response = self.bedrock_agent.create_knowledge_base(
                description='Amazon Bedrock Knowledge Base integrated with Amazon S3 Vectors',
                knowledgeBaseConfiguration={
                    'type': 'VECTOR',
                    'vectorKnowledgeBaseConfiguration': {
                        'embeddingModelArn': f'arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0',
                        'embeddingModelConfiguration': {
                            'bedrockEmbeddingModelConfiguration': {
                                'dimensions': 1024,  # Titan v2 dimensions
                                'embeddingDataType': 'FLOAT32'
                            }
                        },
                    },
                },
                name=self.kb_name,
                roleArn=role_arn,
                storageConfiguration={
                    's3VectorsConfiguration': {
                        'indexArn': vector_index_arn
                    },
                    'type': 'S3_VECTORS'
                }
            )
            
            kb_id = response['knowledgeBase']['knowledgeBaseId']
            print(f"✅ Created Knowledge Base: {kb_id}")
            return kb_id
            
        except Exception as e:
            print(f"❌ Error creating knowledge base: {e}")
            raise
    
    def upload_jira_data(self):
        """Upload Jira tickets to S3"""
        print("📥 Fetching Jira tickets...")
        
        jira_client = JiraClient(
            os.getenv("JIRA_URL"),
            os.getenv("JIRA_EMAIL"), 
            os.getenv("JIRA_API_TOKEN")
        )
        
        tickets = jira_client.fetch_recent_tickets(limit=100, days_back=90)
        print(f"✅ Found {len(tickets)} tickets")
        
        # Create data bucket
        try:
            if self.region == 'us-east-1':
                self.s3.create_bucket(Bucket=self.data_bucket_name)
            else:
                self.s3.create_bucket(
                    Bucket=self.data_bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            print(f"✅ Created data bucket: {self.data_bucket_name}")
        except Exception as e:
            if 'BucketAlreadyExists' in str(e) or 'BucketAlreadyOwnedByYou' in str(e):
                print(f"✅ Data bucket already exists: {self.data_bucket_name}")
        
        # Upload tickets
        for i, ticket in enumerate(tickets):
            content = f"""Title: {ticket.get('summary', 'No title')}
Key: {ticket.get('key', 'Unknown')}
Status: {ticket.get('status', 'Unknown')}
Priority: {ticket.get('priority', 'Unknown')}
Assignee: {ticket.get('assignee', 'Unassigned')}
Component: {ticket.get('component', 'Unknown')}
Created: {ticket.get('created', 'Unknown')}

Description:
{self._extract_description_text(ticket.get('description', 'No description'))}
"""
            
            key = f"jira-tickets/ticket_{ticket.get('key', i)}.txt"
            
            self.s3.put_object(
                Bucket=self.data_bucket_name,
                Key=key,
                Body=content.encode('utf-8'),
                ContentType='text/plain'
            )
        
        print(f"✅ Uploaded {len(tickets)} tickets to S3")
        return len(tickets)
    
    def _extract_description_text(self, description) -> str:
        """Extract plain text from description"""
        if not description:
            return 'No description provided'
        
        if isinstance(description, str):
            return description
        
        if isinstance(description, dict) and description.get('type') == 'doc':
            text_parts = []
            content = description.get('content', [])
            
            for block in content:
                if block.get('type') == 'paragraph':
                    paragraph_content = block.get('content', [])
                    for item in paragraph_content:
                        if item.get('type') == 'text':
                            text_parts.append(item.get('text', ''))
            
            return ' '.join(text_parts)
        
        return str(description)
    
    def run_complete_setup(self):
        """Run complete automated setup"""
        print("🚀 Starting complete S3 Vectors + Knowledge Base setup...")
        print("=" * 60)
        
        try:
            # Step 1: Upload Jira data
            ticket_count = self.upload_jira_data()
            
            # Step 2: Create S3 Vector bucket
            vector_bucket_arn = self.create_s3_vector_bucket()
            
            # Step 3: Create S3 Vector index
            vector_index_arn = self.create_s3_vector_index()
            
            # Step 4: Create IAM role
            role_arn = self.create_iam_role()
            
            # Step 5: Create Knowledge Base
            kb_id = self.create_knowledge_base(role_arn, vector_index_arn)
            
            print("\n" + "=" * 60)
            print("🎉 SETUP COMPLETE!")
            print("=" * 60)
            print(f"📊 Uploaded: {ticket_count} Jira tickets")
            print(f"🪣 Vector Bucket: {self.vector_bucket_name}")
            print(f"📇 Vector Index: {self.vector_index_name}")
            print(f"🧠 Knowledge Base ID: {kb_id}")
            print(f"🔐 IAM Role: {role_arn}")
            
            print(f"\n✅ Update your app:")
            print(f"   src/knowledge_base/bedrock_kb.py")
            print(f"   Replace 'YOUR_KB_ID' with: {kb_id}")
            
            return kb_id
            
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            return None

if __name__ == "__main__":
    setup = S3VectorsAutoSetup()
    setup.run_complete_setup()