import sys
import boto3
import json
import requests
from datetime import datetime, timedelta
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

# Initialize Glue context
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'JIRA_URL', 'JIRA_EMAIL', 'JIRA_TOKEN', 'S3_BUCKET'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

class JiraS3Extractor:
    def __init__(self, jira_url, email, token, s3_bucket):
        self.jira_url = jira_url.rstrip('/')
        self.auth = (email, token)
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client('s3')
        
    def extract_tickets(self, days_back=7):
        """Extract Jira tickets from last N days"""
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        jql = f"updated >= '{start_date}' ORDER BY updated DESC"
        
        tickets = []
        start_at = 0
        max_results = 100
        
        while True:
            url = f"{self.jira_url}/rest/api/3/search"
            params = {
                'jql': jql,
                'startAt': start_at,
                'maxResults': max_results,
                'expand': 'changelog',
                'fields': 'summary,description,priority,status,components,assignee,created,updated,resolution,comment'
            }
            
            response = requests.get(url, auth=self.auth, params=params)
            
            if response.status_code != 200:
                print(f"❌ Error fetching tickets: {response.status_code}")
                break
                
            data = response.json()
            issues = data.get('issues', [])
            
            if not issues:
                break
                
            for issue in issues:
                ticket = self.transform_ticket(issue)
                tickets.append(ticket)
                
            start_at += max_results
            
            if start_at >= data.get('total', 0):
                break
                
        return tickets
    
    def transform_ticket(self, issue):
        """Transform Jira issue to standardized format"""
        fields = issue.get('fields', {})
        
        # Extract components
        components = []
        if fields.get('components'):
            components = [comp['name'] for comp in fields['components']]
        
        # Extract comments
        comments = []
        if fields.get('comment', {}).get('comments'):
            for comment in fields['comment']['comments']:
                comments.append({
                    'author': comment.get('author', {}).get('displayName', 'Unknown'),
                    'body': comment.get('body', ''),
                    'created': comment.get('created', '')
                })
        
        # Build comprehensive text for embedding
        text_content = f"""
        Ticket: {issue['key']}
        Summary: {fields.get('summary', '')}
        Description: {fields.get('description', '')}
        Priority: {fields.get('priority', {}).get('name', 'Unknown')}
        Status: {fields.get('status', {}).get('name', 'Unknown')}
        Components: {', '.join(components)}
        Assignee: {fields.get('assignee', {}).get('displayName', 'Unassigned')}
        Comments: {' '.join([c['body'] for c in comments])}
        """
        
        return {
            'ticket_id': issue['key'],
            'summary': fields.get('summary', ''),
            'description': fields.get('description', ''),
            'priority': fields.get('priority', {}).get('name', 'Unknown'),
            'status': fields.get('status', {}).get('name', 'Unknown'),
            'components': components,
            'assignee': fields.get('assignee', {}).get('displayName', 'Unassigned'),
            'created_date': fields.get('created', ''),
            'updated_date': fields.get('updated', ''),
            'resolution': fields.get('resolution', {}).get('name', '') if fields.get('resolution') else '',
            'comments': comments,
            'text': text_content.strip(),
            'metadata': {
                'source': 'jira',
                'extraction_date': datetime.now().isoformat(),
                'component_count': len(components),
                'comment_count': len(comments)
            }
        }
    
    def upload_to_s3_vectors(self, tickets):
        """Upload tickets to S3 with vector metadata"""
        partition_date = datetime.now().strftime('%Y/%m/%d')
        
        for ticket in tickets:
            key = f"tickets/{partition_date}/{ticket['ticket_id']}.json"
            
            # S3 Vector metadata
            metadata = {
                'vector-metadata': json.dumps({
                    'ticket_id': ticket['ticket_id'],
                    'component': ','.join(ticket['components']),
                    'priority': ticket['priority'],
                    'status': ticket['status'],
                    'created_date': ticket['created_date'],
                    'content_type': 'jira_ticket'
                })
            }
            
            try:
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=key,
                    Body=json.dumps(ticket),
                    Metadata=metadata,
                    ContentType='application/json'
                )
                print(f"✅ Uploaded: {ticket['ticket_id']}")
            except Exception as e:
                print(f"❌ Error uploading {ticket['ticket_id']}: {e}")

# Main execution
def main():
    extractor = JiraS3Extractor(
        jira_url=args['JIRA_URL'],
        email=args['JIRA_EMAIL'], 
        token=args['JIRA_TOKEN'],
        s3_bucket=args['S3_BUCKET']
    )
    
    print("🔄 Starting Jira ticket extraction...")
    tickets = extractor.extract_tickets(days_back=30)  # Last 30 days
    
    print(f"📊 Extracted {len(tickets)} tickets")
    
    print("🔄 Uploading to S3 Vector Store...")
    extractor.upload_to_s3_vectors(tickets)
    
    print("✅ Jira extraction completed successfully")

if __name__ == "__main__":
    main()
    
job.commit()