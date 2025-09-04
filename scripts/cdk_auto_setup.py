#!/usr/bin/env python3
"""
Automated Knowledge Base setup using CDK approach from AWS Builder article
"""

import boto3
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

class CDKKnowledgeBaseSetup:
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.account_id = boto3.client('sts').get_caller_identity()['Account']
        
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=self.region)
        self.s3 = boto3.client('s3', region_name=self.region)
        self.iam = boto3.client('iam', region_name=self.region)
        
        self.data_bucket_name = os.getenv("S3_VECTOR_BUCKET", "my-jira-vector-store")
        self.kb_name = "jira-tickets-kb"
        self.role_name = "AmazonBedrockExecutionRoleForKnowledgeBase"
        
    def create_iam_role(self):
        """Create IAM role for Knowledge Base (simplified from CDK approach)"""
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
                        "bedrock:InvokeModel",
                        "bedrock:RetrieveAndGenerate",
                        "bedrock:Retrieve"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{self.data_bucket_name}",
                        f"arn:aws:s3:::{self.data_bucket_name}/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "aoss:APIAccessAll"
                    ],
                    "Resource": f"arn:aws:aoss:{self.region}:{self.account_id}:collection/*"
                }
            ]
        }
        
        try:
            self.iam.create_role(
                RoleName=self.role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Role for Bedrock Knowledge Base"
            )
            print(f"✅ Created IAM role: {self.role_name}")
            
            self.iam.put_role_policy(
                RoleName=self.role_name,
                PolicyName="BedrockKnowledgeBasePolicy",
                PolicyDocument=json.dumps(policy_document)
            )
            print("✅ Attached policy to role")
            
            time.sleep(10)  # Wait for role propagation
            
        except Exception as e:
            if 'EntityAlreadyExists' in str(e):
                print(f"✅ IAM role already exists: {self.role_name}")
            else:
                print(f"❌ Error creating IAM role: {e}")
                raise
        
        return f"arn:aws:iam::{self.account_id}:role/{self.role_name}"
    
    def create_knowledge_base_with_opensearch(self, role_arn):
        """Create Knowledge Base with OpenSearch Serverless (like CDK approach)"""
        try:
            # Create with minimal OpenSearch Serverless config
            collection_name = f"kb-{self.kb_name.replace('_', '-')}"
            
            response = self.bedrock_agent.create_knowledge_base(
                name=self.kb_name,
                description="Jira tickets knowledge base with OpenSearch Serverless",
                roleArn=role_arn,
                knowledgeBaseConfiguration={
                    'type': 'VECTOR',
                    'vectorKnowledgeBaseConfiguration': {
                        'embeddingModelArn': f'arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0'
                    }
                },
                storageConfiguration={
                    'type': 'OPENSEARCH_SERVERLESS',
                    'opensearchServerlessConfiguration': {
                        'collectionArn': f'arn:aws:aoss:{self.region}:{self.account_id}:collection/{collection_name}',
                        'vectorIndexName': 'bedrock-knowledge-base-default-index',
                        'fieldMapping': {
                            'vectorField': 'bedrock-knowledge-base-default-vector',
                            'textField': 'AMAZON_BEDROCK_TEXT_CHUNK',
                            'metadataField': 'AMAZON_BEDROCK_METADATA'
                        }
                    }
                }
            )
            
            kb_id = response['knowledgeBase']['knowledgeBaseId']
            print(f"✅ Created Knowledge Base: {kb_id}")
            return kb_id
            
        except Exception as e:
            print(f"❌ Error creating knowledge base: {e}")
            raise
    
    def create_data_source(self, kb_id):
        """Create S3 data source"""
        try:
            response = self.bedrock_agent.create_data_source(
                knowledgeBaseId=kb_id,
                name="jira-tickets-source",
                description="S3 data source for Jira tickets",
                dataSourceConfiguration={
                    'type': 'S3',
                    's3Configuration': {
                        'bucketArn': f'arn:aws:s3:::{self.data_bucket_name}',
                        'inclusionPrefixes': ['jira-tickets/']
                    }
                },
                vectorIngestionConfiguration={
                    'chunkingConfiguration': {
                        'chunkingStrategy': 'FIXED_SIZE',
                        'fixedSizeChunkingConfiguration': {
                            'maxTokens': 500,  # Like CDK example
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
            raise
    
    def start_ingestion(self, kb_id, ds_id):
        """Start ingestion job"""
        try:
            response = self.bedrock_agent.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
                description="Initial ingestion of Jira tickets"
            )
            
            job_id = response['ingestionJob']['ingestionJobId']
            print(f"✅ Started ingestion job: {job_id}")
            return job_id
            
        except Exception as e:
            print(f"❌ Error starting ingestion: {e}")
            raise
    
    def run_complete_setup(self):
        """Run complete automated setup"""
        print("🚀 Starting CDK-style Knowledge Base setup...")
        print("=" * 60)
        
        try:
            # Step 1: Create IAM role
            role_arn = self.create_iam_role()
            
            # Step 2: Create Knowledge Base (auto-creates OpenSearch)
            kb_id = self.create_knowledge_base_with_opensearch(role_arn)
            
            # Step 3: Create Data Source
            ds_id = self.create_data_source(kb_id)
            
            # Step 4: Start ingestion
            job_id = self.start_ingestion(kb_id, ds_id)
            
            print("\n" + "=" * 60)
            print("🎉 SETUP COMPLETE!")
            print("=" * 60)
            print(f"🧠 Knowledge Base ID: {kb_id}")
            print(f"📊 Data Source ID: {ds_id}")
            print(f"⚙️ Ingestion Job ID: {job_id}")
            print(f"🔐 IAM Role: {role_arn}")
            print(f"📁 Data Location: s3://{self.data_bucket_name}/jira-tickets/")
            
            print(f"\n✅ Update your app:")
            print(f"   src/knowledge_base/bedrock_kb.py")
            print(f"   Replace 'YOUR_KB_ID' with: {kb_id}")
            
            print(f"\n📋 Note: Using OpenSearch Serverless (auto-created)")
            print(f"💰 Cost: ~$93/month minimum (4 OCUs)")
            
            return kb_id
            
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            return None

if __name__ == "__main__":
    setup = CDKKnowledgeBaseSetup()
    setup.run_complete_setup()