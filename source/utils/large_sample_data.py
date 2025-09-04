import json
import random
from datetime import datetime, timedelta
import requests

def download_github_issues_as_jira_data():
    """Download real GitHub issues and convert to Jira format"""
    
    # Popular repos with lots of issues
    repos = [
        "microsoft/vscode",
        "facebook/react", 
        "angular/angular",
        "kubernetes/kubernetes",
        "tensorflow/tensorflow"
    ]
    
    all_tickets = []
    
    for repo in repos:
        try:
            # Get issues from GitHub API
            for page in range(1, 21):  # 20 pages = ~2000 issues per repo
                url = f"https://api.github.com/repos/{repo}/issues"
                params = {
                    'state': 'all',
                    'per_page': 100,
                    'page': page,
                    'sort': 'created',
                    'direction': 'desc'
                }
                
                response = requests.get(url, params=params)
                if response.status_code != 200:
                    break
                    
                issues = response.json()
                if not issues:
                    break
                
                for issue in issues:
                    # Skip pull requests
                    if 'pull_request' in issue:
                        continue
                    
                    # Convert to Jira format
                    ticket = {
                        'key': f"{repo.split('/')[1].upper()}-{issue['number']}",
                        'summary': issue['title'][:200],  # Limit length
                        'description': (issue['body'] or '')[:1000],  # Limit length
                        'status': 'Closed' if issue['state'] == 'closed' else 'Open',
                        'priority': get_priority_from_labels(issue.get('labels', [])),
                        'assignee': issue['assignee']['login'] if issue.get('assignee') else 'Unassigned',
                        'component': repo.split('/')[1],
                        'created': issue['created_at'],
                        'updated': issue['updated_at'],
                        'url': issue['html_url']
                    }
                    all_tickets.append(ticket)
                    
                    if len(all_tickets) >= 5000:
                        return all_tickets
                        
        except Exception as e:
            print(f"Error fetching from {repo}: {e}")
            continue
    
    return all_tickets

def get_priority_from_labels(labels):
    """Extract priority from GitHub labels"""
    for label in labels:
        name = label['name'].lower()
        if 'critical' in name or 'urgent' in name:
            return 'Critical'
        elif 'high' in name or 'important' in name:
            return 'High'
        elif 'low' in name or 'minor' in name:
            return 'Low'
    return 'Medium'

def create_large_sample_dataset():
    """Create a large sample dataset"""
    # Skip GitHub download for speed - go straight to synthetic
    print("Generating 1000 synthetic tickets for quick demo...")
    return generate_synthetic_tickets(1000)

def generate_synthetic_tickets(count=1000):
    """Generate synthetic tickets for testing"""
    
    components = ["Frontend", "Backend", "Database", "API", "Mobile", "Security", "DevOps", "Analytics", "Payment", "Auth"]
    priorities = ["Critical", "High", "Medium", "Low"]
    statuses = ["Open", "In Progress", "Code Review", "Testing", "Done", "Closed"]
    
    # Issue types and templates
    issue_types = {
        "Bug": [
            "Login fails with error {error_code}",
            "{component} crashes when {action}",
            "Performance issue in {feature}",
            "Memory leak in {component}",
            "{feature} returns incorrect data",
            "UI elements not displaying correctly in {component}",
            "Timeout errors in {feature}",
            "Data validation failing for {field}",
            "Cache invalidation issues in {component}",
            "Race condition in {feature}"
        ],
        "Feature": [
            "Add {feature} to {component}",
            "Implement {functionality} for {component}",
            "Enhance {feature} with {improvement}",
            "Create new {component} for {purpose}",
            "Add support for {technology} in {component}",
            "Integrate {service} with {component}",
            "Add {metric} tracking to {feature}",
            "Implement {security_feature} for {component}",
            "Add {export_format} export to {feature}",
            "Create {dashboard_type} dashboard for {component}"
        ],
        "Task": [
            "Update {component} documentation",
            "Refactor {component} code",
            "Optimize {feature} performance",
            "Migrate {component} to {technology}",
            "Setup {environment} for {component}",
            "Configure {tool} for {component}",
            "Update {dependency} in {component}",
            "Create tests for {feature}",
            "Setup monitoring for {component}",
            "Backup {data_type} data"
        ]
    }
    
    tickets = []
    start_date = datetime.now() - timedelta(days=730)  # 2 years ago
    
    for i in range(count):
        issue_type = random.choice(list(issue_types.keys()))
        template = random.choice(issue_types[issue_type])
        component = random.choice(components)
        
        # Fill template
        summary = template.format(
            component=component,
            error_code=f"ERR_{random.randint(1000, 9999)}",
            action=random.choice(["loading data", "submitting form", "navigating", "searching"]),
            feature=random.choice(["search", "checkout", "profile", "dashboard", "reports"]),
            field=random.choice(["email", "password", "phone", "address", "payment"]),
            functionality=random.choice(["filtering", "sorting", "pagination", "validation"]),
            improvement=random.choice(["better UX", "faster loading", "mobile support"]),
            purpose=random.choice(["analytics", "reporting", "monitoring", "testing"]),
            technology=random.choice(["React", "Node.js", "Python", "Docker", "Kubernetes"]),
            service=random.choice(["Stripe", "SendGrid", "AWS S3", "Redis", "ElasticSearch"]),
            metric=random.choice(["performance", "usage", "error", "conversion"]),
            security_feature=random.choice(["2FA", "encryption", "audit logging", "rate limiting"]),
            export_format=random.choice(["PDF", "CSV", "Excel", "JSON"]),
            dashboard_type=random.choice(["admin", "user", "analytics", "monitoring"]),
            environment=random.choice(["staging", "production", "development", "testing"]),
            tool=random.choice(["CI/CD", "monitoring", "logging", "backup"]),
            dependency=random.choice(["React", "Node.js", "Python", "Docker"]),
            data_type=random.choice(["user", "transaction", "log", "analytics"])
        )
        
        created_date = start_date + timedelta(days=random.randint(0, 730))
        
        ticket = {
            'key': f"PROJ-{10000 + i}",
            'summary': summary,
            'description': f"Detailed description for {summary}. This issue affects {component} component and needs attention.",
            'status': random.choice(statuses),
            'priority': random.choice(priorities),
            'assignee': random.choice([f"User{j}" for j in range(1, 21)] + ["Unassigned"]),
            'component': component,
            'issue_type': issue_type,
            'created': created_date.isoformat(),
            'updated': (created_date + timedelta(days=random.randint(0, 30))).isoformat()
        }
        tickets.append(ticket)
    
    return tickets