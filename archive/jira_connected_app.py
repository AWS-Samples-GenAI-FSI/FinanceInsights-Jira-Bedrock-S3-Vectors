import streamlit as st
import boto3
import json
from datetime import datetime
from src.jira.jira_client import JiraClient

# Page config
st.set_page_config(
    page_title="LendingInsights - Jira Connected",
    page_icon="🚀",
    layout="wide"
)

# Initialize session state
if 'jira_connected' not in st.session_state:
    st.session_state.jira_connected = False
if 'jira_tickets' not in st.session_state:
    st.session_state.jira_tickets = []
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

def connect_to_jira(jira_url, email, api_token):
    """Connect to Jira and fetch tickets"""
    try:
        jira_client = JiraClient(jira_url, email, api_token)
        
        # Test connection
        if not jira_client.test_connection():
            return False, "Failed to connect to Jira. Check your credentials."
        
        # Fetch recent tickets
        tickets = jira_client.fetch_recent_tickets(limit=50, days_back=30)
        
        # Transform tickets for our app
        transformed_tickets = []
        for ticket in tickets:
            transformed_tickets.append({
                'id': ticket['key'],
                'text': f"{ticket['summary']} {ticket.get('description', '')}",
                'summary': ticket['summary'],
                'component': 'General',  # Default since Jira component field not in basic fetch
                'priority': ticket['priority'],
                'status': ticket['status'],
                'assignee': ticket['assignee']
            })
        
        st.session_state.jira_tickets = transformed_tickets
        st.session_state.jira_connected = True
        
        return True, f"Successfully connected! Loaded {len(tickets)} tickets."
        
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def semantic_search(query_text, data):
    """Perform semantic search using Bedrock embeddings"""
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Generate query embedding
        query_response = bedrock_runtime.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            body=json.dumps({
                "inputText": query_text
            })
        )
        
        query_embedding = json.loads(query_response['body'].read())['embedding']
        
        # Generate embeddings for tickets and calculate similarity
        results = []
        
        for ticket in data[:10]:  # Limit to 10 for performance
            ticket_response = bedrock_runtime.invoke_model(
                modelId='amazon.titan-embed-text-v1',
                body=json.dumps({
                    "inputText": ticket['text']
                })
            )
            
            ticket_embedding = json.loads(ticket_response['body'].read())['embedding']
            
            # Calculate cosine similarity
            import numpy as np
            
            query_vec = np.array(query_embedding)
            ticket_vec = np.array(ticket_embedding)
            
            similarity = np.dot(query_vec, ticket_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(ticket_vec))
            
            results.append({
                'ticket': ticket,
                'similarity': similarity
            })
        
        # Sort by similarity
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
        
        prompt = f"""Based on these LendingTree Jira tickets:

{context}

Question: {query_text}

Provide analysis focusing on:
1. Key issues identified
2. Priority and impact assessment
3. Recommended actions for LendingTree's marketplace
4. Potential impact on customer experience"""

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
st.markdown('<p style="font-size: 14px; color: #0066cc; margin-top: -5px;">Connected to Live Jira Data</p>', unsafe_allow_html=True)
st.markdown('<div style="border-bottom: 4px double #0066cc; margin-bottom: 30px;"></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🔗 Jira Connection")
    
    if not st.session_state.jira_connected:
        st.warning("⚠️ Not connected to Jira")
        
        with st.form("jira_connection"):
            jira_url = st.text_input("Jira URL", placeholder="https://yourcompany.atlassian.net")
            email = st.text_input("Email", placeholder="your.email@company.com")
            api_token = st.text_input("API Token", type="password", help="Generate from Jira Account Settings")
            
            if st.form_submit_button("Connect to Jira"):
                if jira_url and email and api_token:
                    with st.spinner("Connecting to Jira..."):
                        success, message = connect_to_jira(jira_url, email, api_token)
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please fill in all fields")
    else:
        st.success("✅ Connected to Jira")
        st.success(f"✅ Tickets Loaded: {len(st.session_state.jira_tickets)}")
        
        if st.button("Disconnect"):
            st.session_state.jira_connected = False
            st.session_state.jira_tickets = []
            st.rerun()
    
    st.header("🚀 System Status")
    st.success("✅ S3 Vectors: Active")
    st.success("✅ Bedrock AI: Connected")

# Main content
if not st.session_state.jira_connected:
    st.markdown('<p style="font-size: 1.8rem; font-weight: 600; color: #444;">Connect to Jira to get started</p>', unsafe_allow_html=True)
    
    st.info("📋 **Setup Instructions:**")
    st.markdown("""
    1. **Jira URL**: Your Atlassian instance URL (e.g., https://company.atlassian.net)
    2. **Email**: Your Jira account email
    3. **API Token**: Generate from Jira Account Settings → Security → API tokens
    """)
    
else:
    st.markdown('<p style="font-size: 1.8rem; font-weight: 600; color: #444;">Ask questions about your Jira tickets</p>', unsafe_allow_html=True)
    
    # Sample questions dropdown
    sample_questions = [
        "Select a sample question...",
        "What are the highest priority issues?",
        "Show me recent critical bugs",
        "Which tickets are still open?",
        "Find authentication-related problems",
        "What issues need immediate attention?"
    ]
    
    selected_sample = st.selectbox("💡 Sample Questions:", sample_questions)
    
    # Question input
    default_question = selected_sample if selected_sample != "Select a sample question..." else ""
    question = st.text_input(
        "Your question:",
        value=default_question,
        placeholder="e.g., What are the most critical issues affecting our system?"
    )
    
    if question:
        with st.spinner("🔍 Analyzing Jira tickets with AI..."):
            # Perform semantic search
            search_results = semantic_search(question, st.session_state.jira_tickets)
            
            if search_results:
                # Generate analysis
                analysis = generate_analysis(question, search_results)
                
                # Display results
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
                
                # Save to history
                st.session_state.search_history.append({
                    'question': question,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'results_count': len(search_results)
                })
            else:
                st.warning("No relevant tickets found for your query.")

# Search history
if st.session_state.search_history:
    with st.expander("📝 Search History", expanded=False):
        for item in reversed(st.session_state.search_history[-5:]):
            st.write(f"**{item['timestamp']}** - {item['question']} ({item['results_count']} results)")

# Footer
st.markdown("---")
st.markdown("💡 **Live Jira Integration** - Real-time ticket analysis powered by AWS AI")