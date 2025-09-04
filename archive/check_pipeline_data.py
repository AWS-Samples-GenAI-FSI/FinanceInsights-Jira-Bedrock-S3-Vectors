#!/usr/bin/env python3

import boto3

def check_pipeline_bucket():
    """Check what's in the pipeline S3 bucket"""
    
    s3_client = boto3.client('s3', region_name='us-east-1')
    bucket = 'lendingtree-jira-vectors-pipeline'
    
    try:
        # List all objects in raw-tickets folder
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix='raw-tickets/'
        )
        
        objects = response.get('Contents', [])
        print(f"📊 Total objects in pipeline bucket: {len(objects)}")
        
        # Show first 10 objects
        print("\n📋 Pipeline tickets:")
        for i, obj in enumerate(objects[:10]):
            print(f"  {i+1}. {obj['Key']} ({obj['Size']} bytes)")
        
        if len(objects) > 10:
            print(f"  ... and {len(objects) - 10} more")
        
        # Check knowledge base folder
        kb_response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix='knowledge-base/'
        )
        
        kb_objects = kb_response.get('Contents', [])
        print(f"\n📚 Knowledge base documents: {len(kb_objects)}")
        for obj in kb_objects:
            print(f"  - {obj['Key']}")
        
        return len(objects)
        
    except Exception as e:
        print(f"❌ Error checking bucket: {e}")
        return 0

if __name__ == "__main__":
    check_pipeline_bucket()