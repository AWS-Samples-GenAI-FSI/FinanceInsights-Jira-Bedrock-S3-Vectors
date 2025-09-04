#!/usr/bin/env python3
"""
Pull real GitHub issues and create them as Jira tickets
"""

import requests
import json
import os
import time
import random
from dotenv import load_dotenv

load_dotenv()

class GitHubToJira:
    def __init__(self):
        self.jira_url = os.getenv("JIRA_URL").rstrip('/')
        self.jira_email = os.getenv("JIRA_EMAIL")
        self.jira_token = os.getenv("JIRA_API_TOKEN")
        self.jira_auth = (self.jira_email, self.jira_token)
        self.project_key = "KAN"
        
        # Popular repos with lots of issues
        self.repos = [
            "microsoft/vscode",
            "facebook/react", 
            "nodejs/node",
            "kubernetes/kubernetes",
            "tensorflow/tensorflow",
            "angular/angular",
            "vuejs/vue",
            "django/django",
            "rails/rails",
            "laravel/laravel"
        ]
    
    def get_github_issues(self, repo, per_page=100):
        """Get issues from a GitHub repository"""
        url = f"https://api.github.com/repos/{repo}/issues"
        params = {
            'state': 'all',
            'per_page': per_page,
            'sort': 'created',
            'direction': 'desc'
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                issues = response.json()
                # Filter out pull requests
                return [issue for issue in issues if 'pull_request' not in issue]
            else:
                print(f"❌ Failed to get issues from {repo}: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error getting issues from {repo}: {e}")
            return []
    
    def create_jira_ticket(self, github_issue):
        """Create a Jira ticket from GitHub issue"""
        
        # Convert GitHub labels to components
        labels = [label['name'] for label in github_issue.get('labels', [])]
        component_map = {
            'bug': 'Bug',
            'enhancement': 'Enhancement', 
            'feature': 'Feature',
            'documentation': 'Documentation',
            'performance': 'Performance',
            'security': 'Security'
        }
        
        # Determine issue type based on labels
        issue_type_id = "10003"  # Default to Task
        for label in labels:
            if 'bug' in label.lower():
                issue_type_id = "10003"  # Task (treating as bug)
                break
        
        # Clean up description
        description = github_issue.get('body', 'No description provided')
        if not description:
            description = 'No description provided'
        
        # Truncate if too long
        if len(description) > 1000:
            description = description[:1000] + "..."
        
        # Create Jira ticket data
        ticket_data = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": f"[GitHub] {github_issue['title']}",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description
                                }
                            ]
                        },
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Original GitHub issue: {github_issue['html_url']}"
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {"id": issue_type_id}
            }
        }
        
        try:
            response = requests.post(
                f"{self.jira_url}/rest/api/3/issue",
                auth=self.jira_auth,
                headers={"Content-Type": "application/json"},
                data=json.dumps(ticket_data)
            )
            
            if response.status_code == 201:
                result = response.json()
                return result['key']
            else:
                print(f"❌ Failed to create Jira ticket: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating Jira ticket: {e}")
            return None
    
    def load_github_issues(self, target_count=1000):
        """Load GitHub issues into Jira"""
        print(f"🚀 Loading {target_count} real GitHub issues into Jira...")
        
        created_count = 0
        all_issues = []
        
        # Collect issues from multiple repos
        for repo in self.repos:
            print(f"📥 Fetching issues from {repo}...")
            issues = self.get_github_issues(repo, per_page=100)
            all_issues.extend(issues)
            print(f"✅ Got {len(issues)} issues from {repo}")
            
            if len(all_issues) >= target_count:
                break
            
            time.sleep(1)  # Rate limiting
        
        # Shuffle and take what we need
        random.shuffle(all_issues)
        selected_issues = all_issues[:target_count]
        
        print(f"📝 Creating {len(selected_issues)} Jira tickets...")
        
        for i, issue in enumerate(selected_issues):
            ticket_key = self.create_jira_ticket(issue)
            if ticket_key:
                created_count += 1
                if created_count % 50 == 0:
                    print(f"✅ Created {created_count} tickets so far...")
            
            # Rate limiting
            if i % 10 == 0:
                time.sleep(1)
        
        print(f"🎉 Complete! Created {created_count} real GitHub issues as Jira tickets.")

if __name__ == "__main__":
    loader = GitHubToJira()
    loader.load_github_issues(1000)