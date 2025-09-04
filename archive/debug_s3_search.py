#!/usr/bin/env python3

import boto3
import json
from src.vector_store.s3_vectors_native import S3VectorsNative

def debug_s3_search():
    """Debug S3 Vectors search issues"""
    
    print("🔍 Debugging S3 Vectors Search")
    
    # Configuration
    VECTOR_BUCKET = 'lendingtree-jira-vectors-working'
    INDEX_NAME = 'jira-tickets-index'
    REGION = 'us-east-1'
    
    try:
        # Initialize S3 Vectors
        s3vectors = S3VectorsNative(
            region=REGION,
            vector_bucket_name=VECTOR_BUCKET,
            index_name=INDEX_NAME
        )
        
        print(f"✅ S3 Vectors client created")
        
        # Check vector count
        count = s3vectors.get_vector_count()
        print(f"📊 Vectors in index: {count}")
        
        if count == 0:
            print("❌ No vectors found - need to re-upload data")
            return False
        
        # Test with exact vector ID search
        print("\n🔍 Testing direct vector retrieval...")
        
        s3vectors_client = boto3.client('s3vectors', region_name=REGION)
        
        # List all vectors to see what's actually stored
        try:
            response = s3vectors_client.list_vectors(
                vectorBucketName=VECTOR_BUCKET,
                indexName=INDEX_NAME,
                maxResults=10
            )
            
            vectors = response.get('vectors', [])
            print(f"📋 Found {len(vectors)} vectors:")
            
            for vector in vectors:
                print(f"  - ID: {vector.get('vectorKey', 'Unknown')}")
                
        except Exception as e:
            print(f"❌ Error listing vectors: {e}")
        
        # Test search with simple query
        print("\n🔍 Testing vector search...")
        
        # Generate simple query embedding
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=REGION)
        
        query_text = "login"
        response = bedrock_runtime.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            body=json.dumps({
                "inputText": query_text
            })
        )
        
        query_embedding = json.loads(response['body'].read())['embedding']
        print(f"✅ Generated query embedding: {len(query_embedding)} dimensions")
        
        # Try direct S3 Vectors API call
        try:
            search_response = s3vectors_client.query_vectors(
                vectorBucketName=VECTOR_BUCKET,
                indexName=INDEX_NAME,
                queryVector={'float32': query_embedding},
                topK=5
            )
            
            matches = search_response.get('vectorMatches', [])
            print(f"🎯 Direct API search results: {len(matches)}")
            
            for match in matches:
                print(f"  - {match.get('vectorKey', 'Unknown')}: {match.get('similarityScore', 0):.3f}")
                
        except Exception as e:
            print(f"❌ Direct search failed: {e}")
        
        # Try search through our wrapper
        results = s3vectors.search_similar(query_embedding, top_k=5)
        print(f"🔧 Wrapper search results: {len(results)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        return False

def reload_sample_data():
    """Reload sample data with better format"""
    
    print("\n🔄 Reloading Sample Data")
    
    VECTOR_BUCKET = 'lendingtree-jira-vectors-working'
    INDEX_NAME = 'jira-tickets-index'
    REGION = 'us-east-1'
    
    try:
        s3vectors = S3VectorsNative(
            region=REGION,
            vector_bucket_name=VECTOR_BUCKET,
            index_name=INDEX_NAME
        )
        
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=REGION)
        
        # Better sample data
        tickets = [
            {
                'id': 'PROJ-001',
                'text': 'Critical login authentication failure preventing user access to the system',
                'summary': 'Login authentication failure',
                'component': 'Authentication',
                'priority': 'Critical',
                'status': 'Open'
            },
            {
                'id': 'PROJ-002',
                'text': 'Frontend performance issues causing slow page loads during peak usage hours',
                'summary': 'Frontend performance degradation', 
                'component': 'Frontend',
                'priority': 'High',
                'status': 'In Progress'
            },
            {
                'id': 'PROJ-003',
                'text': 'Database connection pool exhaustion under high load causing service disruption',
                'summary': 'Database connection issues',
                'component': 'Database', 
                'priority': 'High',
                'status': 'Open'
            },
            {
                'id': 'PROJ-004',
                'text': 'API timeout errors in payment processing endpoint affecting transactions',
                'summary': 'Payment API timeout issues',
                'component': 'API',
                'priority': 'Critical',
                'status': 'Open'
            },
            {
                'id': 'PROJ-005',
                'text': 'Mobile app crashes on iOS devices when uploading large files',
                'summary': 'Mobile app crash on file upload',
                'component': 'Mobile',
                'priority': 'Medium',
                'status': 'In Progress'
            }
        ]
        
        vectors_data = []
        
        for ticket in tickets:
            # Generate embedding
            response = bedrock_runtime.invoke_model(
                modelId='amazon.titan-embed-text-v1',
                body=json.dumps({
                    "inputText": ticket['text']
                })
            )
            
            embedding = json.loads(response['body'].read())['embedding']
            
            # Format for S3 Vectors
            vector_entry = {
                'chunk_id': ticket['id'],
                'embedding': embedding,
                'text': ticket['text'],
                'key': ticket['id'],
                'summary': ticket['summary'],
                'status': ticket['status'],
                'priority': ticket['priority'],
                'component': ticket['component'],
                'chunk_type': 'jira_ticket'
            }
            
            vectors_data.append(vector_entry)
            print(f"✅ Prepared {ticket['id']}")
        
        # Store vectors
        success = s3vectors.store_vectors(vectors_data)
        
        if success:
            print(f"✅ Stored {len(vectors_data)} vectors")
            
            # Wait a moment for indexing
            import time
            print("⏳ Waiting for indexing...")
            time.sleep(5)
            
            # Test search immediately
            query_text = "login authentication"
            response = bedrock_runtime.invoke_model(
                modelId='amazon.titan-embed-text-v1',
                body=json.dumps({
                    "inputText": query_text
                })
            )
            
            query_embedding = json.loads(response['body'].read())['embedding']
            results = s3vectors.search_similar(query_embedding, top_k=3)
            
            print(f"🔍 Test search results: {len(results)}")
            for result in results:
                print(f"  - {result['id']}: {result['score']:.3f}")
            
            return True
        else:
            print("❌ Failed to store vectors")
            return False
            
    except Exception as e:
        print(f"❌ Reload failed: {e}")
        return False

if __name__ == "__main__":
    debug_s3_search()
    print("\n" + "="*50)
    reload_sample_data()