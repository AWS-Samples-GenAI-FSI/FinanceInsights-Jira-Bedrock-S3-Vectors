#!/usr/bin/env python3
"""
Setup Bedrock Knowledge Base with S3 data source
"""

import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

def setup_knowledge_base():
    """Setup Knowledge Base through AWS Console instructions"""
    
    s3_bucket = os.getenv("S3_VECTOR_BUCKET", "my-jira-vector-store")
    region = os.getenv("AWS_REGION", "us-east-1")
    
    print("🚀 Setting up Bedrock Knowledge Base")
    print("=" * 50)
    
    print("\n📋 Manual Setup Steps:")
    print("\n1. Go to AWS Bedrock Console > Knowledge bases")
    print("2. Click 'Create knowledge base'")
    print("3. Configure:")
    print(f"   - Name: jira-tickets-kb")
    print(f"   - Description: Jira tickets RAG system")
    print(f"   - IAM Role: Create new service role")
    
    print("\n4. Data source configuration:")
    print(f"   - Data source name: jira-tickets-source")
    print(f"   - S3 URI: s3://{s3_bucket}/jira-tickets/")
    print(f"   - Chunking: Default chunking")
    print(f"   - Max tokens: 300")
    print(f"   - Overlap: 20%")
    
    print("\n5. Embeddings model:")
    print(f"   - Select: Titan Embeddings G1 - Text")
    
    print("\n6. Vector database:")
    print(f"   - Select: Amazon S3 (Preview)")
    print(f"   - S3 bucket: {s3_bucket}")
    print(f"   - Key prefix: vectors/")
    
    print("\n7. Review and create")
    
    print("\n8. Note: S3 Vectors is in preview - may need to enable in console")
    print("\n9. After creation, copy the Knowledge Base ID")
    print("9. Update src/knowledge_base/bedrock_kb.py:")
    print("   - Replace 'YOUR_KB_ID' with actual KB ID")
    
    print(f"\n✅ Data is ready at: s3://{s3_bucket}/jira-tickets/")
    print("📊 Run the Streamlit app after KB creation is complete!")

if __name__ == "__main__":
    setup_knowledge_base()