#!/usr/bin/env python3
"""
Quick setup - upload data and provide exact console steps
"""

import os
from dotenv import load_dotenv
from src.jira.jira_client import JiraClient
from src.knowledge_base.bedrock_kb import BedrockKnowledgeBase

load_dotenv()

def quick_setup():
    print("🚀 Quick Knowledge Base Setup")
    print("=" * 40)
    
    # Step 1: Get Jira tickets
    jira_client = JiraClient(
        os.getenv("JIRA_URL"),
        os.getenv("JIRA_EMAIL"), 
        os.getenv("JIRA_API_TOKEN")
    )
    
    print("📥 Fetching Jira tickets...")
    tickets = jira_client.fetch_recent_tickets(limit=100, days_back=90)
    print(f"✅ Found {len(tickets)} tickets")
    
    # Step 2: Upload to S3
    kb = BedrockKnowledgeBase()
    kb.upload_tickets_to_s3(tickets)
    
    # Step 3: Console instructions
    print("\n" + "="*50)
    print("📋 FINAL STEP - Create Knowledge Base in Console:")
    print("="*50)
    print("\n1. Go to: https://console.aws.amazon.com/bedrock/home#/knowledge-bases")
    print("2. Click 'Create knowledge base'")
    print("3. Enter:")
    print("   - Name: jira-tickets-kb")
    print("   - IAM Role: BedrockKnowledgeBaseRole (already created)")
    print("\n4. Data source:")
    print("   - S3 URI: s3://my-jira-vector-store/jira-tickets/")
    print("   - Chunking: Default (300 tokens, 20% overlap)")
    print("\n5. Embeddings: Titan Embeddings G1 - Text")
    print("6. Vector store: Quick create new vector store")
    print("7. Click Create")
    print("\n8. Copy the Knowledge Base ID and update:")
    print("   src/knowledge_base/bedrock_kb.py line 15")
    print("   Replace 'YOUR_KB_ID' with actual ID")
    
    print(f"\n✅ Ready! {len(tickets)} tickets uploaded to S3")

if __name__ == "__main__":
    quick_setup()