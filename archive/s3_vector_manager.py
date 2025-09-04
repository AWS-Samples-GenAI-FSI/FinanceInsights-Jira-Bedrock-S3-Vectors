import boto3
import json
import numpy as np
from typing import List, Dict, Any
import pickle
from datetime import datetime

class S3VectorManager:
    def __init__(self, region='us-east-1', bucket_name=None):
        self.s3_client = boto3.client('s3', region_name=region)
        self.bucket_name = bucket_name
        self.vector_prefix = 'vectors/'
        self.metadata_prefix = 'metadata/'
    
    def store_vector(self, ticket_key: str, embedding: List[float], metadata: Dict[str, Any]):
        """Store vector embedding and metadata in S3"""
        try:
            # Store vector embedding
            vector_key = f"{self.vector_prefix}{ticket_key}.pkl"
            vector_data = pickle.dumps(np.array(embedding))
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=vector_key,
                Body=vector_data,
                ContentType='application/octet-stream'
            )
            
            # Store metadata
            metadata_key = f"{self.metadata_prefix}{ticket_key}.json"
            metadata_with_timestamp = {
                **metadata,
                'stored_at': datetime.now().isoformat(),
                'vector_key': vector_key
            }
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=metadata_key,
                Body=json.dumps(metadata_with_timestamp),
                ContentType='application/json'
            )
            
            return True
            
        except Exception as e:
            print(f"Error storing vector for {ticket_key}: {str(e)}")
            return False
    
    def search_similar(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar vectors using cosine similarity"""
        try:
            # List all vector files
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.vector_prefix
            )
            
            if 'Contents' not in response:
                return []
            
            similarities = []
            query_vector = np.array(query_embedding)
            
            # Calculate similarities
            for obj in response['Contents']:
                vector_key = obj['Key']
                ticket_key = vector_key.replace(self.vector_prefix, '').replace('.pkl', '')
                
                try:
                    # Load vector
                    vector_obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=vector_key)
                    stored_vector = pickle.loads(vector_obj['Body'].read())
                    
                    # Calculate cosine similarity
                    similarity = np.dot(query_vector, stored_vector) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(stored_vector)
                    )
                    
                    # Load metadata
                    metadata_key = f"{self.metadata_prefix}{ticket_key}.json"
                    metadata_obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=metadata_key)
                    metadata = json.loads(metadata_obj['Body'].read())
                    
                    similarities.append({
                        'ticket_key': ticket_key,
                        'similarity': float(similarity),
                        'metadata': metadata
                    })
                    
                except Exception as e:
                    print(f"Error processing {vector_key}: {str(e)}")
                    continue
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            print(f"Error searching vectors: {str(e)}")
            return []
    
    def get_ticket_metadata(self, ticket_key: str) -> Dict[str, Any]:
        """Get metadata for a specific ticket"""
        try:
            metadata_key = f"{self.metadata_prefix}{ticket_key}.json"
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=metadata_key)
            return json.loads(response['Body'].read())
        except Exception as e:
            print(f"Error getting metadata for {ticket_key}: {str(e)}")
            return {}
    
    def list_stored_tickets(self) -> List[str]:
        """List all stored ticket keys"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.metadata_prefix
            )
            
            if 'Contents' not in response:
                return []
            
            ticket_keys = []
            for obj in response['Contents']:
                key = obj['Key'].replace(self.metadata_prefix, '').replace('.json', '')
                ticket_keys.append(key)
            
            return ticket_keys
            
        except Exception as e:
            print(f"Error listing tickets: {str(e)}")
            return []