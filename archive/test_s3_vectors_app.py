#!/usr/bin/env python3

import streamlit as st
import boto3
import json
from datetime import datetime
from src.vector_store.s3_vectors_native import S3VectorsNative

# Page config
st.set_page_config(
    page_title="S3 Vectors Test",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 S3 Vectors Test Application")
st.markdown("Testing S3 Vector Engine capabilities")

# Initialize session state
if 'test_results' not in st.session_state:
    st.session_state.test_results = []

def test_s3_vectors():
    """Test S3 Vectors creation and operations"""
    
    with st.expander("🔧 Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            region = st.selectbox("AWS Region", 
                ["us-east-1", "us-west-2", "eu-west-1"], 
                index=0)
            
        with col2:
            bucket_name = st.text_input("Vector Bucket Name", 
                value="test-s3-vectors-bucket")
    
    if st.button("🚀 Test S3 Vectors Creation"):
        
        with st.spinner("Testing S3 Vectors..."):
            results = []
            
            # Test 1: Check if S3 Vectors service exists
            st.write("### Test 1: Service Availability")
            try:
                session = boto3.Session()
                available_services = session.get_available_services()
                
                if 's3vectors' in available_services:
                    st.success("✅ S3 Vectors service available")
                    results.append("✅ S3 Vectors service found")
                else:
                    st.error("❌ S3 Vectors service not available")
                    st.write(f"Available services: {available_services[:10]}...")
                    results.append("❌ S3 Vectors service not found")
                    return results
                    
            except Exception as e:
                st.error(f"❌ Error checking services: {e}")
                results.append(f"❌ Service check failed: {e}")
                return results
            
            # Test 2: Try to create S3 Vectors client
            st.write("### Test 2: Client Creation")
            try:
                s3vectors = S3VectorsNative(
                    region=region,
                    vector_bucket_name=bucket_name
                )
                st.success("✅ S3 Vectors client created")
                results.append("✅ Client creation successful")
                
            except Exception as e:
                st.error(f"❌ Client creation failed: {e}")
                results.append(f"❌ Client creation failed: {e}")
                return results
            
            # Test 3: Try to create vector store
            st.write("### Test 3: Vector Store Creation")
            try:
                success = s3vectors.create_vector_store()
                if success:
                    st.success("✅ Vector store created")
                    results.append("✅ Vector store creation successful")
                else:
                    st.error("❌ Vector store creation failed")
                    results.append("❌ Vector store creation failed")
                    
            except Exception as e:
                st.error(f"❌ Vector store error: {e}")
                results.append(f"❌ Vector store error: {e}")
            
            # Test 4: Test sample data upload
            st.write("### Test 4: Sample Data Upload")
            try:
                sample_data = [{
                    'chunk_id': 'test-001',
                    'embedding': [0.1] * 1536,  # Dummy embedding
                    'text': 'Test ticket content',
                    'key': 'TEST-001',
                    'summary': 'Test summary',
                    'status': 'Open',
                    'priority': 'High',
                    'component': 'Test'
                }]
                
                success = s3vectors.store_vectors(sample_data)
                if success:
                    st.success("✅ Sample data uploaded")
                    results.append("✅ Data upload successful")
                else:
                    st.error("❌ Data upload failed")
                    results.append("❌ Data upload failed")
                    
            except Exception as e:
                st.error(f"❌ Data upload error: {e}")
                results.append(f"❌ Data upload error: {e}")
            
            # Test 5: Test vector search
            st.write("### Test 5: Vector Search")
            try:
                query_embedding = [0.1] * 1536  # Dummy query
                results_search = s3vectors.search_similar(query_embedding, top_k=5)
                
                if results_search:
                    st.success(f"✅ Search returned {len(results_search)} results")
                    results.append(f"✅ Search successful: {len(results_search)} results")
                else:
                    st.warning("⚠️ Search returned no results")
                    results.append("⚠️ Search returned no results")
                    
            except Exception as e:
                st.error(f"❌ Search error: {e}")
                results.append(f"❌ Search error: {e}")
            
            st.session_state.test_results = results
            
        return results

def test_alternative_approach():
    """Test alternative S3 + Bedrock approach"""
    
    st.write("## Alternative: Direct S3 + Bedrock Integration")
    
    if st.button("🔄 Test S3 + Bedrock Approach"):
        
        with st.spinner("Testing S3 + Bedrock..."):
            
            # Test regular S3 bucket creation
            st.write("### Test: Regular S3 Bucket")
            try:
                s3_client = boto3.client('s3', region_name='us-east-1')
                bucket_name = "test-regular-s3-vectors"
                
                s3_client.create_bucket(Bucket=bucket_name)
                st.success(f"✅ Regular S3 bucket created: {bucket_name}")
                
                # Upload sample document
                sample_doc = {
                    "text": "This is a test Jira ticket about login issues",
                    "metadata": {
                        "ticket_id": "TEST-001",
                        "component": "Authentication",
                        "priority": "High"
                    }
                }
                
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key="tickets/TEST-001.json",
                    Body=json.dumps(sample_doc),
                    ContentType="application/json"
                )
                
                st.success("✅ Sample document uploaded to S3")
                
                # Test Bedrock embedding
                bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
                
                response = bedrock_runtime.invoke_model(
                    modelId='amazon.titan-embed-text-v1',
                    body=json.dumps({
                        "inputText": sample_doc["text"]
                    })
                )
                
                embedding = json.loads(response['body'].read())['embedding']
                st.success(f"✅ Bedrock embedding generated: {len(embedding)} dimensions")
                
            except Exception as e:
                st.error(f"❌ S3 + Bedrock test failed: {e}")

# Main interface
col1, col2 = st.columns(2)

with col1:
    st.header("🧪 S3 Vectors Native Test")
    test_s3_vectors()

with col2:
    st.header("🔄 Alternative Approach")
    test_alternative_approach()

# Results display
if st.session_state.test_results:
    st.header("📊 Test Results")
    for result in st.session_state.test_results:
        if "✅" in result:
            st.success(result)
        elif "❌" in result:
            st.error(result)
        else:
            st.warning(result)

# Service availability check
st.header("🔍 AWS Service Check")
if st.button("Check Available Services"):
    session = boto3.Session()
    services = session.get_available_services()
    
    st.write(f"**Total services available:** {len(services)}")
    
    # Check for vector-related services
    vector_services = [s for s in services if 'vector' in s.lower()]
    if vector_services:
        st.success(f"Vector services found: {vector_services}")
    else:
        st.warning("No vector services found")
    
    # Show first 20 services
    st.write("**First 20 services:**")
    for service in services[:20]:
        st.write(f"- {service}")