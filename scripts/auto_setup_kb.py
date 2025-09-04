#!/usr/bin/env python3
"""
Fully automated Bedrock Knowledge Base setup
"""

import boto3
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

class AutoKnowledgeBaseSetup:
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.s3_bucket = os.getenv("S3_VECTOR_BUCKET", "my-jira-vector-store")
        
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=self.region)
        self.iam = boto3.client('iam', region_name=self.region)
        self.s3 = boto3.client('s3', region_name=self.region)
        
        self.account_id = boto3.client('sts').get_caller_identity()['Account']
        self.role_name = "BedrockKnowledgeBaseRole"
        self.kb_name = "jira-tickets-kb"
        
    def create_iam_role(self):
        """Create IAM role for Knowledge Base"""
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
                        f"arn:aws:s3:::{self.s3_bucket}",
                        f"arn:aws:s3:::{self.s3_bucket}/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel"
                    ],
                    "Resource": f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v1"
                }
            ]
        }
        
        try:
            # Create role
            self.iam.create_role(
                RoleName=self.role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Role for Bedrock Knowledge Base"
            )
            print(f"✅ Created IAM role: {self.role_name}")
            
            # Attach policy
            self.iam.put_role_policy(
                RoleName=self.role_name,
                PolicyName="BedrockKnowledgeBasePolicy",
                PolicyDocument=json.dumps(policy_document)
            )
            print("✅ Attached policy to role")
            
            # Wait for role to propagate
            time.sleep(10)
            
        except Exception as e:
            if 'EntityAlreadyExists' in str(e):
                print(f"✅ IAM role already exists: {self.role_name}")
            else:
                print(f"❌ Error creating IAM role: {e}")
                raise
        
        return f"arn:aws:iam::{self.account_id}:role/{self.role_name}"
    
    def create_s3_bucket(self):
        """Create S3 bucket"""
        try:
            if self.region == 'us-east-1':
                self.s3.create_bucket(Bucket=self.s3_bucket)
            else:
                self.s3.create_bucket(
                    Bucket=self.s3_bucket,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            print(f"✅ Created S3 bucket: {self.s3_bucket}")
        except Exception as e:
            if 'BucketAlreadyExists' in str(e) or 'BucketAlreadyOwnedByYou' in str(e):
                print(f"✅ S3 bucket already exists: {self.s3_bucket}")
            else:
                print(f"❌ Error creating S3 bucket: {e}")
                raise
    
    def create_knowledge_base(self, role_arn):
        """Create Knowledge Base with S3 Vectors"""
        try:
            response = self.bedrock_agent.create_knowledge_base(
                name=self.kb_name,
                description="Automated Jira tickets knowledge base",
                roleArn=role_arn,
                knowledgeBaseConfiguration={
                    'type': 'VECTOR',
                    'vectorKnowledgeBaseConfiguration': {
                        'embeddingModelArn': f'arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v1'
                    }
                },
                storageConfiguration={
                    'type': 'OPENSEARCH_SERVERLESS',
                    'opensearchServerlessConfiguration': {
                        'collectionArn': self.create_opensearch_collection(),
                        'vectorIndexName': 'jira-vector-index',
                        'fieldMapping': {
                            'vectorField': 'vector',
                            'textField': 'text',
                            'metadataField': 'metadata'
                        }
                    }
                }
            )
            
            kb_id = response['knowledgeBase']['knowledgeBaseId']
            print(f"✅ Created Knowledge Base: {kb_id}")
            return kb_id
            
        except Exception as e:
            print(f"❌ Error creating knowledge base: {e}")
            return None
    
    def create_opensearch_collection(self):
        """Create OpenSearch Serverless collection"""
        try:
            opensearch = boto3.client('opensearchserverless', region_name=self.region)
            
            collection_name = 'jira-kb-collection'
            
            response = opensearch.create_collection(
                name=collection_name,
                type='VECTORSEARCH',
                description='Vector collection for Jira Knowledge Base'
            )
            
            collection_arn = response['createCollectionDetail']['arn']
            print(f"✅ Created OpenSearch collection: {collection_arn}")
            return collection_arn
            
        except Exception as e:
            print(f"❌ Error creating OpenSearch collection: {e}")
            # Return a placeholder ARN for manual setup
            return f"arn:aws:aoss:{self.region}:{self.account_id}:collection/jira-kb-collection"
    
    def create_data_source(self, kb_id):
        """Create S3 data source"""
        if kb_id == "MANUAL_SETUP_REQUIRED":
            return "MANUAL_SETUP_REQUIRED"
        
        try:
            response = self.bedrock_agent.create_data_source(
                knowledgeBaseId=kb_id,
                name="jira-tickets-source",
                description="S3 data source for Jira tickets",
                dataSourceConfiguration={
                    'type': 'S3',
                    's3Configuration': {
                        'bucketArn': f'arn:aws:s3:::{self.s3_bucket}',
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
            
            ds_id = response['dataSource']['dataSourceId']
            print(f"✅ Created Data Source: {ds_id}")
            return ds_id
            
        except Exception as e:
            print(f"❌ Error creating data source: {e}")
            return None
    
    def run_setup(self):
        """Run complete automated setup"""
        print("🚀 Starting automated Knowledge Base setup...")
        
        # Step 1: Create S3 bucket
        self.create_s3_bucket()
        
        # Step 2: Create IAM role
        role_arn = self.create_iam_role()
        
        # Step 3: Create Knowledge Base
        kb_id = self.create_knowledge_base(role_arn)
        
        # Step 4: Create Data Source
        ds_id = self.create_data_source(kb_id)
        
        print("\n🎉 Setup Summary:")
        print(f"📦 S3 Bucket: {self.s3_bucket}")
        print(f"🔐 IAM Role: {role_arn}")
        print(f"🧠 Knowledge Base ID: {kb_id}")
        print(f"📊 Data Source ID: {ds_id}")
        
        if kb_id != "MANUAL_SETUP_REQUIRED":
            print(f"\n✅ Update your app with KB ID: {kb_id}")
        else:
            print("\n📋 Complete setup manually in AWS Console")
        
        return kb_id

if __name__ == "__main__":
    setup = AutoKnowledgeBaseSetup()
    setup.run_setup()