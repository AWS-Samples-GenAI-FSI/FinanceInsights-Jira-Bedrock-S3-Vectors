#!/usr/bin/env python3

import requests
import json
import random
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
import time
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

class JiraBulkLoader:
    def __init__(self):
        self.jira_url = os.getenv('JIRA_URL').rstrip('/')
        self.auth = HTTPBasicAuth(os.getenv('JIRA_EMAIL'), os.getenv('JIRA_API_TOKEN'))
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        
        # Get project key
        self.project_key = "KAN"  # Your existing project
        
    def generate_realistic_tickets(self, count=10000):
        """Generate realistic Jira tickets"""
        
        # LendingTree-specific components and scenarios
        components = [
            'Authentication', 'API Gateway', 'Loan Matching', 'Rate Engine', 
            'Lender Integration', 'Customer Portal', 'Mobile App', 'Database',
            'Payment Processing', 'Credit Check', 'Document Upload', 'Notifications',
            'Reporting', 'Analytics', 'Security', 'DevOps', 'Frontend', 'Backend'
        ]
        
        priorities = ['Lowest', 'Low', 'Medium', 'High', 'Highest']
        issue_types = ['Task', 'Epic', 'Incident', 'Service Request']
        
        assignees = [
            'john.smith', 'sarah.johnson', 'mike.chen', 'lisa.davis', 'alex.brown',
            'emma.wilson', 'david.lee', 'anna.garcia', 'tom.anderson', 'maria.rodriguez',
            'james.taylor', 'jennifer.white', 'robert.clark', 'michelle.lewis', 'kevin.hall'
        ]
        
        # Realistic issue templates
        bug_templates = [
            "API timeout in {component} causing {impact}",
            "{component} performance degradation during {scenario}",
            "Authentication failure for {user_type} users in {component}",
            "Data corruption in {component} affecting {business_area}",
            "Memory leak in {component} service causing instability",
            "Integration failure between {component} and external service",
            "UI rendering issues in {component} on {device}",
            "Database connection pool exhaustion in {component}",
            "Rate calculation errors in {component} for {loan_type}",
            "Lender API integration failing for {component}"
        ]
        
        story_templates = [
            "As a {user_type}, I want to {action} so that {benefit}",
            "Implement {feature} in {component} to improve {metric}",
            "Add {functionality} to {component} for better {outcome}",
            "Create {interface} for {component} to enable {capability}",
            "Integrate {service} with {component} to support {business_need}"
        ]
        
        descriptions = [
            "Detailed investigation shows impact on customer experience and lender relationships.",
            "Root cause analysis indicates infrastructure scaling issues during peak hours.",
            "Customer reports suggest widespread impact across multiple loan products.",
            "Lender feedback indicates integration stability concerns affecting partnership.",
            "Performance monitoring shows degradation in response times and throughput.",
            "Security audit reveals potential vulnerabilities requiring immediate attention.",
            "User analytics indicate significant drop in conversion rates and engagement.",
            "System logs show recurring errors affecting marketplace operations."
        ]
        
        tickets = []
        
        for i in range(count):
            component = random.choice(components)
            issue_type = random.choice(issue_types)
            priority = random.choice(priorities)
            assignee = random.choice(assignees)
            
            # Generate realistic summary
            if issue_type in ['Incident', 'Service Request']:
                summary = random.choice(bug_templates).format(
                    component=component,
                    impact=random.choice(['service disruption', 'data loss', 'performance issues']),
                    scenario=random.choice(['peak hours', 'high load', 'concurrent users']),
                    user_type=random.choice(['premium', 'standard', 'new']),
                    business_area=random.choice(['loan processing', 'rate comparison', 'lender matching']),
                    device=random.choice(['mobile', 'desktop', 'tablet']),
                    loan_type=random.choice(['mortgage', 'personal loan', 'auto loan'])
                )
            else:
                summary = random.choice(story_templates).format(
                    user_type=random.choice(['customer', 'lender', 'admin']),
                    action=random.choice(['compare rates', 'submit application', 'view status']),
                    benefit=random.choice(['better experience', 'faster processing', 'improved accuracy']),
                    feature=random.choice(['rate calculator', 'document upload', 'status tracking']),
                    component=component,
                    functionality=random.choice(['filtering', 'sorting', 'search']),
                    metric=random.choice(['conversion', 'satisfaction', 'efficiency']),
                    outcome=random.choice(['user experience', 'operational efficiency', 'data accuracy']),
                    interface=random.choice(['dashboard', 'API', 'mobile interface']),
                    capability=random.choice(['real-time updates', 'batch processing', 'automated workflows']),
                    service=random.choice(['credit bureau', 'payment gateway', 'document service']),
                    business_need=random.choice(['compliance', 'scalability', 'reliability'])
                )
            
            # Random creation date (last 2 years)
            created_date = datetime.now() - timedelta(days=random.randint(1, 730))
            
            ticket = {
                'summary': summary,
                'description': random.choice(descriptions),
                'issue_type': issue_type,
                'priority': priority,
                'component': component,
                'assignee': assignee,
                'created_date': created_date,
                'labels': random.sample(['marketplace', 'lender-impact', 'customer-facing', 'performance', 'security', 'integration'], k=random.randint(1, 3))
            }
            
            tickets.append(ticket)
            
            if (i + 1) % 1000 == 0:
                print(f"✅ Generated {i + 1} tickets")
        
        return tickets
    
    def create_jira_ticket(self, ticket):
        """Create single ticket in Jira"""
        
        # Build payload with only supported fields
        fields = {
            "project": {"key": self.project_key},
            "summary": ticket['summary'],
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": ticket['description']
                            }
                        ]
                    }
                ]
            },
            "issuetype": {"name": ticket['issue_type']},
            "labels": ticket['labels']
        }
        
        # Add priority only for supported issue types
        if ticket['issue_type'] in ['Task', 'Incident', 'Service Request']:
            fields["priority"] = {"name": ticket['priority']}
        
        payload = {"fields": fields}
        
        try:
            response = requests.post(
                f"{self.jira_url}/rest/api/3/issue",
                headers=self.headers,
                auth=self.auth,
                data=json.dumps(payload)
            )
            
            if response.status_code == 201:
                return response.json()['key']
            else:
                print(f"❌ Failed to create ticket: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating ticket: {e}")
            return None
    
    def bulk_load_tickets(self, count=10000, batch_size=50):
        """Load tickets in batches"""
        
        print(f"🚀 Starting bulk load of {count} tickets to Jira")
        
        # Generate tickets
        print("📋 Generating realistic tickets...")
        tickets = self.generate_realistic_tickets(count)
        
        # Create tickets in batches
        created_count = 0
        failed_count = 0
        
        for i in range(0, len(tickets), batch_size):
            batch = tickets[i:i + batch_size]
            
            print(f"🔄 Processing batch {i//batch_size + 1}/{(len(tickets) + batch_size - 1)//batch_size}")
            
            for ticket in batch:
                ticket_key = self.create_jira_ticket(ticket)
                
                if ticket_key:
                    created_count += 1
                else:
                    failed_count += 1
                
                # Rate limiting
                time.sleep(0.1)  # 10 requests per second
            
            # Progress update
            if (i + batch_size) % 500 == 0:
                print(f"✅ Created {created_count} tickets, Failed: {failed_count}")
                time.sleep(2)  # Longer pause every 500 tickets
        
        print(f"\n🎉 Bulk load complete!")
        print(f"✅ Successfully created: {created_count} tickets")
        print(f"❌ Failed: {failed_count} tickets")
        
        return created_count

def main():
    """Main execution"""
    
    print("🎯 LendingTree Jira Bulk Loader")
    print("This will create 10,000 realistic tickets in your Jira instance")
    
    # Confirm before proceeding
    confirm = input("\n⚠️  This will create 10,000 tickets. Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    # Ask for count
    try:
        count = int(input("📊 How many tickets to create? (default 1000): ") or "1000")
    except ValueError:
        count = 1000
    
    loader = JiraBulkLoader()
    
    # Test connection first
    try:
        response = requests.get(
            f"{loader.jira_url}/rest/api/3/myself",
            headers=loader.headers,
            auth=loader.auth
        )
        
        if response.status_code == 200:
            print("✅ Jira connection successful")
        else:
            print("❌ Jira connection failed")
            return
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    # Start bulk load
    created_count = loader.bulk_load_tickets(count)
    
    print(f"\n🎉 Process complete! Created {created_count} tickets")
    print("💡 Now run your pipeline to process these tickets with S3 Vectors")

if __name__ == "__main__":
    main()