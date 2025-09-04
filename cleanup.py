#!/usr/bin/env python3

import boto3
import json
from botocore.exceptions import ClientError

def cleanup_resources():
    """Clean up all AWS resources created by FinanceInsights"""
    
    print("🧹 Starting FinanceInsights cleanup...")
    
    # Configuration
    region = 'us-east-1'
    pipeline_bucket = 'financial-jira-vectors-pipeline'
    vector_bucket = 'financial-vectors-kb'
    index_name = 'jira-tickets-enhanced'
    
    # Initialize clients
    s3_client = boto3.client('s3', region_name=region)
    s3vectors_client = boto3.client('s3vectors', region_name=region)
    
    try:
        # 1. Delete S3 Vector Index
        print("🗑️  Deleting S3 Vector index...")
        try:
            s3vectors_client.delete_index(
                vectorBucketName=vector_bucket,
                indexName=index_name
            )
            print(f"✅ Deleted vector index: {index_name}")
        except ClientError as e:
            if 'NotFound' in str(e):
                print(f"ℹ️  Vector index {index_name} not found")
            else:
                print(f"❌ Error deleting vector index: {e}")
        
        # 2. Delete S3 Vector Bucket
        print("🗑️  Deleting S3 Vector bucket...")
        try:
            s3vectors_client.delete_vector_bucket(vectorBucketName=vector_bucket)
            print(f"✅ Deleted vector bucket: {vector_bucket}")
        except ClientError as e:
            if 'NotFound' in str(e):
                print(f"ℹ️  Vector bucket {vector_bucket} not found")
            else:
                print(f"❌ Error deleting vector bucket: {e}")
        
        # 3. Empty and delete Pipeline S3 bucket
        print("🗑️  Emptying pipeline S3 bucket...")
        try:
            # List and delete all objects
            response = s3_client.list_objects_v2(Bucket=pipeline_bucket)
            if 'Contents' in response:
                objects = [{'Key': obj['Key']} for obj in response['Contents']]
                s3_client.delete_objects(
                    Bucket=pipeline_bucket,
                    Delete={'Objects': objects}
                )
                print(f"✅ Deleted {len(objects)} objects from {pipeline_bucket}")
            
            # Delete the bucket
            s3_client.delete_bucket(Bucket=pipeline_bucket)
            print(f"✅ Deleted S3 bucket: {pipeline_bucket}")
            
        except ClientError as e:
            if 'NoSuchBucket' in str(e):
                print(f"ℹ️  S3 bucket {pipeline_bucket} not found")
            else:
                print(f"❌ Error deleting S3 bucket: {e}")
        
        print("\n🎉 Cleanup completed successfully!")
        print("📊 Resources cleaned up:")
        print(f"   - S3 Vector index: {index_name}")
        print(f"   - S3 Vector bucket: {vector_bucket}")
        print(f"   - S3 Pipeline bucket: {pipeline_bucket}")
        print("   - All stored tickets and embeddings")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {str(e)}")
        return False
    
    return True

def confirm_cleanup():
    """Ask user to confirm cleanup"""
    print("⚠️  WARNING: This will permanently delete:")
    print("   - All Jira tickets and embeddings")
    print("   - S3 Vector storage and indexes")
    print("   - Pipeline data and configurations")
    print()
    
    response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
    return response in ['yes', 'y']

if __name__ == "__main__":
    if confirm_cleanup():
        cleanup_resources()
    else:
        print("❌ Cleanup cancelled")