import json
import random
from datetime import datetime, timedelta
import boto3

def generate_sample_jira_data():
    """Generate 1000 realistic Jira tickets"""
    
    components = ['Frontend', 'Backend', 'Database', 'API', 'Mobile', 'Security', 'DevOps', 'UI/UX']
    priorities = ['Blocker', 'Critical', 'High', 'Medium', 'Low']
    statuses = ['Open', 'In Progress', 'Code Review', 'Testing', 'Done', 'Closed']
    issue_types = ['Bug', 'Story', 'Task', 'Epic', 'Sub-task']
    
    assignees = ['John Smith', 'Sarah Johnson', 'Mike Chen', 'Lisa Davis', 'Alex Brown', 
                'Emma Wilson', 'David Lee', 'Anna Garcia', 'Tom Anderson', 'Maria Rodriguez']
    
    # Common issue patterns
    bug_templates = [
        "Application crashes when {action} with {condition}",
        "{component} performance degradation during {scenario}",
        "Memory leak in {component} causing {impact}",
        "Authentication fails for {user_type} users",
        "Data corruption in {component} after {action}",
        "UI elements not responsive on {device}",
        "API timeout errors in {endpoint}",
        "Database connection pool exhaustion",
        "File upload fails for large files",
        "Search functionality returns incorrect results"
    ]
    
    story_templates = [
        "As a {user_type}, I want to {action} so that {benefit}",
        "Implement {feature} for {component}",
        "Add {functionality} to improve {aspect}",
        "Create {interface} for {purpose}",
        "Integrate {service} with {component}"
    ]
    
    s3 = boto3.client('s3')
    bucket = 'lendingtree-jira-s3-vectors'
    
    for i in range(1, 1001):
        issue_type = random.choice(issue_types)
        component = random.choice(components)
        priority = random.choice(priorities)
        status = random.choice(statuses)
        assignee = random.choice(assignees)
        
        # Generate realistic summary
        if issue_type == 'Bug':
            summary = random.choice(bug_templates).format(
                action=random.choice(['login', 'saving data', 'loading page', 'submitting form']),
                condition=random.choice(['special characters', 'large datasets', 'slow network']),
                component=component,
                scenario=random.choice(['peak hours', 'high load', 'concurrent users']),
                impact=random.choice(['system slowdown', 'service unavailability', 'data loss']),
                user_type=random.choice(['admin', 'regular', 'guest']),
                device=random.choice(['mobile', 'tablet', 'desktop']),
                endpoint=random.choice(['user API', 'data API', 'auth API'])
            )
        else:
            summary = random.choice(story_templates).format(
                user_type=random.choice(['admin', 'customer', 'developer']),
                action=random.choice(['view reports', 'manage settings', 'export data']),
                benefit=random.choice(['better visibility', 'improved efficiency', 'easier management']),
                feature=random.choice(['dashboard', 'notification system', 'search filter']),
                functionality=random.choice(['sorting', 'filtering', 'pagination']),
                aspect=random.choice(['user experience', 'performance', 'security']),
                interface=random.choice(['admin panel', 'user dashboard', 'API endpoint']),
                purpose=random.choice(['data management', 'user interaction', 'system monitoring']),
                service=random.choice(['payment gateway', 'email service', 'analytics tool']),
                component=component
            )
        
        # Generate description
        descriptions = [
            f"Detailed analysis shows that {component.lower()} module requires attention. Users report issues with {random.choice(['performance', 'functionality', 'usability'])}.",
            f"Investigation needed for {component.lower()} component. Impact: {random.choice(['high', 'medium', 'low'])} priority issue affecting {random.randint(10, 500)} users.",
            f"Technical debt in {component.lower()} needs addressing. Proposed solution involves {random.choice(['refactoring', 'optimization', 'redesign'])}.",
            f"Customer feedback indicates problems with {component.lower()}. Root cause analysis required for {random.choice(['stability', 'performance', 'security'])} concerns."
        ]
        
        created_date = datetime.now() - timedelta(days=random.randint(1, 365))
        
        ticket_content = f"""Issue Key: PROJ-{i:04d}
Summary: {summary}
Issue Type: {issue_type}
Status: {status}
Priority: {priority}
Component: {component}
Assignee: {assignee}
Created: {created_date.strftime('%Y-%m-%d')}
Description: {random.choice(descriptions)}

Additional Details:
- Environment: {random.choice(['Production', 'Staging', 'Development'])}
- Browser: {random.choice(['Chrome', 'Firefox', 'Safari', 'Edge'])}
- OS: {random.choice(['Windows 10', 'macOS', 'Linux', 'iOS', 'Android'])}
- Severity: {random.choice(['Critical', 'Major', 'Minor'])}

Comments:
- Initial investigation started
- Assigned to {assignee} for resolution
- {random.choice(['Waiting for customer feedback', 'In development', 'Ready for testing', 'Deployed to staging'])}
"""
        
        # Upload to S3
        key = f"tickets/PROJ-{i:04d}.txt"
        s3.put_object(Bucket=bucket, Key=key, Body=ticket_content)
        
        if i % 100 == 0:
            print(f"✅ Generated {i} tickets")
    
    print("🎉 Generated 1000 realistic Jira tickets!")
    print("📊 Data includes: Bugs, Stories, Tasks, Epics across 8 components")
    print("👥 10 different assignees with realistic scenarios")

if __name__ == "__main__":
    generate_sample_jira_data()