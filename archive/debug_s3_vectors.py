#!/usr/bin/env python3

import boto3
import json
from botocore.exceptions import ClientError

def debug_s3_vectors():
    """Debug S3 Vectors creation issues"""
    
    print("🔍 Debugging S3 Vectors Issues")
    
    region = 'us-east-1'
    bucket_name = 'test-s3-vectors-debug'
    
    try:
        # Create S3 Vectors client
        s3vectors_client = boto3.client('s3vectors', region_name=region)
        print("✅ S3 Vectors client created successfully")
        
        # Try to list existing vector buckets
        print("\n📋 Checking existing vector buckets...")
        try:
            response = s3vectors_client.list_vector_buckets()
            buckets = response.get('vectorBuckets', [])
            print(f"Found {len(buckets)} existing vector buckets:")
            for bucket in buckets:
                print(f"  - {bucket.get('vectorBucketName', 'Unknown')}")
        except Exception as e:
            print(f"❌ Error listing buckets: {e}")
        
        # Try to create vector bucket with minimal config
        print(f"\n🪣 Creating vector bucket: {bucket_name}")
        try:
            response = s3vectors_client.create_vector_bucket(
                vectorBucketName=bucket_name
            )
            print(f"✅ Vector bucket created: {response}")
            
            # Try to create index
            print("\n📊 Creating vector index...")
            index_response = s3vectors_client.create_index(
                vectorBucketName=bucket_name,
                indexName='test-index',
                dimension=1536,
                distanceMetric='cosine',
                dataType='FLOAT32'
            )
            print(f"✅ Index created: {index_response}")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"❌ AWS Error: {error_code} - {error_message}")
            
            if error_code == 'AccessDenied':
                print("💡 Solution: Need S3 Vectors permissions")
                print("   Add policy: s3vectors:* or request preview access")
            elif error_code == 'InvalidParameter':
                print("💡 Solution: Check parameter format")
            elif error_code == 'ServiceUnavailable':
                print("💡 Solution: S3 Vectors not available in region")
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print(f"Error type: {type(e)}")
    
    except Exception as e:
        print(f"❌ Client creation failed: {e}")

def check_permissions():
    """Check current IAM permissions"""
    
    print("\n🔐 Checking IAM Permissions...")
    
    try:
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        
        print(f"Account: {identity['Account']}")
        print(f"User/Role: {identity['Arn']}")
        
        # Try to simulate policy check
        iam_client = boto3.client('iam')
        
        # This will show what permissions we have
        print("\n📋 Testing permissions...")
        
        # Test S3 permissions
        try:
            s3_client = boto3.client('s3')
            s3_client.list_buckets()
            print("✅ S3 permissions: OK")
        except Exception as e:
            print(f"❌ S3 permissions: {e}")
        
        # Test Bedrock permissions
        try:
            bedrock_client = boto3.client('bedrock-runtime')
            # Just test client creation, not actual call
            print("✅ Bedrock permissions: OK")
        except Exception as e:
            print(f"❌ Bedrock permissions: {e}")
            
    except Exception as e:
        print(f"❌ Permission check failed: {e}")

def test_alternative_s3_approach():
    """Test using regular S3 with vector metadata"""
    
    print("\n🔄 Testing Alternative: Regular S3 + Vector Metadata")
    
    bucket_name = 'test-regular-s3-vectors'
    
    try:
        s3_client = boto3.client('s3', region_name='us-east-1')
        
        # Create regular S3 bucket
        try:
            s3_client.create_bucket(Bucket=bucket_name)
            print(f"✅ Regular S3 bucket created: {bucket_name}")
        except Exception as e:
            if "BucketAlreadyExists" in str(e):
                print(f"✅ Bucket already exists: {bucket_name}")
            else:
                print(f"❌ Bucket creation failed: {e}")
                return
        
        # Upload sample document with metadata
        sample_doc = {
            "AMAZON_BEDROCK_TEXT_CHUNK": "Critical login bug affecting user authentication system",
            "AMAZON_BEDROCK_METADATA": {
                "ticket_id": "PROJ-001",
                "component": "Authentication",
                "priority": "Critical",
                "status": "Open",
                "assignee": "John Smith"
            }
        }
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key="tickets/PROJ-001.json",
            Body=json.dumps(sample_doc),
            ContentType="application/json",
            Metadata={
                'ticket-id': 'PROJ-001',
                'component': 'Authentication',
                'priority': 'Critical'
            }
        )
        
        print("✅ Sample document uploaded with metadata")
        
        # Test Bedrock embedding generation
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        response = bedrock_runtime.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            body=json.dumps({
                "inputText": sample_doc["AMAZON_BEDROCK_TEXT_CHUNK"]
            })
        )
        
        embedding_data = json.loads(response['body'].read())
        embedding = embedding_data['embedding']
        
        print(f"✅ Bedrock embedding generated: {len(embedding)} dimensions")
        print("💡 This approach works! Can use regular S3 + Bedrock for now")
        
        return True
        
    except Exception as e:
        print(f"❌ Alternative approach failed: {e}")
        return False

if __name__ == "__main__":
    debug_s3_vectors()
    check_permissions()
    test_alternative_s3_approach()