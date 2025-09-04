import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def fix_and_test():
    """Fix KB and test query"""
    
    region = os.getenv('AWS_REGION', 'us-east-1')
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=region)
    
    kb_id = "ICK71UCFE6"
    
    # Update .env
    with open('.env', 'w') as f:
        f.write(f'AWS_REGION={region}\n')
        f.write(f'KNOWLEDGE_BASE_ID={kb_id}\n')
    
    print(f"✅ Using KB: {kb_id}")
    
    # Test query directly
    try:
        response = bedrock_runtime.retrieve_and_generate(
            input={'text': 'What are the main issues?'},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kb_id,
                    'modelArn': f'arn:aws:bedrock:{region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0'
                }
            }
        )
        
        print("✅ KB query successful!")
        print(f"Response: {response['output']['text'][:200]}...")
        print("✅ Ready to run: streamlit run app.py")
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        
        # Check if we need to wait for ingestion
        ds_response = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
        for ds in ds_response['dataSourceSummaries']:
            ds_id = ds['dataSourceId']
            jobs = bedrock_agent.list_ingestion_jobs(knowledgeBaseId=kb_id, dataSourceId=ds_id, maxResults=1)
            if jobs['ingestionJobSummaries']:
                job_status = jobs['ingestionJobSummaries'][0]['status']
                print(f"Ingestion status: {job_status}")
                
                if job_status == 'FAILED':
                    print("🔄 Restarting ingestion...")
                    bedrock_agent.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id)
                    print("✅ Ingestion restarted - wait 5 minutes then test again")

if __name__ == "__main__":
    fix_and_test()