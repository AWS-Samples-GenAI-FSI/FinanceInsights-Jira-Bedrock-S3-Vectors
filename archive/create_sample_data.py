import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

def create_sample_data():
    """Create properly formatted sample data for KB"""
    
    s3 = boto3.client('s3')
    bucket = 'jira-tickets-s3-kb'
    
    # Sample tickets in correct format
    tickets = [
        {
            "title": "Frontend Performance Issue - Slow Page Load",
            "description": "Users reporting slow page load times on the dashboard. Initial investigation shows large bundle sizes and unoptimized images causing delays.",
            "priority": "High",
            "status": "Open",
            "component": "Frontend",
            "assignee": "John Doe",
            "ticket_id": "PERF-001"
        },
        {
            "title": "Database Connection Timeout",
            "description": "Application experiencing database connection timeouts during peak hours. Need to optimize connection pooling and query performance.",
            "priority": "Critical",
            "status": "In Progress", 
            "component": "Database",
            "assignee": "Jane Smith",
            "ticket_id": "DB-002"
        },
        {
            "title": "Mobile App Crash on Login",
            "description": "iOS app crashes when users attempt to login with special characters in password. Error occurs in authentication module.",
            "priority": "High",
            "status": "Open",
            "component": "Mobile",
            "assignee": "Mike Johnson",
            "ticket_id": "MOB-003"
        },
        {
            "title": "API Rate Limiting Issues",
            "description": "Third-party API calls are being rate limited causing service disruptions. Need to implement proper retry logic and caching.",
            "priority": "Medium",
            "status": "Open",
            "component": "Backend",
            "assignee": "Sarah Wilson",
            "ticket_id": "API-004"
        },
        {
            "title": "Security Vulnerability in User Authentication",
            "description": "Potential SQL injection vulnerability discovered in user login endpoint. Requires immediate patching and security review.",
            "priority": "Critical",
            "status": "In Progress",
            "component": "Security",
            "assignee": "Alex Brown",
            "ticket_id": "SEC-005"
        }
    ]
    
    # Upload as individual text files
    for ticket in tickets:
        content = f"""Title: {ticket['title']}
Description: {ticket['description']}
Priority: {ticket['priority']}
Status: {ticket['status']}
Component: {ticket['component']}
Assignee: {ticket['assignee']}
Ticket ID: {ticket['ticket_id']}"""
        
        key = f"tickets/{ticket['ticket_id']}.txt"
        s3.put_object(Bucket=bucket, Key=key, Body=content)
        print(f"✅ Uploaded {ticket['ticket_id']}")
    
    print("✅ Sample data created")
    print("Now restart ingestion in the KB")

if __name__ == "__main__":
    create_sample_data()