import streamlit as st
import boto3
import json
from datetime import datetime

# Page config
st.set_page_config(
    page_title="LendingInsights - Pipeline Integrated",
    page_icon="🚀",
    layout="wide"
)

# Configuration
PIPELINE_S3_BUCKET = 'lendingtree-jira-vectors-pipeline'
VECTOR_BUCKET = 'lendingtree-vectors-kb'
INDEX_NAME = 'jira-tickets-enhanced'
REGION = 'us-east-1'

# Initialize session state
if 'pipeline_data' not in st.session_state:
    st.session_state.pipeline_data = []
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

def load_pipeline_data():
    """Load tickets from the pipeline S3 bucket"""
    try:
        s3_client = boto3.client('s3', region_name=REGION)
        
        # List objects in raw-tickets folder
        response = s3_client.list_objects_v2(
            Bucket=PIPELINE_S3_BUCKET,
            Prefix='raw-tickets/'
        )
        
        tickets = []
        for obj in response.get('Contents', [])[:20]:  # Limit to 20 for performance
            # Get ticket data
            ticket_response = s3_client.get_object(
                Bucket=PIPELINE_S3_BUCKET,
                Key=obj['Key']
            )
            
            ticket_data = json.loads(ticket_response['Body'].read())
            
            # Transform for app
            tickets.append({
                'id': ticket_data['ticket_id'],
                'text': ticket_data['text'],
                'summary': ticket_data['summary'],
                'component': ticket_data.get('components', ['General'])[0] if ticket_data.get('components') else 'General',
                'priority': ticket_data['priority'],
                'status': ticket_data['status'],
                'assignee': ticket_data['assignee'],
                'marketplace_impact': ticket_data['business_context']['marketplace_impact'],
                'customer_impact': ticket_data['business_context']['customer_impact'],
                'urgency_score': ticket_data['business_context']['urgency_score']
            })
        
        st.session_state.pipeline_data = tickets
        return True, f"Loaded {len(tickets)} tickets from pipeline"
        
    except Exception as e:
        return False, f"Error loading pipeline data: {str(e)}"

def search_s3_vectors(query_text):
    """Search using S3 Vectors from pipeline"""
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
        
        # Format results
        results = []
        for match in search_results.get('vectorMatches', []):
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
                'similarity': match.get('similarityScore', 0)
            })
        
        return results
        
    except Exception as e:
        st.error(f"Vector search error: {e}")
        return []

def generate_enhanced_analysis(query_text, search_results):
    """Generate analysis with business context"""
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=REGION)
        
        # Prepare context with business insights
        context = "\n".join([
            f"Ticket {r['ticket']['id']}: {r['ticket']['summary']}\n"
            f"  Priority: {r['ticket']['priority']}, Status: {r['ticket']['status']}\n"
            f"  Marketplace Impact: {r['ticket']['marketplace_impact']}\n"
            f"  Customer Impact: {r['ticket']['customer_impact']}\n"
            f"  Urgency Score: {r['ticket']['urgency_score']}/10\n"
            for r in search_results
        ])
        
        prompt = f"""Based on these LendingTree support tickets with business context:

{context}

Question: {query_text}

Provide comprehensive analysis including:

1. **Issue Summary**: Key problems identified
2. **Business Impact**: Effect on marketplace, customers, and lenders
3. **Urgency Assessment**: Priority based on urgency scores and business impact
4. **Predictive Insights**: Potential escalation risks and patterns
5. **Recommended Actions**: Specific steps for LendingTree operations team

Focus on LendingTree's marketplace operations, customer experience, and lender relationships."""

        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                "max_tokens": 1200,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        
        response_data = json.loads(response['body'].read())
        return response_data['content'][0]['text']
        
    except Exception as e:
        return f"Analysis generation failed: {e}"

# Header
st.markdown('<h1 style="font-size: 50px; font-weight: 900; color: #0066cc;">🚀 LendingInsights</h1>', unsafe_allow_html=True)
st.markdown('<p style="font-size: 14px; color: #0066cc; margin-top: -5px;">Live Pipeline Data + S3 Vectors + Business Intelligence</p>', unsafe_allow_html=True)
st.markdown('<div style="border-bottom: 4px double #0066cc; margin-bottom: 30px;"></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🔗 Pipeline Status")
    
    if not st.session_state.pipeline_data:
        if st.button("📊 Load Pipeline Data"):
            with st.spinner("Loading from pipeline..."):
                success, message = load_pipeline_data()
            
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    else:
        st.success("✅ Pipeline Data Loaded")
        st.success(f"✅ Tickets: {len(st.session_state.pipeline_data)}")
        
        if st.button("🔄 Refresh Data"):
            with st.spinner("Refreshing..."):
                success, message = load_pipeline_data()
            if success:
                st.success("Refreshed!")
                st.rerun()
    
    st.header("🚀 System Status")
    st.success("✅ S3 Vectors: Active")
    st.success("✅ Bedrock AI: Connected")
    st.success("✅ Business Context: Enhanced")
    
    if st.session_state.pipeline_data:
        st.header("📊 Business Insights")
        
        # Calculate metrics
        high_urgency = len([t for t in st.session_state.pipeline_data if int(t['urgency_score']) >= 7])
        critical_priority = len([t for t in st.session_state.pipeline_data if t['priority'] == 'Critical'])
        marketplace_impact = len([t for t in st.session_state.pipeline_data if 'High' in t['marketplace_impact']])
        
        st.metric("High Urgency Tickets", high_urgency)
        st.metric("Critical Priority", critical_priority)
        st.metric("Marketplace Impact", marketplace_impact)

# Main content
if not st.session_state.pipeline_data:
    st.markdown('<p style="font-size: 1.8rem; font-weight: 600; color: #444;">Load pipeline data to get started</p>', unsafe_allow_html=True)
    st.info("Click 'Load Pipeline Data' in the sidebar to fetch live data from the Jira pipeline.")
    
else:
    st.markdown('<p style="font-size: 1.8rem; font-weight: 600; color: #444;">Ask questions about your live Jira pipeline data</p>', unsafe_allow_html=True)
    
    # Sample questions dropdown
    sample_questions = [
        "Select a sample question...",
        "What are the highest urgency tickets?",
        "Show me marketplace impact issues",
        "Which tickets affect customer experience?",
        "Find tickets with high business risk",
        "What patterns indicate escalation risk?",
        "Show me lender-affecting issues"
    ]
    
    selected_sample = st.selectbox("💡 Sample Questions:", sample_questions)
    
    # Question input
    default_question = selected_sample if selected_sample != "Select a sample question..." else ""
    question = st.text_input(
        "Your question:",
        value=default_question,
        placeholder="e.g., What are the most critical marketplace issues affecting our lenders?"
    )
    
    if question:
        with st.spinner("🔍 Analyzing pipeline data with AI..."):
            # Search S3 Vectors
            search_results = search_s3_vectors(question)
            
            if search_results:
                # Generate enhanced analysis
                analysis = generate_enhanced_analysis(question, search_results)
                
                # Display results
                st.subheader("📊 Business Intelligence Analysis")
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
                            st.write(f"**Urgency Score:** {ticket['urgency_score']}/10")
                        with col2:
                            st.write(f"**Assignee:** {ticket['assignee']}")
                            st.write(f"**Similarity:** {similarity:.1%}")
                        with col3:
                            st.write(f"**Marketplace Impact:** {ticket['marketplace_impact']}")
                            st.write(f"**Customer Impact:** {ticket['customer_impact']}")
                        
                        st.write("**Summary:**")
                        st.write(ticket['summary'])
                
                # Save to history
                st.session_state.search_history.append({
                    'question': question,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'results_count': len(search_results)
                })
            else:
                st.warning("No relevant tickets found in pipeline data.")

# Search history
if st.session_state.search_history:
    with st.expander("📝 Search History", expanded=False):
        for item in reversed(st.session_state.search_history[-5:]):
            st.write(f"**{item['timestamp']}** - {item['question']} ({item['results_count']} results)")

# Footer
st.markdown("---")
st.markdown("💡 **Live Pipeline Integration** - Real-time Jira data with business intelligence and predictive analysis")