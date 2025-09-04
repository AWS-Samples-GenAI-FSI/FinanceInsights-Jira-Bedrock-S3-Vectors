#!/usr/bin/env python3
"""
Final simple setup - upload data and provide exact console steps
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.jira.jira_client import JiraClient
from src.knowledge_base.bedrock_kb import BedrockKnowledgeBase

load_dotenv()

def final_setup():
    print("🚀 Final Simple Knowledge Base Setup")
    print("=" * 50)
    
    # Step 1: Get Jira tickets
    print("📥 Fetching your real Jira tickets...")
    jira_client = JiraClient(
        os.getenv("JIRA_URL"),
        os.getenv("JIRA_EMAIL"), 
        os.getenv("JIRA_API_TOKEN")
    )
    
    tickets = jira_client.fetch_recent_tickets(limit=100, days_back=90)
    print(f"✅ Found {len(tickets)} real tickets from your Jira")
    
    # Step 2: Upload to S3
    print("📤 Uploading to S3...")
    kb = BedrockKnowledgeBase()
    kb.upload_tickets_to_s3(tickets)
    
    # Step 3: Console instructions
    print("\n" + "="*60)
    print("🎯 FINAL STEP - Create Knowledge Base (2 minutes)")
    print("="*60)
    
    print("\n1. Open: https://console.aws.amazon.com/bedrock/home#/knowledge-bases")
    print("2. Click 'Create knowledge base'")
    print("3. Enter:")
    print("   ✅ Name: jira-tickets-kb")
    print("   ✅ IAM Role: AmazonBedrockExecutionRoleForKnowledgeBase (already created)")
    
    print("\n4. Data source:")
    print("   ✅ S3 URI: s3://my-jira-vector-store/jira-tickets/")
    print("   ✅ Chunking: Default (Fixed size)")
    print("   ✅ Max tokens: 300")
    print("   ✅ Overlap: 20%")
    
    print("\n5. Embeddings:")
    print("   ✅ Model: Titan Embeddings G1 - Text v2")
    
    print("\n6. Vector database:")
    print("   ✅ Select: Quick create a new vector store")
    
    print("\n7. Click 'Create knowledge base'")
    print("8. Wait for creation (2-3 minutes)")
    print("9. Copy the Knowledge Base ID")
    print("10. Update src/knowledge_base/bedrock_kb.py line 15:")
    print("    Replace 'YOUR_KB_ID' with the actual ID")
    
    print(f"\n🎉 SUCCESS! Your {len(tickets)} real Jira tickets are ready!")
    print("💰 Cost: ~$93/month (OpenSearch Serverless minimum)")
    print("🚀 After KB creation, run your Streamlit app!")

if __name__ == "__main__":
    final_setup()