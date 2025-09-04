import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def check_kb_status():
    """Check Knowledge Base and ingestion status"""
    
    region = os.getenv('AWS_REGION', 'us-east-1')
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    
    kb_id = "ICK71UCFE6"
    
    # Check KB status
    kb_response = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
    kb_status = kb_response['knowledgeBase']['status']
    print(f"📋 Knowledge Base Status: {kb_status}")
    
    # List data sources
    ds_response = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
    
    for ds in ds_response['dataSourceSummaries']:
        ds_id = ds['dataSourceId']
        ds_name = ds['name']
        ds_status = ds['status']
        print(f"📁 Data Source '{ds_name}': {ds_status}")
        
        # Check ingestion jobs
        jobs_response = bedrock_agent.list_ingestion_jobs(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id,
            maxResults=5
        )
        
        print(f"🔄 Recent Ingestion Jobs:")
        for job in jobs_response['ingestionJobSummaries']:
            job_id = job['ingestionJobId']
            job_status = job['status']
            started_at = job.get('startedAt', 'N/A')
            updated_at = job.get('updatedAt', 'N/A')
            
            print(f"   Job {job_id}: {job_status}")
            print(f"   Started: {started_at}")
            print(f"   Updated: {updated_at}")
            
            if job_status == 'FAILED':
                # Get failure details
                job_details = bedrock_agent.get_ingestion_job(
                    knowledgeBaseId=kb_id,
                    dataSourceId=ds_id,
                    ingestionJobId=job_id
                )
                failure_reasons = job_details['ingestionJob'].get('failureReasons', [])
                if failure_reasons:
                    print(f"   ❌ Failure reasons: {failure_reasons}")
            
            print()
    
    # Check if we need to sync
    if kb_status == 'ACTIVE':
        print("✅ Knowledge Base is ACTIVE")
        
        # Check if any ingestion is still running
        running_jobs = [job for job in jobs_response['ingestionJobSummaries'] if job['status'] in ['IN_PROGRESS', 'STARTING']]
        
        if running_jobs:
            print("⏳ Ingestion still in progress - wait before querying")
        else:
            completed_jobs = [job for job in jobs_response['ingestionJobSummaries'] if job['status'] == 'COMPLETE']
            failed_jobs = [job for job in jobs_response['ingestionJobSummaries'] if job['status'] == 'FAILED']
            
            if completed_jobs:
                print("✅ Data ingestion completed - KB ready for queries!")
            elif failed_jobs:
                print("❌ Data ingestion failed - need to restart sync")
                
                # Start new ingestion job
                print("🔄 Starting new ingestion job...")
                bedrock_agent.start_ingestion_job(
                    knowledgeBaseId=kb_id,
                    dataSourceId=ds_id
                )
                print("✅ New ingestion job started")
            else:
                print("⚠️ No completed ingestion jobs - starting sync...")
                bedrock_agent.start_ingestion_job(
                    knowledgeBaseId=kb_id,
                    dataSourceId=ds_id
                )
                print("✅ Ingestion job started")
    else:
        print(f"⚠️ Knowledge Base status: {kb_status} - wait for ACTIVE")

if __name__ == "__main__":
    check_kb_status()