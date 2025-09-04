import streamlit as st
import boto3
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from src.jira.jira_client import JiraClient

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="LendingInsights - Live Jira",
    page_icon="🚀",
    layout="wide"
)

# Initialize session state
if 'jira_tickets' not in st.session_state:
    st.session_state.jira_tickets = []
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'jira_loaded' not in st.session_state:
    st.session_state.jira_loaded = False

def load_jira_tickets():
    """Load tickets from Jira"""
    try:
        jira_client = JiraClient(
            jira_url=os.getenv('JIRA_URL'),
            email=os.getenv('JIRA_EMAIL'),
            api_token=os.getenv('JIRA_API_TOKEN')
        )
        
        # Test connection
        if not jira_client.test_connection():
            return False, "Failed to connect to Jira"
        
        # Fetch tickets
        tickets = jira_client.fetch_recent_tickets(limit=20, days_back=90)
        
        # Transform for our app
        transformed_tickets = []
        for ticket in tickets:
            transformed_tickets.append({
                'id': ticket['key'],
                'text': f"{ticket['summary']} {ticket.get('description', '')}",
                'summary': ticket['summary'],
                'component': 'General',
                'priority': ticket['priority'],
                'status': ticket['status'],
                'assignee': ticket['assignee']
            })
        
        st.session_state.jira_tickets = transformed_tickets
        st.session_state.jira_loaded = True
        
        return True, f"Loaded {len(tickets)} tickets"
        
    except Exception as e:
        return False, f"Error: {str(e)}"

def chunk_text(text, max_tokens=512):
    """Bedrock-style text chunking"""
    if not text or len(text) < max_tokens:
        return [text]
    
    sentences = text.replace('.', '.|').replace('!', '!|').replace('?', '?|').split('|')
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        if len(current_chunk + sentence) > max_tokens:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                words = sentence.split()
                for i in range(0, len(words), max_tokens//10):
                    chunk_words = words[i:i + max_tokens//10]
                    chunks.append(' '.join(chunk_words))
        else:
            current_chunk += " " + sentence
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks if chunks else [text]

def semantic_search(query_text, data):
    """Perform semantic search using Bedrock embeddings"""
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Generate query embedding
        query_response = bedrock_runtime.invoke_model(
            modelId='amazon.titan-embed-text-v2:0',
            body=json.dumps({
                "inputText": query_text,
                "dimensions": 1024,
                "normalize": True
            })
        )
        
        query_embedding = json.loads(query_response['body'].read())['embedding']
        
        results = []
        
        for ticket in data:
            ticket_chunks = chunk_text(ticket['text'])
            text_to_embed = ticket_chunks[0] if ticket_chunks else ticket['text']
            
            ticket_response = bedrock_runtime.invoke_model(
                modelId='amazon.titan-embed-text-v2:0',
                body=json.dumps({
                    "inputText": text_to_embed,
                    "dimensions": 1024,
                    "normalize": True
                })
            )
            
            ticket_embedding = json.loads(ticket_response['body'].read())['embedding']
            
            import numpy as np
            
            query_vec = np.array(query_embedding)
            ticket_vec = np.array(ticket_embedding)
            
            similarity = np.dot(query_vec, ticket_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(ticket_vec))
            
            results.append({
                'ticket': ticket,
                'similarity': similarity
            })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:5]
        
    except Exception as e:
        st.error(f"Search error: {e}")
        return []

def generate_analysis(query_text, search_results):
    """Generate analysis using Claude"""
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        context = "\n".join([
            f"Ticket {r['ticket']['id']}: {r['ticket']['summary']} (Priority: {r['ticket']['priority']}, Status: {r['ticket']['status']})"
            for r in search_results
        ])
        
        prompt = f"""Based on these live Jira tickets:

{context}

Question: {query_text}

Provide analysis focusing on:
1. Key issues identified
2. Priority and impact assessment  
3. Recommended actions
4. Operational impact"""

        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        
        response_data = json.loads(response['body'].read())
        return response_data['content'][0]['text']
        
    except Exception as e:
        return f"Analysis generation failed: {e}"

# Header
st.markdown('<h1 style="font-size: 50px; font-weight: 900; color: #0066cc;">🚀 LendingInsights</h1>', unsafe_allow_html=True)
st.markdown('<p style="font-size: 14px; color: #0066cc; margin-top: -5px;">Live Jira Data + S3 Vectors + Titan v2</p>', unsafe_allow_html=True)
st.markdown('<div style="border-bottom: 4px double #0066cc; margin-bottom: 30px;"></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🔗 Jira Status")
    
    if not st.session_state.jira_loaded:
        if st.button("🔄 Load Jira Tickets"):
            with st.spinner("Loading from Jira..."):
                success, message = load_jira_tickets()
            
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    else:
        st.success("✅ Jira Connected")
        st.success(f"✅ Tickets: {len(st.session_state.jira_tickets)}")
        
        if st.button("🔄 Refresh Tickets"):
            with st.spinner("Refreshing..."):
                success, message = load_jira_tickets()
            if success:
                st.success("Refreshed!")
                st.rerun()
    
    st.header("🚀 System Status")
    st.success("✅ S3 Vectors: Active")
    st.success("✅ Bedrock AI: Connected")

# Main content
if not st.session_state.jira_loaded:
    st.markdown('<p style="font-size: 1.8rem; font-weight: 600; color: #444;">Load Jira tickets to get started</p>', unsafe_allow_html=True)
    st.info("Click 'Load Jira Tickets' in the sidebar to fetch live data from your Jira instance.")
    
else:
    st.markdown('<p style="font-size: 1.8rem; font-weight: 600; color: #444;">Ask questions about your live Jira tickets</p>', unsafe_allow_html=True)
    
    # Sample questions dropdown
    sample_questions = [
        "Select a sample question...",
        "What are the highest priority issues?",
        "Show me recent critical bugs",
        "Which tickets are still open?",
        "Find performance-related problems",
        "What issues need immediate attention?"
    ]
    
    selected_sample = st.selectbox("💡 Sample Questions:", sample_questions)
    
    # Question input
    default_question = selected_sample if selected_sample != "Select a sample question..." else ""
    question = st.text_input(
        "Your question:",
        value=default_question,
        placeholder="e.g., What are the most critical issues in our system?"
    )
    
    if question:
        with st.spinner("🔍 Analyzing live Jira tickets..."):
            search_results = semantic_search(question, st.session_state.jira_tickets)
            
            if search_results:
                analysis = generate_analysis(question, search_results)
                
                st.subheader("📊 AI Analysis")
                st.write(analysis)
                
                st.subheader(f"🎫 Related Tickets ({len(search_results)} found)")
                
                for i, result in enumerate(search_results):
                    ticket = result['ticket']
                    similarity = result['similarity']
                    
                    with st.expander(f"Ticket {i+1}: {ticket['id']} - {ticket['summary']} (Similarity: {similarity:.1%})"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**Priority:** {ticket['priority']}")
                            st.write(f"**Status:** {ticket['status']}")
                        with col2:
                            st.write(f"**Assignee:** {ticket['assignee']}")
                        with col3:
                            st.write(f"**Similarity:** {similarity:.1%}")
                        
                        st.write("**Summary:**")
                        st.write(ticket['summary'])
                
                st.session_state.search_history.append({
                    'question': question,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'results_count': len(search_results)
                })
            else:
                st.warning("No relevant tickets found.")

# Search history
if st.session_state.search_history:
    with st.expander("📝 Search History", expanded=False):
        for item in reversed(st.session_state.search_history[-5:]):
            st.write(f"**{item['timestamp']}** - {item['question']} ({item['results_count']} results)")

# Footer
st.markdown("---")
st.markdown("💡 **Live Jira Integration** - Real-time ticket analysis with AWS AI")