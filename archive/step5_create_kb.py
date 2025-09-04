import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

def step5_create_kb():
    """Step 5: Create Knowledge Base"""
    
    region = os.getenv('AWS_REGION', 'us-east-1')
    account_id = boto3.client('sts').get_caller_identity()['Account']
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    
    # Read details
    with open('collection_details.txt', 'r') as f:
        lines = f.readlines()
        collection_name = lines[0].strip().split('=')[1]
        collection_id = lines[1].strip().split('=')[1]
        role_arn = lines[3].strip().split('=')[1]
        index_name = lines[4].strip().split('=')[1]
    
    collection_arn = f"arn:aws:aoss:{region}:{account_id}:collection/{collection_id}"
    
    print(f"Step 5: Creating Knowledge Base")
    
    # Create KB
    kb_response = bedrock_agent.create_knowledge_base(
        name=f'jira-kb-{collection_name.split("-")[1]}',
        roleArn=role_arn,
        knowledgeBaseConfiguration={
            'type': 'VECTOR',
            'vectorKnowledgeBaseConfiguration': {
                'embeddingModelArn': f'arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1'
            }
        },
        storageConfiguration={
            'type': 'OPENSEARCH_SERVERLESS',
            'opensearchServerlessConfiguration': {
                'collectionArn': collection_arn,
                'vectorIndexName': index_name,
                'fieldMapping': {
                    'vectorField': 'bedrock-knowledge-base-default-vector',
                    'textField': 'AMAZON_BEDROCK_TEXT_CHUNK',
                    'metadataField': 'AMAZON_BEDROCK_METADATA'
                }
            }
        }
    )
    
    kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
    print(f"✅ Created Knowledge Base: {kb_id}")
    
    # Create data source
    ds_response = bedrock_agent.create_data_source(
        knowledgeBaseId=kb_id,
        name='jira-datasource',
        dataSourceConfiguration={
            'type': 'S3',
            's3Configuration': {
                'bucketArn': 'arn:aws:s3:::jira-tickets-s3-kb'
            }
        }
    )
    
    ds_id = ds_response['dataSource']['dataSourceId']
    print(f"✅ Created data source: {ds_id}")
    
    # Start ingestion
    bedrock_agent.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id)
    print("✅ Started ingestion job")
    
    # Save to .env
    with open('.env', 'a') as f:
        f.write(f'\nKNOWLEDGE_BASE_ID={kb_id}\n')
    
    print(f"🎉 SUCCESS! Knowledge Base created: {kb_id}")
    print("✅ Ready to run: streamlit run app.py")
    
    return kb_id

if __name__ == "__main__":
    step5_create_kb()