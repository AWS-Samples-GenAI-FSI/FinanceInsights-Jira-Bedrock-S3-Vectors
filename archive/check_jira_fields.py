#!/usr/bin/env python3

import requests
import json
import os
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

# Load environment
load_dotenv()

def check_jira_project_fields():
    """Check available fields in Jira project"""
    
    jira_url = os.getenv('JIRA_URL').rstrip('/')
    auth = HTTPBasicAuth(os.getenv('JIRA_EMAIL'), os.getenv('JIRA_API_TOKEN'))
    headers = {"Accept": "application/json"}
    
    project_key = "KAN"
    
    print(f"🔍 Checking Jira project: {project_key}")
    
    try:
        # Get project info
        response = requests.get(
            f"{jira_url}/rest/api/3/project/{project_key}",
            headers=headers,
            auth=auth
        )
        
        if response.status_code == 200:
            project = response.json()
            print(f"✅ Project: {project['name']}")
        
        # Get issue types for project
        response = requests.get(
            f"{jira_url}/rest/api/3/issuetype/project?projectId={project['id']}",
            headers=headers,
            auth=auth
        )
        
        if response.status_code == 200:
            issue_types = response.json()
            print(f"\n📋 Available Issue Types:")
            for issue_type in issue_types:
                print(f"  - {issue_type['name']} (id: {issue_type['id']})")
        
        # Get priorities
        response = requests.get(
            f"{jira_url}/rest/api/3/priority",
            headers=headers,
            auth=auth
        )
        
        if response.status_code == 200:
            priorities = response.json()
            print(f"\n⚡ Available Priorities:")
            for priority in priorities:
                print(f"  - {priority['name']} (id: {priority['id']})")
        
        # Get create meta for project
        response = requests.get(
            f"{jira_url}/rest/api/3/issue/createmeta?projectKeys={project_key}&expand=projects.issuetypes.fields",
            headers=headers,
            auth=auth
        )
        
        if response.status_code == 200:
            meta = response.json()
            print(f"\n🛠️ Available Fields for Issue Creation:")
            
            if meta['projects']:
                project_meta = meta['projects'][0]
                for issue_type in project_meta['issuetypes']:
                    print(f"\n  Issue Type: {issue_type['name']}")
                    fields = issue_type['fields']
                    
                    # Show key fields
                    key_fields = ['summary', 'description', 'priority', 'assignee', 'labels', 'components']
                    for field_key in key_fields:
                        if field_key in fields:
                            field = fields[field_key]
                            print(f"    ✅ {field['name']} ({field_key}) - Required: {field['required']}")
                        else:
                            print(f"    ❌ {field_key} - Not available")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_jira_project_fields()