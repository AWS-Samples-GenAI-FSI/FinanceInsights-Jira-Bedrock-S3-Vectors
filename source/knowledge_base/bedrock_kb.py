import boto3
import json
import os
from typing import List, Dict

class BedrockKnowledgeBaseProper:
    def __init__(self, region_name: str = "us-east-1"):
        self.region_name = region_name
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        self.knowledge_base_id = os.getenv('KNOWLEDGE_BASE_ID')
    
    def query_knowledge_base(self, query: str, max_results: int = 5) -> str:
        """Query the Bedrock Knowledge Base and generate response"""
        try:
            # Retrieve relevant documents
            retrieve_response = self.bedrock_agent_runtime.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            
            # Extract context from retrieved documents
            context = ""
            for result in retrieve_response['retrievalResults']:
                context += f"{result['content']['text']}\n\n"
            
            # Generate response using Claude
            prompt = f"""Based on the following Jira ticket information, answer the user's question.

Context from Jira tickets:
{context}

User question: {query}

Please provide a helpful answer based on the ticket information above. If the information is not sufficient, say so."""

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self.bedrock_runtime.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            return f"Error querying knowledge base: {str(e)}"
    
    def retrieve_similar_tickets(self, query: str, max_results: int = 5) -> List[Dict]:
        """Retrieve similar tickets without generation"""
        try:
            response = self.bedrock_agent_runtime.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            
            results = []
            for result in response['retrievalResults']:
                results.append({
                    'content': result['content']['text'],
                    'score': result['score'],
                    'location': result['location']['s3Location']['uri'] if 'location' in result else 'Unknown'
                })
            
            return results
            
        except Exception as e:
            return [{'error': f"Error retrieving tickets: {str(e)}"}]