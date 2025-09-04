import boto3
import json
from typing import List, Dict, Any

class BedrockHelper:
    def __init__(self, region='us-east-1'):
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=region)
        self.embedding_model = 'amazon.titan-embed-text-v1'
        self.text_model = 'anthropic.claude-3-sonnet-20240229-v1:0'
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Amazon Titan"""
        try:
            # Clean and prepare text
            clean_text = text.replace('\n', ' ').strip()
            if not clean_text:
                clean_text = "empty"
            
            body = json.dumps({
                "inputText": clean_text
            })
            
            response = self.bedrock_client.invoke_model(
                modelId=self.embedding_model,
                body=body,
                contentType='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['embedding']
            
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            # Return zero vector as fallback
            return [0.0] * 1536  # Titan embedding dimension
    
    def generate_response(self, query: str, context: str) -> str:
        """Generate response using Claude with retrieved context"""
        try:
            prompt = f"""You are a helpful Jira assistant. Based on the following Jira tickets context, answer the user's question.

Context from Jira tickets:
{context}

User Question: {query}

Please provide a helpful response based on the Jira tickets shown above. If the context doesn't contain relevant information, say so clearly."""

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
            
            response = self.bedrock_client.invoke_model(
                modelId=self.text_model,
                body=body,
                contentType='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def analyze_tickets(self, tickets: List[Dict[str, Any]]) -> str:
        """Analyze a collection of tickets for insights"""
        try:
            # Prepare ticket summaries
            ticket_summaries = []
            for ticket in tickets:
                summary = f"- {ticket.get('key', 'Unknown')}: {ticket.get('summary', 'No summary')} (Status: {ticket.get('status', 'Unknown')})"
                ticket_summaries.append(summary)
            
            context = "\n".join(ticket_summaries)
            
            prompt = f"""Analyze the following Jira tickets and provide insights:

Tickets:
{context}

Please provide:
1. Common themes or patterns
2. Priority distribution
3. Status summary
4. Any notable trends or issues

Keep the analysis concise and actionable."""

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 800,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self.bedrock_client.invoke_model(
                modelId=self.text_model,
                body=body,
                contentType='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            return f"Error analyzing tickets: {str(e)}"