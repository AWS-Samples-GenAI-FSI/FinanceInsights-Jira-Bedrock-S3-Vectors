#!/usr/bin/env python3
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

jira_url = os.getenv("JIRA_URL").rstrip('/')
email = os.getenv("JIRA_EMAIL")
api_token = os.getenv("JIRA_API_TOKEN")
auth = (email, api_token)

print("🔍 Testing Jira connection and project setup...")

# Test 1: Get project info
response = requests.get(
    f"{jira_url}/rest/api/3/project/KAN",
    auth=auth,
    headers={"Accept": "application/json"}
)

if response.status_code == 200:
    project = response.json()
    print(f"✅ Project: {project['name']} ({project['key']})")
else:
    print(f"❌ Project error: {response.status_code} - {response.text}")
    exit(1)

# Test 2: Get issue types
response = requests.get(
    f"{jira_url}/rest/api/3/issuetype",
    auth=auth,
    headers={"Accept": "application/json"}
)

if response.status_code == 200:
    issue_types = response.json()
    print(f"✅ Available issue types:")
    for it in issue_types:
        print(f"  - {it['name']} (ID: {it['id']})")
    
    # Find a valid issue type (avoid Subtask)
    valid_type = None
    for it in issue_types:
        if it['name'].lower() in ['task', 'story', 'bug']:
            valid_type = it['id']
            print(f"✅ Using issue type: {it['name']} (ID: {valid_type})")
            break
    
    if not valid_type:
        # Use Task if available, otherwise first non-subtask
        for it in issue_types:
            if 'subtask' not in it['name'].lower():
                valid_type = it['id']
                print(f"✅ Using issue type: {it['name']} (ID: {valid_type})")
                break
else:
    print(f"❌ Issue types error: {response.status_code} - {response.text}")
    exit(1)

# Test 3: Create one test ticket
test_ticket = {
    "fields": {
        "project": {"key": "KAN"},
        "summary": "Test ticket from bulk loader",
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "This is a test ticket to verify the API works"
                        }
                    ]
                }
            ]
        },
        "issuetype": {"id": valid_type}
    }
}

response = requests.post(
    f"{jira_url}/rest/api/3/issue",
    auth=auth,
    headers={"Content-Type": "application/json"},
    data=json.dumps(test_ticket)
)

if response.status_code == 201:
    result = response.json()
    print(f"✅ Test ticket created: {result['key']}")
else:
    print(f"❌ Ticket creation error: {response.status_code}")
    print(f"Response: {response.text}")