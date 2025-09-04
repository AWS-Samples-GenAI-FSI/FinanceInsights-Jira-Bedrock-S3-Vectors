# File Structure

## Main Application Files
- `main_app.py` - Streamlit web application with hybrid search
- `jira_pipeline.py` - Complete data pipeline (Jira → S3 → Vectors)
- `jira_bulk_loader.py` - Parallel bulk ticket creation tool
- `kb_setup.py` - Knowledge base setup utilities

## Source Code (`src/`)
- `src/jira/jira_client.py` - Jira API client
- `src/vector_store/s3_vectors.py` - S3 Vector Engine integration
- `src/bedrock/bedrock_helper.py` - Bedrock utilities
- `src/knowledge_base/bedrock_kb.py` - Knowledge base management
- `src/utils/` - Text processing and sample data utilities

## Scripts (`scripts/`)
- Various setup and utility scripts
- `glue_job_jira_extraction.py` - AWS Glue job for data extraction

## Archive (`archive/`)
- All temporary, test, and deprecated files
- Previous versions and experimental code

## Configuration
- `.env` - Environment variables (AWS, Jira credentials)
- `.env.example` - Template for environment setup
- `requirements.txt` - Python dependencies
- `README.md` - Project documentation