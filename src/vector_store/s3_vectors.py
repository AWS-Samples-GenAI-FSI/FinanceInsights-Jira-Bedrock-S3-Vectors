import boto3
import json
from typing import List, Dict, Any
from datetime import datetime

class S3VectorsNative:
    def __init__(self, region='us-east-1', vector_bucket_name=None, index_name='jira-tickets'):
        try:
            self.s3vectors_client = boto3.client('s3vectors', region_name=region)
            print(f"✅ S3 Vectors client created successfully in {region}")
        except Exception as e:
            print(f"❌ Error creating S3 Vectors client: {str(e)}")
            print(f"Available services: {boto3.Session().get_available_services()[:10]}...")  # Show first 10
            raise e
        self.vector_bucket_name = vector_bucket_name
        self.index_name = index_name
        self.dimension = 1536  # Titan v1 dimension
    
    def create_vector_store(self):
        """Create S3 Vector bucket and index"""
        try:
            # Create vector bucket
            self.s3vectors_client.create_vector_bucket(
                vectorBucketName=self.vector_bucket_name
            )
            
            # Create vector index with metadata configuration
            self.s3vectors_client.create_index(
                vectorBucketName=self.vector_bucket_name,
                indexName=self.index_name,
                dimension=self.dimension,
                distanceMetric='cosine',
                dataType='float32',
                metadataConfiguration={
                    'nonFilterableMetadataKeys': ['AMAZON_BEDROCK_TEXT', 'description']
                }
            )
            return True
            
        except Exception as e:
            if 'already exists' in str(e).lower():
                return True  # Already exists, that's fine
            print(f"Error creating vector store: {str(e)}")
            return False
    
    def store_vectors(self, vectors_data: List[Dict[str, Any]]):
        """Store multiple vectors with metadata"""
        try:
            vectors = []
            
            for data in vectors_data:
                vector_entry = {
                    'key': data['chunk_id'],
                    'data': {'float32': data['embedding']},
                    'metadata': {
                        'key': data.get('key', ''),
                        'summary': data.get('summary', ''),
                        'status': data.get('status', ''),
                        'priority': data.get('priority', ''),
                        'component': data.get('component', ''),
                        'assignee': data.get('assignee', ''),
                        'chunk_type': data.get('chunk_type', ''),
                        'created': data.get('created', ''),
                        'AMAZON_BEDROCK_TEXT': data.get('text', '')
                    }
                }
                vectors.append(vector_entry)
            
            # Store vectors in batches of 100
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i+batch_size]
                
                self.s3vectors_client.put_vectors(
                    vectorBucketName=self.vector_bucket_name,
                    indexName=self.index_name,
                    vectors=batch
                )
            
            return True
            
        except Exception as e:
            print(f"Error storing vectors: {str(e)}")
            return False
    
    def search_similar(self, query_embedding: List[float], top_k: int = 10, filters: Dict = None) -> List[Dict[str, Any]]:
        """Search for similar vectors with optional metadata filtering"""
        try:
            query_params = {
                'vectorBucketName': self.vector_bucket_name,
                'indexName': self.index_name,
                'queryVector': {'float32': query_embedding},
                'topK': top_k
            }
            
            # Add metadata filters if provided
            if filters:
                query_params['metadataFilters'] = filters
            
            response = self.s3vectors_client.query_vectors(**query_params)
            
            results = []
            for match in response.get('vectorMatches', []):
                result = {
                    'id': match['vectorKey'],
                    'score': match['similarityScore'],
                    'metadata': match.get('metadata', {})
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error searching vectors: {str(e)}")
            return []
    
    def get_vector_count(self) -> int:
        """Get total number of vectors in the index"""
        try:
            response = self.s3vectors_client.get_index(
                vectorBucketName=self.vector_bucket_name,
                indexName=self.index_name
            )
            return response.get('vectorCount', 0)
            
        except Exception as e:
            print(f"Error getting vector count: {str(e)}")
            return 0
    
    def delete_vectors(self, vector_ids: List[str]):
        """Delete specific vectors by ID"""
        try:
            self.s3vectors_client.delete_vectors(
                vectorBucketName=self.vector_bucket_name,
                indexName=self.index_name,
                vectorIds=vector_ids
            )
            return True
            
        except Exception as e:
            print(f"Error deleting vectors: {str(e)}")
            return False