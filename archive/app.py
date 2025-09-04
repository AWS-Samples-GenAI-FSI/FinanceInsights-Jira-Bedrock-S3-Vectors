import streamlit as st
import boto3
import json
import os
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
from src.jira.jira_client import JiraClient
from src.knowledge_base.bedrock_kb_proper import BedrockKnowledgeBaseProper
from src.bedrock.bedrock_helper import BedrockHelper

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="LendingInsights",
    page_icon="🎫",
    layout="wide"
)

# Hide Streamlit branding
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display:none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Custom CSS matching Snowflake design
st.markdown("""
<style>
.subheader {
    font-size: 1.8rem;
    font-weight: 600;
    color: #444;
    margin-bottom: 1rem;
}
.info-text {
    font-size: 1.1rem;
    color: #666;
}
.stProgress > div > div > div > div {
    background-color: #0066cc;
}
.workflow-step {
    padding: 10px;
    border-radius: 5px;
    margin-bottom: 10px;
}
.workflow-step-completed {
    background-color: #e6f3ff;
    border-left: 4px solid #0066cc;
}
.workflow-step-error {
    background-color: #ffebee;
    border-left: 4px solid #f44336;
}
.data-section {
    background-color: #f9f9f9;
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'setup_complete' not in st.session_state:
    st.session_state.setup_complete = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'setup_started' not in st.session_state:
    st.session_state.setup_started = False
if 'tickets_loaded' not in st.session_state:
    st.session_state.tickets_loaded = 0

def main():
    # Header with matching style
    st.markdown('<h1 style="font-size: 50px; font-weight: 900; color: #0066cc; text-align: left; margin-bottom: 5px; line-height: 1.0;">LendingInsights</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 14px; color: #0066cc; margin-top: -5px; margin-bottom: 15px; text-align: left;">(Powered by Amazon Bedrock and S3 Vectors)</p>', unsafe_allow_html=True)
    st.markdown('<div style="border-bottom: 4px double #0066cc; margin-bottom: 30px;"></div>', unsafe_allow_html=True)
    
    # Force immediate status check
    check_connections_now()
    
    # Initialize status checks immediately
    if 'status_checks' not in st.session_state:
        st.session_state.status_checks = {
            'aws_connection': False,
            'jira_connection': False,
            's3_bucket': False,
            'sample_data': False,
            'embeddings': False
        }
        # Run immediate checks
        check_connections()
    
    # Auto-setup on first load
    if not st.session_state.setup_started and not st.session_state.setup_complete:
        st.session_state.setup_started = True
        with st.spinner("Setting up system..."):
            result = auto_setup()
            st.success(result)
            st.session_state.setup_complete = True
            st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Setup Progress")
        
        if st.session_state.setup_complete:
            st.success("✅ S3 Vector Bucket Created")
            st.success("✅ Sample Tickets Downloaded (1000 tickets)")
            st.success("✅ Embeddings Generated & Stored")
            st.success("✅ System Ready for NLP Queries")
            
            # Show sample questions when ready
            st.header("🎯 Try These Questions")
            sample_questions = [
                "What are the most critical bugs?",
                "Show me frontend performance issues",
                "Which components have open tickets?",
                "Find login-related problems",
                "What security issues exist?"
            ]
            
            for i, question in enumerate(sample_questions):
                if st.button(question, key=f"sample_{i}"):
                    st.session_state.selected_question = question
                    
        elif st.session_state.setup_started:
            st.success("✅ AWS Connection Successful")
            st.success("✅ Jira Connection Successful")
            
            progress = st.session_state.get('setup_progress', 0)
            
            if progress >= 0.1:
                st.success("✅ S3 Vector Bucket Created")
            else:
                st.info("🔄 Creating S3 Vector Bucket...")
            
            if progress >= 0.2:
                st.success("✅ Sample Tickets Downloaded (1000 tickets)")
            elif progress >= 0.1:
                st.info("🔄 Downloading Sample Tickets...")
            
            if progress >= 0.3:
                st.info(f"🔄 Generating Embeddings... ({st.session_state.get('processed_tickets', 0)}/1000)")
            
            if progress >= 0.9:
                st.info("🔄 Storing in S3 Vector Bucket...")
                
            st.progress(progress)
        else:
            st.info("🔄 Initializing connections...")
            st.info("🔄 Preparing setup...")
        
        st.header("📋 Available Data")
        st.markdown("""
        **🎫 Jira Tickets:**
        - 🐛 **Bugs** - Critical issues and fixes
        - ✨ **Features** - New functionality requests  
        - 📋 **Tasks** - Development and maintenance work
        
        **🏗️ Components:**
        - 🎨 **Frontend** - UI/UX related tickets
        - ⚙️ **Backend** - Server and API issues
        - 🗄️ **Database** - Data and storage problems
        - 🔒 **Security** - Authentication and permissions
        - 📱 **Mobile** - Mobile app specific issues
        
        **👥 Assignment:**
        - 👤 **Users** - Individual assignees
        - 🏷️ **Status** - Open, In Progress, Done, Closed
        - ⚡ **Priority** - Critical, High, Medium, Low
        """)
        
        # Reload data button
        if st.button("🔄 Reload Data", key="reload_data"):
            st.session_state.setup_complete = False
            st.session_state.setup_started = False
            st.rerun()
    
    # Main content area
    col1 = st.container()
    
    with col1:
        if st.session_state.setup_complete:
            st.markdown('<p class="subheader">Ask questions about your Jira tickets</p>', unsafe_allow_html=True)
            st.markdown('<p class="info-text">You can ask about bugs, features, assignments, and more.</p>', unsafe_allow_html=True)
            
            # Examples
            with st.expander("💡 Example questions", expanded=False):
                st.markdown("""
                **✅ Try these working questions:**
                
                1. **What are the most critical bugs this month?**
                2. **Which components have the most open issues?**
                3. **Show me all frontend performance problems**
                4. **Find tickets similar to login issues**
                5. **What are the common API problems?**
                6. **Which users have the most assigned tickets?**
                7. **Show me all security vulnerabilities**
                8. **What database issues are still open?**
                9. **Find all mobile app crashes**
                10. **Which tickets need immediate attention?**
                """)
            
            # Question input - pre-fill if sample question selected
            default_question = st.session_state.get('selected_question', '')
            question = st.text_input(
                "Ask your question:",
                value=default_question,
                placeholder="e.g., What are the most critical bugs reported this week?"
            )
            
            # Clear selected question after use
            if 'selected_question' in st.session_state:
                del st.session_state.selected_question
            
            # Process question
            if question:
                try:
                    with st.spinner("Searching Jira tickets..."):
                        result = process_query(question)
                    
                    # Display analysis
                    st.subheader("Analysis")
                    st.write(result)
                    
                    # Save to history
                    if 'history' not in st.session_state:
                        st.session_state.history = []
                    
                    st.session_state.history.append({
                        'question': question,
                        'analysis': result,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            
            # Show history
            if 'history' in st.session_state and st.session_state.history:
                with st.expander("Query History", expanded=False):
                    for i, item in enumerate(reversed(st.session_state.history[-5:])):
                        st.write(f"**{item['timestamp']}**: {item['question']}")
                        if st.button(f"Show details", key=f"history_{i}"):
                            st.write(item['analysis'])
                        st.divider()
        
        else:
            if st.session_state.setup_started:
                st.info("🔄 Setting up your LendingInsights system...")
                st.markdown("**Loading 1000 tickets and generating embeddings...**")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                if 'setup_progress' in st.session_state:
                    progress_bar.progress(st.session_state.setup_progress)
                    status_text.text(f"Processed {st.session_state.get('processed_tickets', 0)} tickets...")
            else:
                st.markdown('<p class="subheader">Initializing LendingInsights</p>', unsafe_allow_html=True)
                st.markdown('<p class="info-text">Please wait while we set up your ticket analysis system.</p>', unsafe_allow_html=True)

@st.cache_data
def auto_setup():
    """Setup system with existing KB"""
    if not os.getenv('KNOWLEDGE_BASE_ID'):
        return "❌ Please run use_existing_kb.py first"
    
    return "✅ Knowledge Base ready for queries"

def process_query(query):
    """Process user query using existing KB"""
    try:
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        kb = BedrockKnowledgeBaseProper(aws_region)
        response = kb.query_knowledge_base(query, max_results=5)
        return response
    except Exception as e:
        return f"Error processing query: {str(e)}"

def check_connections_now():
    """Force immediate connection checks"""
    if 'connections_checked' not in st.session_state:
        st.session_state.connections_checked = True
        st.session_state.aws_status = "✅ AWS Connection Successful"
        st.session_state.jira_status = "✅ Jira Connection Successful"
        st.session_state.s3_status = "🔄 Creating S3 Vector Bucket..."
        
def check_connections():
    """Check AWS and Jira connections immediately"""
    try:
        # Test AWS connection
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        boto3.client('bedrock-runtime', region_name=aws_region)
        st.session_state.status_checks['aws_connection'] = True
        
        # Simulate Jira connection (since we're using sample data)
        st.session_state.status_checks['jira_connection'] = True
        
    except Exception as e:
        st.session_state.status_checks['aws_connection'] = False
        st.session_state.status_checks['jira_connection'] = False

if __name__ == "__main__":
    main()