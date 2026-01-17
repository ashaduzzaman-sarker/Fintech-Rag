"""
Streamlit UI for FinTech RAG Knowledge Assistant.

Run with: streamlit run ui/streamlit_app.py
"""

import streamlit as st
import requests
from typing import Dict, Any
import json
from datetime import datetime


# Configuration
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")
API_V1 = f"{API_BASE_URL}/api/v1"


# Page config
st.set_page_config(
    page_title="FinTech RAG Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .citation-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .confidence-high {
        color: #28a745;
        font-weight: bold;
    }
    .confidence-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .confidence-low {
        color: #dc3545;
        font-weight: bold;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def check_api_health() -> Dict[str, Any]:
    """Check API health status."""
    try:
        response = requests.get(f"{API_V1}/health", timeout=5)
        return response.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}


def query_rag(question: str, top_k: int = 5, include_confidence: bool = True) -> Dict[str, Any]:
    """Query the RAG system."""
    try:
        response = requests.post(
            f"{API_V1}/query",
            json={
                "question": question,
                "top_k": top_k,
                "include_confidence": include_confidence
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def ingest_documents(directory_path: str, recursive: bool = True) -> Dict[str, Any]:
    """Ingest documents."""
    try:
        response = requests.post(
            f"{API_V1}/ingest",
            json={
                "directory_path": directory_path,
                "recursive": recursive,
                "use_advanced_chunking": True
            },
            timeout=300
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def get_system_stats() -> Dict[str, Any]:
    """Get system statistics."""
    try:
        response = requests.get(f"{API_V1}/stats", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# Sidebar
# ============================================================================

with st.sidebar:
    st.markdown("## 🏦 FinTech RAG")
    st.markdown("### Knowledge Assistant")
    
    st.markdown("---")
    
    # System Health
    st.markdown("#### System Status")
    health = check_api_health()
    
    if health.get("status") == "healthy":
        st.success("✓ System Healthy")
    elif health.get("status") == "degraded":
        st.warning("⚠ System Degraded")
    else:
        st.error("✗ System Unhealthy")
    
    if "components" in health:
        with st.expander("Component Status"):
            for component, status in health["components"].items():
                st.text(f"{component}: {status}")
    
    st.markdown("---")
    
    # Settings
    st.markdown("#### Query Settings")
    top_k = st.slider("Number of results", 1, 20, 5)
    show_context = st.checkbox("Show context documents", value=True)
    show_confidence = st.checkbox("Show confidence", value=True)
    
    st.markdown("---")
    
    # Sample queries
    st.markdown("#### Sample Queries")
    sample_queries = [
        "What are our AML transaction monitoring thresholds?",
        "What is the minimum CET1 ratio under Basel III?",
        "What documents are required for customer identification?",
        "What is our maximum Value at Risk limit?",
        "Explain our KYC procedures for high-risk customers",
    ]
    
    selected_sample = st.selectbox(
        "Try a sample query:",
        [""] + sample_queries,
        index=0
    )


# ============================================================================
# Main Content
# ============================================================================

st.markdown('<div class="main-header">🏦 FinTech Knowledge Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Ask questions about compliance, risk management, and regulations</div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["💬 Query", "📚 Ingest", "📊 Statistics"])


# ============================================================================
# Tab 1: Query Interface
# ============================================================================

with tab1:
    # Query input
    question = st.text_area(
        "Ask a question:",
        value=selected_sample if selected_sample else "",
        height=100,
        placeholder="e.g., What are our Basel III capital requirements?"
    )
    
    col1, col2 = st.columns([1, 5])
    with col1:
        submit_button = st.button("🔍 Ask", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("Clear", use_container_width=True)
    
    if clear_button:
        st.rerun()
    
    if submit_button and question:
        with st.spinner("🤔 Thinking..."):
            result = query_rag(question, top_k=top_k, include_confidence=show_confidence)
        
        if "error" in result:
            st.error(f"❌ Error: {result['error']}")
        else:
            # Answer
            st.markdown("### 📝 Answer")
            st.markdown(result.get("answer", "No answer generated."))
            
            # Confidence
            if show_confidence and "confidence" in result:
                confidence = result["confidence"]
                confidence_level = result.get("confidence_level", "unknown")
                
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Confidence", f"{confidence:.0%}")
                with col2:
                    if confidence_level == "high":
                        st.markdown('<p class="confidence-high">High Confidence</p>', unsafe_allow_html=True)
                    elif confidence_level == "medium":
                        st.markdown('<p class="confidence-medium">Medium Confidence</p>', unsafe_allow_html=True)
                    else:
                        st.markdown('<p class="confidence-low">Low Confidence</p>', unsafe_allow_html=True)
                with col3:
                    st.metric("Response Time", f"{result.get('processing_time', 0):.2f}s")
            
            # Citations
            if result.get("citations"):
                st.markdown("---")
                st.markdown("### 📚 Sources")
                
                for i, citation in enumerate(result["citations"], 1):
                    st.markdown(f"""
                    <div class="citation-box">
                        <strong>Source {i}:</strong> {citation['source']}<br>
                        <strong>Page:</strong> {citation['page']}<br>
                        <strong>Type:</strong> {citation['type']}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Context documents
            if show_context and result.get("context_used"):
                st.markdown("---")
                st.markdown("### 📄 Context Documents")
                
                for i, doc in enumerate(result["context_used"], 1):
                    with st.expander(f"Document {i}: {doc['source']} (Score: {doc['score']:.3f})"):
                        st.text(f"Source: {doc['source']}")
                        st.text(f"Page: {doc['page']}")
                        st.progress(doc['score'])
            
            # Metadata
            with st.expander("🔍 Query Metadata"):
                st.json({
                    "question": result.get("question"),
                    "model": result.get("model"),
                    "processing_time": result.get("processing_time"),
                    "num_citations": len(result.get("citations", [])),
                    "num_context_docs": len(result.get("context_used", []))
                })


# ============================================================================
# Tab 2: Document Ingestion
# ============================================================================

with tab2:
    st.markdown("### 📚 Ingest Documents")
    st.info("Upload documents to make them searchable in the RAG system.")
    
    directory_path = st.text_input(
        "Document Directory Path:",
        value="./data/raw",
        help="Path to directory containing documents (PDF, DOCX, TXT)"
    )
    
    recursive = st.checkbox("Search subdirectories recursively", value=True)
    
    if st.button("📥 Start Ingestion", type="primary"):
        with st.spinner("🔄 Processing documents... This may take several minutes."):
            result = ingest_documents(directory_path, recursive)
        
        if "error" in result:
            st.error(f"❌ Ingestion failed: {result['error']}")
        elif result.get("status") == "success":
            st.success(f"✅ {result.get('message')}")
            
            # Stats
            stats = result.get("stats", {})
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Files Processed", stats.get("total_files", 0))
            with col2:
                st.metric("Chunks Created", stats.get("total_chunks", 0))
            with col3:
                st.metric("Total Tokens", f"{stats.get('total_tokens', 0):,}")
            with col4:
                st.metric("Processing Time", f"{result.get('processing_time', 0):.1f}s")
            
            with st.expander("📊 Detailed Statistics"):
                st.json(stats)
        else:
            st.warning(result.get("message", "Unknown status"))
    
    st.markdown("---")
    st.markdown("#### 📖 Supported Formats")
    st.markdown("- PDF (`.pdf`)")
    st.markdown("- Word Documents (`.docx`)")
    st.markdown("- Text Files (`.txt`, `.md`)")


# ============================================================================
# Tab 3: System Statistics
# ============================================================================

with tab3:
    st.markdown("### 📊 System Statistics")
    
    if st.button("🔄 Refresh Stats"):
        st.rerun()
    
    stats = get_system_stats()
    
    if "error" in stats:
        st.error(f"Failed to load statistics: {stats['error']}")
    else:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Documents Indexed",
                f"{stats.get('total_documents_indexed', 0):,}"
            )
        with col2:
            st.metric(
                "Queries Processed",
                f"{stats.get('total_queries_processed', 0):,}"
            )
        with col3:
            st.metric(
                "Avg Query Time",
                f"{stats.get('avg_query_time', 0):.2f}s"
            )
        with col4:
            uptime_hours = stats.get('uptime_seconds', 0) / 3600
            st.metric(
                "Uptime",
                f"{uptime_hours:.1f}h"
            )
        
        # Detailed stats
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Vector Store Stats")
            vector_stats = stats.get("vector_store_stats", {})
            if vector_stats:
                st.json(vector_stats)
            else:
                st.info("No vector store statistics available")
        
        with col2:
            st.markdown("#### BM25 Store Stats")
            bm25_stats = stats.get("bm25_store_stats", {})
            if bm25_stats:
                st.json(bm25_stats)
            else:
                st.info("No BM25 statistics available")


# ============================================================================
# Footer
# ============================================================================

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; padding: 2rem 0;">
        <p>🏦 FinTech RAG Knowledge Assistant | Built with ❤️ using LangChain, Pinecone, and OpenAI</p>
        <p style="font-size: 0.9rem;">
            <a href="{}/docs" target="_blank">API Documentation</a> | 
            <a href="https://github.com/your-org/fintech-rag" target="_blank">GitHub</a>
        </p>
    </div>
    """.format(API_BASE_URL),
    unsafe_allow_html=True
)