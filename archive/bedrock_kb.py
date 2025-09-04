import boto3
import json
import os
from typing import List, Dict, Any

class BedrockKnowledgeBase:
    def __init__(self, region='us-east-1'):
        self.bedrock_agent = boto3.client('bedrock-agent-runtime', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.region = region
        
        # Use existing S3 bucket
        self.s3_bucket = os.getenv("S3_VECTOR_BUCKET", "my-jira-vector-store")
        self.s3_prefix = "jira-tickets/"
        
        # Knowledge base ID (will be set manually)
        self.kb_id = "YOUR_KB_ID"  # Replace with actual KB ID from console
        self.vector_prefix = "vectors/"
    
    def create_s3_bucket(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            self.s3.create_bucket(Bucket=self.s3_bucket)
            print(f"✅ Created S3 bucket: {self.s3_bucket}")
        except Exception as e:
            if 'BucketAlreadyExists' in str(e) or 'BucketAlreadyOwnedByYou' in str(e):
                print(f"✅ S3 bucket already exists: {self.s3_bucket}")
            else:
                print(f"❌ Error with S3 bucket: {e}")
    
    def upload_tickets_to_s3(self, tickets: List[Dict[str, Any]]):
        """Upload Jira tickets as text files to S3"""
        print(f"📤 Uploading {len(tickets)} tickets to S3...")
        
        # Ensure bucket exists
        self.create_s3_bucket()
        
        for i, ticket in enumerate(tickets):
            # Create readable document for each ticket
            content = f"""Title: {ticket.get('summary', 'No title')}
Key: {ticket.get('key', 'Unknown')}
Status: {ticket.get('status', 'Unknown')}
Priority: {ticket.get('priority', 'Unknown')}
Assignee: {ticket.get('assignee', 'Unassigned')}
Component: {ticket.get('component', 'Unknown')}
Created: {ticket.get('created', 'Unknown')}

Description:
{self._extract_description_text(ticket.get('description', 'No description'))}
"""
            
            # Upload as text file
            key = f"{self.s3_prefix}ticket_{ticket.get('key', i)}.txt"
            
            try:
                self.s3.put_object(
                    Bucket=self.s3_bucket,
                    Key=key,
                    Body=content.encode('utf-8'),
                    ContentType='text/plain'
                )
            except Exception as e:
                print(f"❌ Error uploading ticket {ticket.get('key', i)}: {e}")
        
        print(f"✅ Uploaded tickets to s3://{self.s3_bucket}/{self.s3_prefix}")
        print(f"📊 Vector storage will be at: s3://{self.s3_bucket}/{self.vector_prefix}")
    
    def _extract_description_text(self, description) -> str:
        """Extract plain text from description"""
        if not description:
            return 'No description provided'
        
        if isinstance(description, str):
            return description
        
        if isinstance(description, dict) and description.get('type') == 'doc':
            text_parts = []
            content = description.get('content', [])
            
            for block in content:
                if block.get('type') == 'paragraph':
                    paragraph_content = block.get('content', [])
                    for item in paragraph_content:
                        if item.get('type') == 'text':
                            text_parts.append(item.get('text', ''))
            
            return ' '.join(text_parts)
        
        return str(description)
    
    def query_knowledge_base(self, query: str, max_results: int = 5) -> str:
        """Query the knowledge base using retrieve and generate"""
        try:
            response = self.bedrock_agent.retrieve_and_generate(
                input={
                    'text': query
                },
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.kb_id,
                        'modelArn': f'arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0',
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': max_results
                            }
                        }
                    }
                }
            )
            
            return response['output']['text']
            
        except Exception as e:
            return f"Error querying knowledge base: {str(e)}"
    
    def retrieve_only(self, query: str, max_results: int = 5) -> List[Dict]:
        """Retrieve relevant chunks without generation"""
        try:
            response = self.bedrock_agent.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={
                    'text': query
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            
            return response.get('retrievalResults', [])
            
        except Exception as e:
            print(f"Error retrieving from knowledge base: {e}")
            return []