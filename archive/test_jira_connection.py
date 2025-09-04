#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from src.jira.jira_client import JiraClient

# Load environment variables
load_dotenv()

def test_jira_connection():
    """Test Jira connection with stored credentials"""
    
    print("🔍 Testing Jira Connection")
    
    # Get credentials from .env
    jira_url = os.getenv('JIRA_URL')
    jira_email = os.getenv('JIRA_EMAIL') 
    jira_token = os.getenv('JIRA_API_TOKEN')
    
    print(f"📋 Jira URL: {jira_url}")
    print(f"📧 Email: {jira_email}")
    print(f"🔑 Token: {jira_token[:20]}..." if jira_token else "❌ No token")
    
    if not all([jira_url, jira_email, jira_token]):
        print("❌ Missing Jira credentials in .env file")
        return False
    
    try:
        # Initialize Jira client
        jira_client = JiraClient(jira_url, jira_email, jira_token)
        
        # Test connection
        print("\n🔄 Testing connection...")
        if jira_client.test_connection():
            print("✅ Jira connection successful!")
            
            # Try to fetch some tickets
            print("\n📋 Fetching recent tickets...")
            tickets = jira_client.fetch_recent_tickets(limit=5, days_back=30)
            
            print(f"✅ Found {len(tickets)} tickets:")
            for i, ticket in enumerate(tickets[:3]):
                print(f"  {i+1}. {ticket['key']}: {ticket['summary'][:50]}...")
            
            return True
        else:
            print("❌ Jira connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_jira_connection()