#!/usr/bin/env python3

import requests
import json
import random
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
import time
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Load environment
load_dotenv()

class FastJiraBulkLoader:
    def __init__(self):
        self.jira_url = os.getenv('JIRA_URL').rstrip('/')
        self.auth = HTTPBasicAuth(os.getenv('JIRA_EMAIL'), os.getenv('JIRA_API_TOKEN'))
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.project_key = "KAN"
        self.created_count = 0
        self.failed_count = 0
        self.lock = threading.Lock()
        
    def generate_ticket_data(self):
        """Generate single ticket data"""
        components = ['Authentication', 'API Gateway', 'Loan Matching', 'Rate Engine', 'Lender Integration', 'Customer Portal']
        priorities = ['Lowest', 'Low', 'Medium', 'High', 'Highest']
        issue_types = ['Task', 'Epic', 'Incident', 'Service Request']
        
        templates = [
            "API timeout in {comp} causing service disruption",
            "{comp} performance degradation during peak hours", 
            "Authentication failure in {comp} affecting users",
            "Data processing error in {comp} system",
            "Integration failure between {comp} and external service",
            "Memory leak in {comp} causing instability"
        ]
        
        component = random.choice(components)
        issue_type = random.choice(issue_types)
        priority = random.choice(priorities)
        
        summary = random.choice(templates).format(comp=component)
        description = f"Issue in {component} component requiring investigation and resolution."
        
        # Build payload
        fields = {
            "project": {"key": self.project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description}]
                }]
            },
            "issuetype": {"name": issue_type},
            "labels": [component.lower().replace(' ', '-')]
        }
        
        # Add priority for supported types
        if issue_type in ['Task', 'Incident', 'Service Request']:
            fields["priority"] = {"name": priority}
        
        return {"fields": fields}
    
    def create_single_ticket(self, ticket_data):
        """Create single ticket - thread-safe"""
        try:
            response = requests.post(
                f"{self.jira_url}/rest/api/3/issue",
                headers=self.headers,
                auth=self.auth,
                data=json.dumps(ticket_data),
                timeout=10
            )
            
            with self.lock:
                if response.status_code == 201:
                    self.created_count += 1
                    if self.created_count % 50 == 0:
                        print(f"✅ Created {self.created_count} tickets")
                    return True
                else:
                    self.failed_count += 1
                    return False
                    
        except Exception as e:
            with self.lock:
                self.failed_count += 1
            return False
    
    def fast_bulk_load(self, count=1000, max_workers=20):
        """Load tickets in parallel"""
        print(f"🚀 Fast loading {count} tickets with {max_workers} parallel workers")
        
        start_time = time.time()
        
        # Generate all ticket data first
        print("📋 Generating ticket data...")
        tickets = [self.generate_ticket_data() for _ in range(count)]
        
        # Create tickets in parallel
        print("⚡ Creating tickets in parallel...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = [executor.submit(self.create_single_ticket, ticket) for ticket in tickets]
            
            # Wait for completion with progress
            completed = 0
            for future in as_completed(futures):
                completed += 1
                if completed % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = completed / elapsed
                    eta = (count - completed) / rate if rate > 0 else 0
                    print(f"🔄 Progress: {completed}/{count} ({rate:.1f}/sec, ETA: {eta:.0f}s)")
        
        elapsed_time = time.time() - start_time
        
        print(f"\n🎉 Bulk load complete in {elapsed_time:.1f} seconds!")
        print(f"✅ Successfully created: {self.created_count} tickets")
        print(f"❌ Failed: {self.failed_count} tickets")
        print(f"⚡ Rate: {self.created_count/elapsed_time:.1f} tickets/second")
        
        return self.created_count

def main():
    """Main execution"""
    print("⚡ Fast Jira Bulk Loader (2-minute target)")
    
    # Get count
    try:
        count = int(input("📊 How many tickets? (default 1000): ") or "1000")
        workers = int(input("🔧 Parallel workers? (default 20): ") or "20")
    except ValueError:
        count = 1000
        workers = 20
    
    if count > 2000:
        print("⚠️ Warning: >2000 tickets may hit API rate limits")
    
    loader = FastJiraBulkLoader()
    
    # Test connection
    try:
        response = requests.get(
            f"{loader.jira_url}/rest/api/3/myself",
            headers=loader.headers,
            auth=loader.auth,
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Jira connection successful")
        else:
            print("❌ Jira connection failed")
            return
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    # Start fast bulk load
    created_count = loader.fast_bulk_load(count, workers)
    
    print(f"\n🎯 Target: 2 minutes")
    print(f"📊 Result: {created_count} tickets created")
    print("💡 Now run your pipeline to process these tickets!")

if __name__ == "__main__":
    main()