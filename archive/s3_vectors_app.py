import streamlit as st
import boto3
import json
from datetime import datetime
from src.vector_store.s3_vectors_native import S3VectorsNative

# Page config
st.set_page_config(
    page_title="LendingInsights S3 Vectors",
    page_icon="🚀",
    layout="wide"
)

# Load S3 Vectors config
try:
    with open('.env.s3vectors', 'r') as f:
        config = {}
        for line in f:
            key, value = line.strip().split('=')
            config[key] = value
    
    VECTOR_BUCKET = config.get('VECTOR_BUCKET', 'lendingtree-jira-vectors-working')
    INDEX_NAME = config.get('INDEX_NAME', 'jira-tickets-index')
    REGION = config.get('REGION', 'us-east-1')
except:
    VECTOR_BUCKET = 'lendingtree-jira-vectors-working'
    INDEX_NAME = 'jira-tickets-index'
    REGION = 'us-east-1'

# Initialize session state
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

def query_s3_vectors(query_text):
    """Query S3 Vectors with natural language"""
    try:
        # Initialize S3 Vectors
        s3vectors = S3VectorsNative(
            region=REGION,
            vector_bucket_name=VECTOR_BUCKET,
            index_name=INDEX_NAME
        )
        
        # Generate query embedding
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=REGION)
        
        response = bedrock_runtime.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            body=json.dumps({
                "inputText": query_text
            })
        )
        
        query_embedding = json.loads(response['body'].read())['embedding']
        
        # Search vectors
        results = s3vectors.search_similar(query_embedding, top_k=5)
        
        if results:
            # Generate response using Claude
            context = "\n".join([f"Ticket {r['metadata'].get('key', 'Unknown')}: {r['metadata'].get('AMAZON_BEDROCK_TEXT', '')}" for r in results])
            
            prompt = f"""Based on these Jira tickets:

{context}

Question: {query_text}

Provide a helpful analysis of the tickets related to this question."""

            claude_response = bedrock_runtime.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            
            claude_data = json.loads(claude_response['body'].read())
            analysis = claude_data['content'][0]['text']
            
            return {
                'analysis': analysis,
                'results': results,
                'vector_count': len(results)
            }
        else:
            return {
                'analysis': 'No relevant tickets found for your query.',
                'results': [],
                'vector_count': 0
            }
            
    except Exception as e:
        return {
            'analysis': f'Error processing query: {str(e)}',
            'results': [],
            'vector_count': 0
        }

# Header
st.markdown('<h1 style="font-size: 50px; font-weight: 900; color: #0066cc;">🚀 LendingInsights</h1>', unsafe_allow_html=True)
st.markdown('<p style="font-size: 14px; color: #0066cc; margin-top: -5px;">Powered by S3 Vector Engine (Preview)</p>', unsafe_allow_html=True)
st.markdown('<div style="border-bottom: 4px double #0066cc; margin-bottom: 30px;"></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🚀 S3 Vectors Status")
    st.success(f"✅ Vector Bucket: {VECTOR_BUCKET}")
    st.success(f"✅ Index: {INDEX_NAME}")
    st.success(f"✅ Region: {REGION}")
    
    st.header("🎯 Sample Questions")
    sample_questions = [
        "What authentication issues exist?",
        "Show me critical bugs",
        "Which components have problems?",
        "Find performance issues",
        "What database problems are open?"
    ]
    
    for i, question in enumerate(sample_questions):
        if st.button(question, key=f"sample_{i}"):
            st.session_state.selected_question = question

# Main content
col1 = st.container()

with col1:
    st.markdown('<p style="font-size: 1.8rem; font-weight: 600; color: #444;">Ask questions about your Jira tickets</p>', unsafe_allow_html=True)
    
    # Question input
    default_question = st.session_state.get('selected_question', '')
    question = st.text_input(
        "Your question:",
        value=default_question,
        placeholder="e.g., What are the most critical authentication issues?"
    )
    
    # Clear selected question
    if 'selected_question' in st.session_state:
        del st.session_state.selected_question
    
    if question:
        with st.spinner("🔍 Searching S3 Vectors..."):
            result = query_s3_vectors(question)
        
        # Display results
        st.subheader("📊 Analysis")
        st.write(result['analysis'])
        
        if result['results']:
            st.subheader(f"🎫 Related Tickets ({result['vector_count']} found)")
            
            for i, ticket in enumerate(result['results']):
                with st.expander(f"Ticket {i+1}: {ticket['metadata'].get('key', 'Unknown')} (Score: {ticket['score']:.3f})"):
                    metadata = ticket['metadata']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Priority:** {metadata.get('priority', 'Unknown')}")
                        st.write(f"**Status:** {metadata.get('status', 'Unknown')}")
                    with col2:
                        st.write(f"**Component:** {metadata.get('component', 'Unknown')}")
                        st.write(f"**Assignee:** {metadata.get('assignee', 'Unassigned')}")
                    with col3:
                        st.write(f"**Similarity:** {ticket['score']:.1%}")
                    
                    st.write("**Content:**")
                    st.write(metadata.get('AMAZON_BEDROCK_TEXT', 'No content available'))
        
        # Save to history
        st.session_state.search_history.append({
            'question': question,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'results_count': result['vector_count']
        })

# Search history
if st.session_state.search_history:
    with st.expander("📝 Search History", expanded=False):
        for item in reversed(st.session_state.search_history[-5:]):
            st.write(f"**{item['timestamp']}** - {item['question']} ({item['results_count']} results)")

# Footer
st.markdown("---")
st.markdown("💡 **Powered by AWS S3 Vector Engine** - Next-generation serverless vector search")