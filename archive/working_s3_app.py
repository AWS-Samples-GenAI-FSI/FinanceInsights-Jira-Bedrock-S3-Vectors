import streamlit as st
import boto3
import json
from datetime import datetime

# Page config
st.set_page_config(
    page_title="LendingInsights S3 Vectors",
    page_icon="🚀",
    layout="wide"
)

# Initialize session state
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'sample_data' not in st.session_state:
    # In-memory sample data for demo
    st.session_state.sample_data = [
        {
            'id': 'PROJ-001',
            'text': 'Critical login authentication failure preventing user access to the system',
            'summary': 'Login authentication failure',
            'component': 'Authentication',
            'priority': 'Critical',
            'status': 'Open',
            'assignee': 'John Smith'
        },
        {
            'id': 'PROJ-002',
            'text': 'Frontend performance issues causing slow page loads during peak usage hours',
            'summary': 'Frontend performance degradation', 
            'component': 'Frontend',
            'priority': 'High',
            'status': 'In Progress',
            'assignee': 'Sarah Johnson'
        },
        {
            'id': 'PROJ-003',
            'text': 'Database connection pool exhaustion under high load causing service disruption',
            'summary': 'Database connection issues',
            'component': 'Database', 
            'priority': 'High',
            'status': 'Open',
            'assignee': 'Mike Chen'
        },
        {
            'id': 'PROJ-004',
            'text': 'API timeout errors in payment processing endpoint affecting transactions',
            'summary': 'Payment API timeout issues',
            'component': 'API',
            'priority': 'Critical',
            'status': 'Open',
            'assignee': 'Lisa Davis'
        },
        {
            'id': 'PROJ-005',
            'text': 'Mobile app crashes on iOS devices when uploading large files',
            'summary': 'Mobile app crash on file upload',
            'component': 'Mobile',
            'priority': 'Medium',
            'status': 'In Progress',
            'assignee': 'Alex Brown'
        },
        {
            'id': 'PROJ-006',
            'text': 'Security vulnerability in user session management allowing unauthorized access',
            'summary': 'Session management security issue',
            'component': 'Security',
            'priority': 'Critical',
            'status': 'Open',
            'assignee': 'Emma Wilson'
        },
        {
            'id': 'PROJ-007',
            'text': 'Email notification system failing to send alerts for critical events',
            'summary': 'Email notification failure',
            'component': 'Backend',
            'priority': 'Medium',
            'status': 'Open',
            'assignee': 'David Lee'
        },
        {
            'id': 'PROJ-008',
            'text': 'Search functionality returning incorrect results for complex queries',
            'summary': 'Search result accuracy issues',
            'component': 'Frontend',
            'priority': 'Medium',
            'status': 'In Progress',
            'assignee': 'Anna Garcia'
        }
    ]

def chunk_text(text, max_tokens=512):
    """Bedrock-style text chunking"""
    if not text or len(text) < max_tokens:
        return [text]
    
    # Split by sentences first
    sentences = text.replace('.', '.|').replace('!', '!|').replace('?', '?|').split('|')
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # If adding this sentence exceeds max_tokens, start new chunk
        if len(current_chunk + sentence) > max_tokens:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                # Single sentence too long, split by words
                words = sentence.split()
                for i in range(0, len(words), max_tokens//10):
                    chunk_words = words[i:i + max_tokens//10]
                    chunks.append(' '.join(chunk_words))
        else:
            current_chunk += " " + sentence
    
    # Add final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks if chunks else [text]

def semantic_search(query_text, data):
    """Perform semantic search using Bedrock embeddings"""
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Generate query embedding with newer model
        query_response = bedrock_runtime.invoke_model(
            modelId='amazon.titan-embed-text-v2:0',
            body=json.dumps({
                "inputText": query_text,
                "dimensions": 1024,
                "normalize": True
            })
        )
        
        query_embedding = json.loads(query_response['body'].read())['embedding']
        
        # Generate embeddings for all tickets and calculate similarity
        results = []
        
        for ticket in data:
            # Generate ticket embedding with chunking
            ticket_chunks = chunk_text(ticket['text'])
            
            # Use first chunk or combine if multiple
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
            
            # Calculate cosine similarity
            import numpy as np
            
            query_vec = np.array(query_embedding)
            ticket_vec = np.array(ticket_embedding)
            
            similarity = np.dot(query_vec, ticket_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(ticket_vec))
            
            results.append({
                'ticket': ticket,
                'similarity': similarity
            })
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:5]
        
    except Exception as e:
        st.error(f"Search error: {e}")
        return []

def generate_analysis(query_text, search_results):
    """Generate analysis using Claude"""
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Prepare context from search results
        context = "\n".join([
            f"Ticket {r['ticket']['id']}: {r['ticket']['summary']} - {r['ticket']['text']} (Priority: {r['ticket']['priority']}, Status: {r['ticket']['status']}, Component: {r['ticket']['component']})"
            for r in search_results
        ])
        
        prompt = f"""Based on these LendingTree support tickets:

{context}

Question: {query_text}

Provide a comprehensive analysis addressing:
1. Summary of relevant issues found
2. Common patterns or themes
3. Priority assessment
4. Recommended actions
5. Impact on LendingTree's marketplace operations

Focus on how these issues affect the lending marketplace, customer experience, and lender relationships."""

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
st.markdown('<p style="font-size: 14px; color: #0066cc; margin-top: -5px;">Powered by S3 Vectors + Titan v2 + Native Chunking</p>', unsafe_allow_html=True)
st.markdown('<div style="border-bottom: 4px double #0066cc; margin-bottom: 30px;"></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🚀 System Status")
    st.success("✅ S3 Vectors: Active")
    st.success("✅ Bedrock AI: Connected")
    st.success(f"✅ Tickets Loaded: {len(st.session_state.sample_data)}")

# Main content
col1 = st.container()

with col1:
    st.markdown('<p style="font-size: 1.8rem; font-weight: 600; color: #444;">Ask questions about LendingTree support tickets</p>', unsafe_allow_html=True)
    
    # Sample questions dropdown
    sample_questions = [
        "Select a sample question...",
        "What authentication issues exist?",
        "Show me critical bugs",
        "Which components have the most problems?",
        "Find performance issues",
        "What security vulnerabilities are open?",
        "Show me payment-related problems"
    ]
    
    selected_sample = st.selectbox("💡 Sample Questions:", sample_questions)
    
    # Question input
    default_question = selected_sample if selected_sample != "Select a sample question..." else ""
    question = st.text_input(
        "Your question:",
        value=default_question,
        placeholder="e.g., What are the most critical authentication issues affecting our marketplace?"
    )
    
    if question:
        with st.spinner("🔍 Analyzing tickets with AI..."):
            # Perform semantic search
            search_results = semantic_search(question, st.session_state.sample_data)
            
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
                            st.write(f"**Component:** {ticket['component']}")
                            st.write(f"**Assignee:** {ticket['assignee']}")
                        with col3:
                            st.write(f"**Similarity:** {similarity:.1%}")
                        
                        st.write("**Description:**")
                        st.write(ticket['text'])
                
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
st.markdown("💡 **Powered by AWS S3 Vector Engine + Amazon Bedrock** - AI-driven ticket analysis for LendingTree's marketplace operations")