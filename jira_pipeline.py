#!/usr/bin/env python3

import boto3
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from src.jira.jira_client import JiraClient

# Load environment
load_dotenv()

def test_complete_pipeline():
    """Test the complete pipeline locally"""
    
    print("🚀 Testing Complete Jira → S3 Vectors Pipeline")
    
    # Configuration
    s3_bucket = 'financial-jira-vectors-pipeline'
    vector_bucket = 'financial-vectors-kb'
    region = 'us-east-1'
    
    # Initialize clients
    s3_client = boto3.client('s3', region_name=region)
    s3vectors_client = boto3.client('s3vectors', region_name=region)
    bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
    
    try:
        # Step 1: Extract Jira tickets
        print("📋 Step 1: Extracting Jira tickets...")
        
        jira_client = JiraClient(
            jira_url=os.getenv('JIRA_URL'),
            email=os.getenv('JIRA_EMAIL'),
            api_token=os.getenv('JIRA_API_TOKEN')
        )
        
        tickets = jira_client.fetch_recent_tickets(limit=1000, days_back=90)
        print(f"✅ Extracted {len(tickets)} tickets")
        
        # Step 2: Transform tickets with business context
        print("🔄 Step 2: Adding business context...")
        
        enhanced_tickets = []
        for ticket in tickets:
            enhanced_ticket = {
                'ticket_id': ticket['key'],
                'summary': ticket['summary'],
                'description': ticket.get('description', ''),
                'priority': ticket['priority'],
                'status': ticket['status'],
                'assignee': ticket['assignee'],
                'created_date': ticket['created'],
                'text': f"{ticket['summary']} {ticket.get('description', '')}",
                'business_context': {
                    'marketplace_impact': assess_marketplace_impact(ticket),
                    'customer_impact': assess_customer_impact(ticket),
                    'urgency_score': calculate_urgency_score(ticket)
                }
            }
            enhanced_tickets.append(enhanced_ticket)
        
        print(f"✅ Enhanced {len(enhanced_tickets)} tickets with business context")
        
        # Step 3: Create S3 buckets
        print("📦 Step 3: Creating S3 buckets...")
        
        try:
            s3_client.create_bucket(Bucket=s3_bucket)
            print(f"✅ Created S3 bucket: {s3_bucket}")
        except:
            print(f"✅ S3 bucket exists: {s3_bucket}")
        
        # Step 4: Upload raw tickets to S3
        print("📤 Step 4: Uploading tickets to S3...")
        
        for ticket in enhanced_tickets:
            key = f"raw-tickets/{datetime.now().strftime('%Y/%m/%d')}/{ticket['ticket_id']}.json"
            
            s3_client.put_object(
                Bucket=s3_bucket,
                Key=key,
                Body=json.dumps(ticket),
                ContentType='application/json'
            )
        
        print(f"✅ Uploaded {len(enhanced_tickets)} tickets to S3")
        
        # Step 5: Create S3 Vector store
        print("🔍 Step 5: Creating S3 Vector store...")
        
        try:
            s3vectors_client.create_vector_bucket(vectorBucketName=vector_bucket)
            print(f"✅ Created vector bucket: {vector_bucket}")
        except:
            print(f"✅ Vector bucket exists: {vector_bucket}")
        
        try:
            s3vectors_client.create_index(
                vectorBucketName=vector_bucket,
                indexName='jira-tickets-enhanced',
                dimension=1024,
                distanceMetric='cosine',
                dataType='float32'
            )
            print("✅ Created vector index: jira-tickets-enhanced")
        except:
            print("✅ Vector index exists: jira-tickets-enhanced")
        
        # Step 6: Generate embeddings and store vectors
        print("📊 Step 6: Generating embeddings...")
        
        vectors = []
        for ticket in enhanced_tickets:
            # Generate embedding
            response = bedrock_runtime.invoke_model(
                modelId='amazon.titan-embed-text-v2:0',
                body=json.dumps({
                    "inputText": ticket['text'],
                    "dimensions": 1024,
                    "normalize": True
                })
            )
            
            embedding = json.loads(response['body'].read())['embedding']
            
            # Prepare vector
            vector_entry = {
                'key': ticket['ticket_id'],
                'data': {'float32': embedding},
                'metadata': {
                    'ticket_id': ticket['ticket_id'],
                    'summary': ticket['summary'],
                    'priority': ticket['priority'],
                    'status': ticket['status'],
                    'assignee': ticket['assignee'],
                    'marketplace_impact': ticket['business_context']['marketplace_impact'],
                    'customer_impact': ticket['business_context']['customer_impact'],
                    'urgency_score': str(ticket['business_context']['urgency_score']),
                    'AMAZON_BEDROCK_TEXT': ticket['text']
                }
            }
            
            vectors.append(vector_entry)
        
        # Store vectors
        s3vectors_client.put_vectors(
            vectorBucketName=vector_bucket,
            indexName='jira-tickets-enhanced',
            vectors=vectors
        )
        
        print(f"✅ Stored {len(vectors)} vectors")
        
        # Step 7: Upload organizational context
        print("📚 Step 7: Adding organizational context...")
        
        org_context = {
            "financial_context.txt": """
Financial Services Business Context:

Mission: Provide secure, compliant financial services and products
Key Products: Banking, Trading, Payments, Lending, Investment Management

Critical Systems:
- Payment processing platforms
- Trading and settlement systems
- Risk management engines
- Compliance monitoring tools
- Customer account management
- Fraud detection systems
- Regulatory reporting platforms

Success Metrics:
- System availability (99.99% target)
- Transaction processing speed
- Regulatory compliance score
- Customer fund security
- Fraud detection accuracy

Risk Areas:
- Payment system failures
- Trading platform outages
- Compliance violations
- Security breaches
- Fraud incidents
            """,
            
            "predictive_patterns.txt": """
Financial Services Predictive Analysis Patterns:

High-Risk Indicators:
- Payment processing errors → Customer fund risks
- Authentication failures → Security breaches
- Trading system issues → Market impact
- Compliance alerts → Regulatory violations

Regulatory Patterns:
- Month-end: High reporting activity
- Quarter-end: Compliance reviews
- Market hours: Trading system criticality

Escalation Triggers:
- Customer funds affected = Immediate escalation
- Regulatory violation = Compliance team alert
- Fraud detected = Security team notification
- Trading system down = Market operations alert

Recommended Actions:
- Real-time fraud monitoring
- Proactive compliance checks
- Customer fund protection protocols
- Regulatory notification procedures
            """
        }
        
        for filename, content in org_context.items():
            s3_client.put_object(
                Bucket=s3_bucket,
                Key=f"knowledge-base/{filename}",
                Body=content,
                ContentType='text/plain'
            )
        
        print("✅ Uploaded organizational context documents")
        
        # Step 8: Test vector search
        print("🔍 Step 8: Testing vector search...")
        
        query_text = "authentication issues"
        query_response = bedrock_runtime.invoke_model(
            modelId='amazon.titan-embed-text-v2:0',
            body=json.dumps({
                "inputText": query_text,
                "dimensions": 1024,
                "normalize": True
            })
        )
        
        query_embedding = json.loads(query_response['body'].read())['embedding']
        
        search_results = s3vectors_client.query_vectors(
            vectorBucketName=vector_bucket,
            indexName='jira-tickets-enhanced',
            queryVector={'float32': query_embedding},
            topK=3
        )
        
        matches = search_results.get('vectorMatches', [])
        print(f"✅ Vector search test: Found {len(matches)} matches")
        
        for match in matches:
            print(f"  - {match.get('vectorKey', 'Unknown')}: {match.get('similarityScore', 0):.3f}")
        
        print("\n🎉 Complete Pipeline Test Successful!")
        print(f"📊 Processed: {len(enhanced_tickets)} tickets")
        print(f"🪣 S3 Bucket: {s3_bucket}")
        print(f"🔍 Vector Bucket: {vector_bucket}")
        print(f"📈 Business Context: Enhanced with LendingTree-specific insights")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {str(e)}")
        return False

def assess_marketplace_impact(ticket):
    """Assess financial system impact"""
    summary = ticket['summary'].lower()
    
    if any(word in summary for word in ['payment', 'trading', 'fraud', 'compliance']):
        return 'High - Critical financial system'
    elif any(word in summary for word in ['performance', 'slow', 'timeout']):
        return 'Medium - Performance impact'
    else:
        return 'Low - Standard impact'

def assess_customer_impact(ticket):
    """Assess customer financial impact"""
    summary = ticket['summary'].lower()
    
    if any(word in summary for word in ['account', 'balance', 'transaction', 'funds']):
        return 'High - Customer funds affected'
    elif any(word in summary for word in ['login', 'authentication', 'access']):
        return 'Medium - Access issues'
    else:
        return 'Low - Backend impact'

def calculate_urgency_score(ticket):
    """Calculate urgency score"""
    score = 0
    
    priority = ticket['priority'].lower()
    if 'critical' in priority: score += 10
    elif 'high' in priority: score += 7
    elif 'medium' in priority: score += 4
    
    summary = ticket['summary'].lower()
    if any(word in summary for word in ['critical', 'urgent', 'blocker']): score += 3
    
    return min(score, 10)

if __name__ == "__main__":
    test_complete_pipeline()