#!/usr/bin/env python3
"""
Bulk load 1000 realistic tickets into Jira
Usage: python scripts/bulk_load_jira.py
"""

import requests
import json
import os
import time
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

load_dotenv()

class JiraBulkLoader:
    def __init__(self):
        self.jira_url = os.getenv("JIRA_URL").rstrip('/')
        self.email = os.getenv("JIRA_EMAIL")
        self.api_token = os.getenv("JIRA_API_TOKEN")
        self.auth = (self.email, self.api_token)
        self.headers = {"Content-Type": "application/json"}
        
        # Get project key (you'll need to set this)
        self.project_key = "KAN"  # Your Kanban project
        
    def get_project_info(self):
        """Get project details and issue types"""
        try:
            # Get project
            response = requests.get(
                f"{self.jira_url}/rest/api/3/project/{self.project_key}",
                auth=self.auth,
                headers=self.headers
            )
            if response.status_code != 200:
                print(f"Project not found. Available projects:")
                projects_response = requests.get(
                    f"{self.jira_url}/rest/api/3/project",
                    auth=self.auth,
                    headers=self.headers
                )
                if projects_response.status_code == 200:
                    for project in projects_response.json():
                        print(f"  - {project['key']}: {project['name']}")
                return None
                
            project = response.json()
            print(f"✅ Found project: {project['name']} ({project['key']})")
            
            # Get issue types
            issue_types_response = requests.get(
                f"{self.jira_url}/rest/api/3/issuetype",
                auth=self.auth,
                headers=self.headers
            )
            
            if issue_types_response.status_code == 200:
                issue_types = issue_types_response.json()
                print(f"✅ Available issue types:")
                for it in issue_types:
                    print(f"  - {it['name']} (ID: {it['id']})")
                return project, issue_types
            
        except Exception as e:
            print(f"❌ Error getting project info: {e}")
            return None
    
    def create_single_ticket(self, ticket_data):
        """Create a single ticket"""
        try:
            response = requests.post(
                f"{self.jira_url}/rest/api/3/issue",
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(ticket_data)
            )
            
            if response.status_code == 201:
                return response.json()['key']
            else:
                print(f"❌ Failed to create ticket: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating ticket: {e}")
            return None
    
    def generate_tickets(self, issue_types, count=1000):
        """Generate and create tickets one by one"""
        
        # Find a valid issue type (avoid Subtask)
        valid_type = None
        for it in issue_types:
            if it['name'].lower() in ['task', 'story', 'bug']:
                valid_type = it['id']
                break
        
        if not valid_type:
            # Use first non-subtask type
            for it in issue_types:
                if 'subtask' not in it['name'].lower():
                    valid_type = it['id']
                    break
        
        # Sample data
        components = ['Frontend', 'Backend', 'Database', 'API', 'Mobile', 'Security']
        
        summaries = [
            "Login page crashes on mobile devices",
            "Database connection timeout errors", 
            "API returns 500 error for large datasets",
            "Search functionality not working properly",
            "File upload fails for files over 10MB",
            "User session expires too quickly",
            "Performance issues on product listing page",
            "Memory leak in user dashboard",
            "Email notifications not being sent",
            "CSS styling broken in Safari browser"
        ]
        
        descriptions = [
            "This issue needs immediate attention as it affects user experience.",
            "The problem occurs intermittently and needs investigation.",
            "Multiple users have reported this issue across different browsers.",
            "This is impacting system performance significantly.",
            "The current implementation doesn't meet requirements."
        ]
        
        created_count = 0
        
        for i in range(count):
            component = random.choice(components)
            summary = f"[{component}] {random.choice(summaries)} #{i+1}"
            
            ticket_data = {
                "fields": {
                    "project": {"key": self.project_key},
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": random.choice(descriptions)
                                    }
                                ]
                            }
                        ]
                    },
                    "issuetype": {"id": valid_type}
                }
            }
            
            ticket_key = self.create_single_ticket(ticket_data)
            if ticket_key:
                created_count += 1
                if created_count % 50 == 0:
                    print(f"✅ Created {created_count} tickets so far...")
                    time.sleep(1)  # Rate limiting
            
        return created_count
    
    def load_tickets(self):
        """Main function to load all tickets"""
        print("🚀 Starting Jira bulk ticket loading...")
        
        # Get project info
        project_info = self.get_project_info()
        if not project_info:
            return
            
        project, issue_types = project_info
        
        # Generate and create tickets
        print("📝 Creating 1000 tickets...")
        total_created = self.generate_tickets(issue_types, 1000)
        
        print(f"🎉 Bulk loading complete! Created {total_created} tickets total.")

if __name__ == "__main__":
    loader = JiraBulkLoader()
    loader.load_tickets()