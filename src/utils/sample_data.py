from datetime import datetime, timedelta
import random

def create_sample_jira_data():
    """Create realistic sample Jira tickets for demo"""
    
    # Sample data components
    components = ["Authentication", "Payment Gateway", "User Interface", "Database", "API", "Mobile App", "Reporting", "Security"]
    priorities = ["Critical", "High", "Medium", "Low"]
    statuses = ["Open", "In Progress", "Code Review", "Testing", "Done", "Closed"]
    assignees = ["John Doe", "Jane Smith", "Mike Johnson", "Sarah Wilson", "David Brown", "Lisa Garcia", "Unassigned"]
    
    # Sample ticket templates
    ticket_templates = [
        {
            "summary": "Login page not loading for mobile users",
            "description": "Users report that the login page fails to load on mobile devices, particularly on iOS Safari. Error occurs intermittently.",
            "component": "Authentication",
            "priority": "High"
        },
        {
            "summary": "Payment processing timeout errors",
            "description": "Credit card payments are timing out during peak hours. Users receive error message 'Transaction failed, please try again'.",
            "component": "Payment Gateway", 
            "priority": "Critical"
        },
        {
            "summary": "Dashboard loading performance is slow",
            "description": "Main dashboard takes 15+ seconds to load. Multiple database queries causing performance bottleneck.",
            "component": "User Interface",
            "priority": "Medium"
        },
        {
            "summary": "Database connection pool exhaustion",
            "description": "Application crashes during high traffic with 'connection pool exhausted' error. Need to optimize connection management.",
            "component": "Database",
            "priority": "Critical"
        },
        {
            "summary": "API rate limiting not working correctly",
            "description": "Rate limiting middleware allows more requests than configured limit. Security concern for API abuse.",
            "component": "API",
            "priority": "High"
        },
        {
            "summary": "Mobile app crashes on startup",
            "description": "iOS app crashes immediately after launch on devices running iOS 17. Stack trace shows memory allocation error.",
            "component": "Mobile App",
            "priority": "Critical"
        },
        {
            "summary": "Export to PDF feature broken",
            "description": "Users cannot export reports to PDF format. Feature returns 500 error when attempting to generate PDF.",
            "component": "Reporting",
            "priority": "Medium"
        },
        {
            "summary": "SQL injection vulnerability in search",
            "description": "Security audit revealed potential SQL injection in user search functionality. Immediate fix required.",
            "component": "Security",
            "priority": "Critical"
        },
        {
            "summary": "User profile images not displaying",
            "description": "Profile pictures show as broken images. Issue started after recent CDN migration.",
            "component": "User Interface",
            "priority": "Low"
        },
        {
            "summary": "Email notifications not being sent",
            "description": "System notifications and password reset emails are not reaching users. SMTP configuration issue suspected.",
            "component": "Authentication",
            "priority": "High"
        },
        {
            "summary": "Search functionality returns incorrect results",
            "description": "Product search returns irrelevant results. Search algorithm needs tuning for better relevance scoring.",
            "component": "API",
            "priority": "Medium"
        },
        {
            "summary": "Memory leak in background job processor",
            "description": "Background job processor shows increasing memory usage over time. Suspected memory leak in task handling.",
            "component": "Database",
            "priority": "High"
        },
        {
            "summary": "Two-factor authentication setup fails",
            "description": "Users cannot complete 2FA setup. QR code generation fails with timeout error.",
            "component": "Security",
            "priority": "High"
        },
        {
            "summary": "Mobile app offline mode not syncing",
            "description": "Data entered in offline mode doesn't sync when connection is restored. Data loss reported by users.",
            "component": "Mobile App",
            "priority": "High"
        },
        {
            "summary": "Report generation takes too long",
            "description": "Monthly reports take over 30 minutes to generate. Users experience timeout errors.",
            "component": "Reporting",
            "priority": "Medium"
        }
    ]
    
    # Generate tickets
    tickets = []
    base_date = datetime.now() - timedelta(days=30)
    
    for i, template in enumerate(ticket_templates):
        ticket_key = f"PROJ-{1000 + i}"
        created_date = base_date + timedelta(days=random.randint(0, 30))
        
        ticket = {
            "key": ticket_key,
            "summary": template["summary"],
            "description": template["description"],
            "status": random.choice(statuses),
            "priority": template["priority"],
            "assignee": random.choice(assignees),
            "component": template["component"],
            "created": created_date.isoformat(),
            "updated": (created_date + timedelta(days=random.randint(0, 5))).isoformat()
        }
        tickets.append(ticket)
    
    return tickets