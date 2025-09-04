#!/usr/bin/env python3
import requests
import os
from dotenv import load_dotenv

load_dotenv()

jira_url = os.getenv("JIRA_URL").rstrip('/')
email = os.getenv("JIRA_EMAIL")
api_token = os.getenv("JIRA_API_TOKEN")
auth = (email, api_token)

print("🔍 Checking your Jira projects...")

response = requests.get(
    f"{jira_url}/rest/api/3/project",
    auth=auth,
    headers={"Accept": "application/json"}
)

if response.status_code == 200:
    projects = response.json()
    print(f"✅ Found {len(projects)} projects:")
    for project in projects:
        print(f"  - {project['key']}: {project['name']}")
else:
    print(f"❌ Error: {response.status_code} - {response.text}")