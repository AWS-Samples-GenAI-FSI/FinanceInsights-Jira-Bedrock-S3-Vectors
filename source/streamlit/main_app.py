import streamlit as st
import boto3
import json
import time
from datetime import datetime

# Load financial context
with open('source/config/financial_context.json', 'r') as f:
    FINANCIAL_CONFIG = json.load(f)

# Page config
st.set_page_config(
    page_title=f"{FINANCIAL_CONFIG['app_name']} - Jira RAG Assistant",
    page_icon="💰",
    layout="wide"
)

# Custom CSS for stylish fonts
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.main-header {
    font-family: 'Inter', sans-serif;
    font-weight: 900;
    font-size: 3.5rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin-bottom: 0.5rem;
}

.sub-header {
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    font-size: 1.1rem;
    color: #6366f1;
    text-align: center;
    margin-bottom: 2rem;
    opacity: 0.8;
}

.metric-card {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem;
    margin: 0.5rem 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.stSelectbox label, .stTextInput label {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    color: #374151;
}

.stButton > button {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    border-radius: 8px;
    border: none;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.sidebar-header {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    color: #1f2937;
}

.code-font {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
}

.analysis-text {
    font-family: 'Inter', sans-serif;
    line-height: 1.6;
    color: #374151;
}

.ticket-title {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    color: #1f2937;
}

.footer-text {
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    color: #6366f1;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# Configuration
PIPELINE_S3_BUCKET = 'financial-jira-vectors-pipeline'
VECTOR_BUCKET = 'financial-vectors-kb'
INDEX_NAME = 'jira-tickets-enhanced'
REGION = 'us-east-1'

# Initialize session state
if 'pipeline_tickets' not in st.session_state:
    st.session_state.pipeline_tickets = []
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'setup_complete' not in st.session_state:
    st.session_state.setup_complete = False
if 'setup_running' not in st.session_state:
    st.session_state.setup_running = False
if 'setup_mode' not in st.session_state:
    st.session_state.setup_mode = 'existing'

def check_setup_status():
    """Check if initial setup is complete"""
    try:
        s3_client = boto3.client('s3', region_name=REGION)
        
        # Check if pipeline bucket exists and has data
        try:
            response = s3_client.list_objects_v2(
                Bucket=PIPELINE_S3_BUCKET,
                Prefix='raw-tickets/',
                MaxKeys=1
            )
            return 'Contents' in response and len(response['Contents']) > 0
        except:
            return False
    except:
        return False

def run_initial_setup(mode="existing"):
    """Run the initial ETL pipeline setup"""
    try:
        import subprocess
        import sys
        
        if mode == "demo":
            # First generate demo tickets
            demo_result = subprocess.run(
                [sys.executable, 'source/utils/jira_bulk_loader.py'],
                capture_output=True,
                text=True,
                timeout=180  # 3 minute timeout for demo generation
            )
            
            if demo_result.returncode != 0:
                return False, f"Demo data generation failed: {demo_result.stderr}"
        
        # Run the pipeline script
        result = subprocess.run(
            [sys.executable, 'deployment/jira_pipeline.py'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            ticket_count = "100+" if mode == "demo" else "your"
            return True, f"Setup completed successfully! Processed {ticket_count} tickets with AI embeddings."
        else:
            return False, f"Setup failed: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "Setup timed out - please check your Jira connection and try again"
    except Exception as e:
        return False, f"Setup error: {str(e)}"

def load_pipeline_tickets():
    """Load tickets from pipeline S3 bucket"""
    try:
        s3_client = boto3.client('s3', region_name=REGION)
        
        response = s3_client.list_objects_v2(
            Bucket=PIPELINE_S3_BUCKET,
            Prefix='raw-tickets/'
        )
        
        tickets = []
        for obj in response.get('Contents', [])[:100]:  # Load more tickets
            ticket_response = s3_client.get_object(
                Bucket=PIPELINE_S3_BUCKET,
                Key=obj['Key']
            )
            
            ticket_data = json.loads(ticket_response['Body'].read())
            
            tickets.append({
                'id': ticket_data['ticket_id'],
                'text': ticket_data['text'],
                'summary': ticket_data['summary'],
                'priority': ticket_data['priority'],
                'status': ticket_data['status'],
                'assignee': ticket_data['assignee'],
                'marketplace_impact': ticket_data['business_context']['marketplace_impact'],
                'customer_impact': ticket_data['business_context']['customer_impact'],
                'urgency_score': ticket_data['business_context']['urgency_score']
            })
        
        st.session_state.pipeline_tickets = tickets
        return True, f"Loaded {len(tickets)} pipeline tickets"
        
    except Exception as e:
        return False, f"Error: {str(e)}"

def hybrid_search(query_text):
    """Hybrid search: Try S3 Vectors first, fallback to semantic search"""
    
    # Try S3 Vectors first
    vector_results = try_s3_vectors_search(query_text)
    if vector_results:
        return vector_results
    
    # Fallback to semantic search on loaded data
    return semantic_search_fallback(query_text)

def try_s3_vectors_search(query_text):
    """Try S3 Vectors search"""
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=REGION)
        s3vectors_client = boto3.client('s3vectors', region_name=REGION)
        
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
        
        # Search S3 Vectors
        search_results = s3vectors_client.query_vectors(
            vectorBucketName=VECTOR_BUCKET,
            indexName=INDEX_NAME,
            queryVector={'float32': query_embedding},
            topK=5
        )
        
        matches = search_results.get('vectorMatches', [])
        if not matches:
            return None
        
        # Format results
        results = []
        for match in matches:
            metadata = match.get('metadata', {})
            
            results.append({
                'ticket': {
                    'id': metadata.get('ticket_id', 'Unknown'),
                    'summary': metadata.get('summary', 'No summary'),
                    'priority': metadata.get('priority', 'Unknown'),
                    'status': metadata.get('status', 'Unknown'),
                    'assignee': metadata.get('assignee', 'Unassigned'),
                    'marketplace_impact': metadata.get('marketplace_impact', 'Unknown'),
                    'customer_impact': metadata.get('customer_impact', 'Unknown'),
                    'urgency_score': metadata.get('urgency_score', '0'),
                    'text': metadata.get('AMAZON_BEDROCK_TEXT', 'No content')
                },
                'similarity': match.get('similarityScore', 0),
                'source': 'S3 Vectors'
            })
        
        return results
        
    except Exception as e:
        st.warning(f"S3 Vectors search failed: {e}")
        return None

def semantic_search_fallback(query_text):
    """Fallback semantic search on loaded tickets"""
    try:
        if not st.session_state.pipeline_tickets:
            return []
        
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=REGION)
        
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
        
        for ticket in st.session_state.pipeline_tickets:
            # Generate ticket embedding
            ticket_response = bedrock_runtime.invoke_model(
                modelId='amazon.titan-embed-text-v2:0',
                body=json.dumps({
                    "inputText": ticket['text'],
                    "dimensions": 1024,
                    "normalize": True
                })
            )
            
            ticket_embedding = json.loads(ticket_response['body'].read())['embedding']
            
            # Calculate similarity
            import numpy as np
            
            query_vec = np.array(query_embedding)
            ticket_vec = np.array(ticket_embedding)
            
            similarity = np.dot(query_vec, ticket_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(ticket_vec))
            
            results.append({
                'ticket': ticket,
                'similarity': similarity,
                'source': 'Direct Search'
            })
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:5]
        
    except Exception as e:
        st.error(f"Fallback search error: {e}")
        return []

def generate_business_analysis(query_text, search_results):
    """Generate business-focused analysis"""
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=REGION)
        
        context = "\n".join([
            f"Ticket {r['ticket']['id']}: {r['ticket']['summary']}\n"
            f"  Priority: {r['ticket']['priority']}, Status: {r['ticket']['status']}\n"
            f"  Marketplace Impact: {r['ticket']['marketplace_impact']}\n"
            f"  Customer Impact: {r['ticket']['customer_impact']}\n"
            f"  Urgency Score: {r['ticket']['urgency_score']}/10\n"
            f"  Search Method: {r['source']}\n"
            for r in search_results
        ])
        
        prompt = f"""Based on these financial services support tickets:

{context}

Question: {query_text}

Provide analysis focusing on:

**🎯 Risk & Compliance Patterns:**
- High urgency scores (7+) with regulatory impact
- Multiple tickets affecting critical financial systems
- Compliance violations requiring immediate attention
- Customer funds or trading system impacts

**📊 Financial Impact Assessment:**
- Regulatory compliance risks
- Customer financial impact
- Trading/payment system disruptions
- Operational risk exposure

**🔮 Predictive Insights:**
- Fraud pattern indicators
- System vulnerability trends
- Compliance gap patterns
- Customer impact escalation risks

**⚡ Recommended Actions:**
- Regulatory notification requirements
- Customer communication needs
- System isolation procedures
- Compliance team escalation

Focus on financial services risk management and regulatory compliance."""

        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1200,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        
        response_data = json.loads(response['body'].read())
        return response_data['content'][0]['text']
        
    except Exception as e:
        return f"Analysis generation failed: {e}"

# Header
st.markdown(f'<div class="main-header">💰 {FINANCIAL_CONFIG["app_name"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">{FINANCIAL_CONFIG["app_description"]}</div>', unsafe_allow_html=True)
st.markdown('<div style="border-bottom: 4px double #0066cc; margin-bottom: 30px;"></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown('<div class="sidebar-header">🔗 Pipeline Status</div>', unsafe_allow_html=True)
    
    if not st.session_state.pipeline_tickets:
        if st.button("📊 Load Pipeline Data"):
            with st.spinner("Loading pipeline tickets..."):
                success, message = load_pipeline_tickets()
            
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    else:
        st.success("✅ Pipeline Data Loaded")
        st.success(f"✅ Tickets: {len(st.session_state.pipeline_tickets)}")
        
        if st.button("🔄 Refresh Data"):
            with st.spinner("Refreshing..."):
                success, message = load_pipeline_tickets()
            if success:
                st.success("Refreshed!")
                st.rerun()
    
    st.markdown('<div class="sidebar-header">🚀 System Status</div>', unsafe_allow_html=True)
    st.success("✅ S3 Vectors: Active")
    st.success("✅ Direct Search: Active")
    st.success("✅ Business Context: Enhanced")
    
    if st.session_state.pipeline_tickets:
        st.markdown('<div class="sidebar-header">📊 Risk Indicators</div>', unsafe_allow_html=True)
        
        # Calculate risk metrics
        high_urgency = len([t for t in st.session_state.pipeline_tickets if int(t['urgency_score']) >= 7])
        critical_tickets = len([t for t in st.session_state.pipeline_tickets if t['priority'] == 'Critical'])
        marketplace_risks = len([t for t in st.session_state.pipeline_tickets if 'High' in t['marketplace_impact']])
        open_tickets = len([t for t in st.session_state.pipeline_tickets if t['status'] in ['Open', 'In Progress']])
        
        st.metric("🚨 High Urgency", high_urgency, delta=f"{(high_urgency/len(st.session_state.pipeline_tickets)*100):.0f}%")
        st.metric("⚡ Critical Priority", critical_tickets)
        st.metric("🏪 Marketplace Risk", marketplace_risks)
        st.metric("📋 Open Issues", open_tickets)

# Auto-setup check
if not st.session_state.setup_complete and not st.session_state.setup_running:
    if not check_setup_status():
        st.markdown('<div style="font-family: Inter, sans-serif; font-size: 1.8rem; font-weight: 600; color: #374151; text-align: center; margin: 2rem 0;">Welcome to FinanceInsights!</div>', unsafe_allow_html=True)
        
        st.markdown('<div style="font-family: Inter, sans-serif; font-size: 1.2rem; color: #6b7280; text-align: center; margin-bottom: 2rem;">Choose your setup option:</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem; margin: 0.5rem;"><h4 style="color: #1f2937; margin-top: 0;">🏢 Use Your Jira Tickets</h4><p style="color: #6b7280; font-size: 0.9rem;">Extract and analyze your existing Jira tickets with financial context and AI insights.</p></div>', unsafe_allow_html=True)
            
            if st.button("🚀 Setup with My Jira Data", type="primary", use_container_width=True):
                st.session_state.setup_mode = "existing"
                st.session_state.setup_running = True
                st.rerun()
        
        with col2:
            st.markdown('<div style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem; margin: 0.5rem;"><h4 style="color: #1f2937; margin-top: 0;">🎯 Demo Mode</h4><p style="color: #6b7280; font-size: 0.9rem;">Generate realistic financial services demo tickets for testing and exploration.</p></div>', unsafe_allow_html=True)
            
            if st.button("📊 Setup Demo Environment", use_container_width=True):
                st.session_state.setup_mode = "demo"
                st.session_state.setup_running = True
                st.rerun()
        
        st.markdown("---")
        st.markdown('<div style="font-family: Inter, sans-serif; font-size: 0.9rem; color: #6b7280; text-align: center;"><strong>New to Jira?</strong> Choose Demo Mode to explore FinanceInsights with sample financial services tickets.</div>', unsafe_allow_html=True)
        
    else:
        st.session_state.setup_complete = True
        st.rerun()

# Show setup progress
if st.session_state.setup_running:
    mode = st.session_state.get('setup_mode', 'existing')
    mode_text = "Demo Environment" if mode == "demo" else "Jira Integration"
    
    st.markdown(f'<div style="font-family: Inter, sans-serif; font-size: 1.8rem; font-weight: 600; color: #374151; text-align: center; margin: 2rem 0;">Setting up {mode_text}...</div>', unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    with st.spinner(f"Running {mode_text.lower()} setup..."):
        if mode == "demo":
            status_text.text("Generating demo financial tickets...")
            progress_bar.progress(30)
        else:
            status_text.text("Extracting your Jira tickets...")
            progress_bar.progress(20)
        
        success, message = run_initial_setup(mode)
        
        if success:
            progress_bar.progress(100)
            status_text.text("Setup complete!")
            st.success(message)
            
            if mode == "demo":
                st.info("🎉 Demo mode ready! You now have 100+ realistic financial services tickets to explore.")
            else:
                st.info("✅ Your Jira tickets are now enhanced with AI-powered financial risk analysis.")
            
            st.session_state.setup_complete = True
            st.session_state.setup_running = False
            st.balloons()
            time.sleep(2)
            st.rerun()
        else:
            st.error(message)
            st.session_state.setup_running = False
            
            # Show helpful error guidance
            if "jira" in message.lower() or "connection" in message.lower():
                st.warning("💡 **Tip**: If you're having Jira connection issues, try Demo Mode to explore the application first.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Retry Setup"):
                    st.rerun()
            with col2:
                if st.button("🔙 Back to Options"):
                    for key in ['setup_running', 'setup_mode']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

# Main content
elif not st.session_state.pipeline_tickets:
    st.markdown('<div style="font-family: Inter, sans-serif; font-size: 1.8rem; font-weight: 600; color: #374151; text-align: center; margin: 2rem 0;">Load pipeline data to analyze escalation patterns</div>', unsafe_allow_html=True)
    st.info("Click 'Load Pipeline Data' to fetch your processed Jira tickets.")
    
else:
    st.markdown('<div style="font-family: Inter, sans-serif; font-size: 1.8rem; font-weight: 600; color: #374151; text-align: center; margin: 2rem 0;">Analyze escalation patterns and business risks</div>', unsafe_allow_html=True)
    
    # Sample questions
    sample_questions = ["Select a sample question..."] + FINANCIAL_CONFIG['sample_questions']
    
    selected_sample = st.selectbox("💡 Business Intelligence Questions:", sample_questions)
    
    # Question input
    default_question = selected_sample if selected_sample != "Select a sample question..." else ""
    question = st.text_input(
        "Your question:",
        value=default_question,
        placeholder="e.g., What patterns indicate escalation risk in our marketplace?"
    )
    
    if question:
        with st.spinner("🔍 Analyzing patterns with hybrid search..."):
            # Hybrid search
            search_results = hybrid_search(question)
            
            if search_results:
                # Generate business analysis
                analysis = generate_business_analysis(question, search_results)
                
                # Display results
                st.markdown('<div style="font-family: Inter, sans-serif; font-size: 1.5rem; font-weight: 700; color: #1f2937; margin: 2rem 0 1rem 0;">📊 Business Intelligence Analysis</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="analysis-text">{analysis}</div>', unsafe_allow_html=True)
                
                st.markdown(f'<div style="font-family: Inter, sans-serif; font-size: 1.5rem; font-weight: 700; color: #1f2937; margin: 2rem 0 1rem 0;">🎫 Related Tickets ({len(search_results)} found)</div>', unsafe_allow_html=True)
                
                for i, result in enumerate(search_results):
                    ticket = result['ticket']
                    similarity = result['similarity']
                    source = result['source']
                    
                    # Color code by urgency
                    urgency = int(ticket['urgency_score'])
                    if urgency >= 8:
                        urgency_color = "🔴"
                    elif urgency >= 6:
                        urgency_color = "🟡"
                    else:
                        urgency_color = "🟢"
                    
                    with st.expander(f"{urgency_color} **Ticket {i+1}:** {ticket['id']} - {ticket['summary']} *({source})*"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**Priority:** {ticket['priority']}")
                            st.write(f"**Status:** {ticket['status']}")
                            st.write(f"**Urgency:** {ticket['urgency_score']}/10")
                        with col2:
                            st.write(f"**Assignee:** {ticket['assignee']}")
                            st.write(f"**Similarity:** {similarity:.1%}")
                            st.write(f"**Source:** {source}")
                        with col3:
                            st.write(f"**Marketplace:** {ticket['marketplace_impact']}")
                            st.write(f"**Customer:** {ticket['customer_impact']}")
                        
                        st.write("**Summary:**")
                        st.write(ticket['summary'])
                
                # Save to history
                st.session_state.search_history.append({
                    'question': question,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'results_count': len(search_results),
                    'source_mix': f"{len([r for r in search_results if r['source'] == 'S3 Vectors'])} vectors, {len([r for r in search_results if r['source'] == 'Direct Search'])} direct"
                })
            else:
                st.warning("No relevant patterns found in current data.")

# Search history
if st.session_state.search_history:
    with st.expander("📝 Analysis History", expanded=False):
        for item in reversed(st.session_state.search_history[-5:]):
            st.write(f"**{item['timestamp']}** - {item['question']}")
            st.write(f"   Results: {item['results_count']} ({item['source_mix']})")

# Footer
st.markdown("---")
st.markdown('<div class="footer-text">💡 <strong>Financial Intelligence</strong> - S3 Vectors + Direct Search + Risk Analysis for financial services compliance</div>', unsafe_allow_html=True)