#!/usr/bin/env python3

import boto3
import json
from src.vector_store.s3_vectors_native import S3VectorsNative

def create_working_s3_vectors():
    """Create working S3 Vectors setup"""
    
    print("🚀 Creating Working S3 Vectors Setup")
    
    # Configuration
    region = 'us-east-1'
    bucket_name = 'lendingtree-jira-vectors-working'
    index_name = 'jira-tickets-index'
    
    try:
        # Initialize S3 Vectors
        s3vectors = S3VectorsNative(
            region=region,
            vector_bucket_name=bucket_name,
            index_name=index_name
        )
        
        print(f"✅ S3 Vectors client created")
        
        # Create vector store
        success = s3vectors.create_vector_store()
        if success:
            print(f"✅ Vector store created: {bucket_name}")
        else:
            print(f"❌ Vector store creation failed")
            return False
        
        # Generate sample embeddings using Bedrock
        print("🔄 Generating sample embeddings...")
        
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        
        sample_tickets = [
            {
                'chunk_id': 'PROJ-001',
                'text': 'Critical login bug affecting user authentication system',
                'key': 'PROJ-001',
                'summary': 'Login authentication failure',
                'status': 'Open',
                'priority': 'Critical',
                'component': 'Authentication'
            },
            {
                'chunk_id': 'PROJ-002', 
                'text': 'Frontend performance issues during peak hours causing slow page loads',
                'key': 'PROJ-002',
                'summary': 'Frontend performance degradation',
                'status': 'In Progress',
                'priority': 'High',
                'component': 'Frontend'
            },
            {
                'chunk_id': 'PROJ-003',
                'text': 'Database connection pool exhaustion under high load conditions',
                'key': 'PROJ-003', 
                'summary': 'Database connection issues',
                'status': 'Open',
                'priority': 'High',
                'component': 'Database'
            }
        ]
        
        # Generate embeddings for each ticket
        vectors_data = []
        for ticket in sample_tickets:
            
            # Generate embedding using Bedrock
            response = bedrock_runtime.invoke_model(
                modelId='amazon.titan-embed-text-v1',
                body=json.dumps({
                    "inputText": ticket['text']
                })
            )
            
            embedding_data = json.loads(response['body'].read())
            embedding = embedding_data['embedding']
            
            # Prepare vector data
            vector_entry = {
                'chunk_id': ticket['chunk_id'],
                'embedding': embedding,
                'text': ticket['text'],
                'key': ticket['key'],
                'summary': ticket['summary'],
                'status': ticket['status'],
                'priority': ticket['priority'],
                'component': ticket['component'],
                'chunk_type': 'jira_ticket',
                'created': '2024-01-01'
            }
            
            vectors_data.append(vector_entry)
            print(f"✅ Generated embedding for {ticket['chunk_id']}")
        
        # Store vectors
        print("📊 Storing vectors in S3 Vectors...")
        success = s3vectors.store_vectors(vectors_data)
        
        if success:
            print(f"✅ Stored {len(vectors_data)} vectors successfully")
        else:
            print("❌ Vector storage failed")
            return False
        
        # Test search
        print("🔍 Testing vector search...")
        
        # Generate query embedding
        query_text = "authentication login problems"
        response = bedrock_runtime.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            body=json.dumps({
                "inputText": query_text
            })
        )
        
        query_embedding = json.loads(response['body'].read())['embedding']
        
        # Search for similar vectors
        search_results = s3vectors.search_similar(query_embedding, top_k=3)
        
        if search_results:
            print(f"✅ Search successful! Found {len(search_results)} results:")
            for i, result in enumerate(search_results):
                print(f"  {i+1}. {result['id']} (score: {result['score']:.3f})")
        else:
            print("⚠️ Search returned no results")
        
        # Get vector count
        count = s3vectors.get_vector_count()
        print(f"📊 Total vectors in index: {count}")
        
        print(f"\n🎉 S3 Vectors Setup Complete!")
        print(f"🪣 Vector Bucket: {bucket_name}")
        print(f"📊 Index: {index_name}")
        print(f"🔢 Vectors Stored: {len(vectors_data)}")
        
        # Save configuration
        config = {
            "VECTOR_BUCKET": bucket_name,
            "INDEX_NAME": index_name,
            "REGION": region,
            "VECTOR_COUNT": len(vectors_data)
        }
        
        with open('.env.s3vectors', 'w') as f:
            for key, value in config.items():
                f.write(f"{key}={value}\n")
        
        print("✅ Configuration saved to .env.s3vectors")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    create_working_s3_vectors()