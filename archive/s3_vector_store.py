import boto3
import json
import pickle
import numpy as np
from typing import List, Dict, Any
from src.bedrock.bedrock_helper import BedrockHelper

class S3VectorStore:
    def __init__(self, bucket_name: str, region_name: str = 'us-east-1'):
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.s3 = boto3.client('s3', region_name=region_name)
        self.bedrock = BedrockHelper(region_name)
        
    def store_document_with_embedding(self, doc_id: str, text: str, metadata: Dict):
        """Store document text and its embedding"""
        try:
            # Generate embedding
            embedding = self.bedrock.get_embeddings([text])[0]
            
            # Store embedding as pickle
            embedding_key = f"embeddings/{doc_id}.pkl"
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=embedding_key,
                Body=pickle.dumps(embedding)
            )
            
            # Store metadata
            metadata_key = f"metadata/{doc_id}.json"
            metadata['text'] = text  # Include text in metadata
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=metadata_key,
                Body=json.dumps(metadata)
            )
            
            return True
        except Exception as e:
            print(f"Error storing document {doc_id}: {e}")
            return False
    
    def search_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for similar documents"""
        try:
            # Generate query embedding
            query_embedding = self.bedrock.get_embeddings([query])[0]
            
            # Get all embeddings
            embeddings_response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="embeddings/"
            )
            
            similarities = []
            
            for obj in embeddings_response.get('Contents', []):
                doc_id = obj['Key'].replace('embeddings/', '').replace('.pkl', '')
                
                # Load embedding
                embedding_obj = self.s3.get_object(Bucket=self.bucket_name, Key=obj['Key'])
                doc_embedding = pickle.loads(embedding_obj['Body'].read())
                
                # Calculate cosine similarity
                similarity = np.dot(query_embedding, doc_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                )
                
                similarities.append({
                    'doc_id': doc_id,
                    'similarity': float(similarity)
                })
            
            # Sort by similarity and get top_k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            top_results = similarities[:top_k]
            
            # Get metadata for top results
            results = []
            for result in top_results:
                try:
                    metadata_obj = self.s3.get_object(
                        Bucket=self.bucket_name,
                        Key=f"metadata/{result['doc_id']}.json"
                    )
                    metadata = json.loads(metadata_obj['Body'].read())
                    
                    results.append({
                        'doc_id': result['doc_id'],
                        'similarity': result['similarity'],
                        'text': metadata.get('text', ''),
                        'metadata': metadata
                    })
                except Exception as e:
                    print(f"Error loading metadata for {result['doc_id']}: {e}")
            
            return results
            
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    def query_with_generation(self, query: str, top_k: int = 5) -> str:
        """Search and generate response using Claude"""
        try:
            # Get similar documents
            similar_docs = self.search_similar(query, top_k)
            
            if not similar_docs:
                return "No relevant documents found."
            
            # Build context from similar documents
            context = ""
            for doc in similar_docs:
                context += f"Document: {doc['text']}\n\n"
            
            # Generate response using Claude
            prompt = f"""Based on the following Jira ticket information, answer the user's question.

Context from Jira tickets:
{context}

User question: {query}

Please provide a helpful answer based on the ticket information above."""

            response = self.bedrock.generate_text(prompt, max_tokens=1000)
            return response
            
        except Exception as e:
            return f"Error generating response: {str(e)}"