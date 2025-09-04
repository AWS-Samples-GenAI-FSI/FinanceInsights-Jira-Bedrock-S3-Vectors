import requests
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime, timedelta

class JiraClient:
    def __init__(self, jira_url, email, api_token):
        self.jira_url = jira_url.rstrip('/')
        self.auth = HTTPBasicAuth(email, api_token)
        self.headers = {"Accept": "application/json"}
    
    def test_connection(self):
        """Test Jira connection"""
        try:
            response = requests.get(
                f"{self.jira_url}/rest/api/3/myself",
                headers=self.headers,
                auth=self.auth,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def fetch_recent_tickets(self, limit=100, days_back=30):
        """Fetch recent Jira tickets"""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # JQL query for recent tickets
            jql = f"created >= '{start_date.strftime('%Y-%m-%d')}' ORDER BY created DESC"
            
            response = requests.get(
                f"{self.jira_url}/rest/api/3/search",
                headers=self.headers,
                auth=self.auth,
                params={
                    'jql': jql,
                    'maxResults': limit,
                    'fields': 'key,summary,description,status,priority,assignee,created,updated'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                tickets = []
                
                for issue in data.get('issues', []):
                    ticket = {
                        'key': issue['key'],
                        'summary': issue['fields'].get('summary', ''),
                        'description': issue['fields'].get('description', ''),
                        'status': issue['fields']['status']['name'] if issue['fields'].get('status') else '',
                        'priority': issue['fields']['priority']['name'] if issue['fields'].get('priority') else '',
                        'assignee': issue['fields']['assignee']['displayName'] if issue['fields'].get('assignee') else 'Unassigned',
                        'created': issue['fields'].get('created', ''),
                        'updated': issue['fields'].get('updated', '')
                    }
                    tickets.append(ticket)
                
                return tickets
            else:
                raise Exception(f"Failed to fetch tickets: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Error fetching Jira tickets: {str(e)}")
    
    def search_tickets(self, jql_query, limit=50):
        """Search tickets with custom JQL"""
        try:
            response = requests.get(
                f"{self.jira_url}/rest/api/3/search",
                headers=self.headers,
                auth=self.auth,
                params={
                    'jql': jql_query,
                    'maxResults': limit,
                    'fields': 'key,summary,description,status,priority,assignee'
                }
            )
            
            if response.status_code == 200:
                return response.json().get('issues', [])
            else:
                raise Exception(f"Search failed: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Error searching tickets: {str(e)}")