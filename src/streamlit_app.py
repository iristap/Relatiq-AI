import streamlit as st
import asyncio
import os
import sys

# Add the project root to the path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ingest import extract_info, save_to_neo4j

st.set_page_config(page_title="Relatiq-AI Ingestion", layout="wide")

st.title("Relatiq-AI - Data Ingestion Interface")

st.markdown("""
Paste a news article below to ingest it into the Neo4j Knowledge Graph.
The system will extract metadata, identify entities, and analyze sentiment.
""")

# Initialize Session State
if "extraction_results" not in st.session_state:
    st.session_state.extraction_results = None

# Text Input
article_text = st.text_area("News Article Content", height=300)

if st.button("Extract Article"):
    if not article_text:
        st.warning("Please enter some text.")
    else:
        with st.spinner("Analyzing... This may take a moment."):
            try:
                # Run the async extract_info function
                results = asyncio.run(extract_info(article_text))
                st.session_state.extraction_results = results
                st.success("Analysis Complete! Review the results below and click 'Confirm Ingestion' to save.")
            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")

if st.session_state.extraction_results:
    results = st.session_state.extraction_results
    
    # Display Results
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Extracted Metadata")
        st.json(results.get("metadata", {}))
        
        if "metadata_error" in results:
            st.error(f"Metadata Error: {results['metadata_error']}")

    with col2:
        st.subheader("Sentiment Analysis")
        sentiment_data = results.get("sentiment", [])
        if sentiment_data:
            for item in sentiment_data:
                color = "green" if item.sentiment == "Positive" else "red" if item.sentiment == "Negative" else "gray"
                st.markdown(f"**{item.entity_name}**: :{color}[{item.sentiment}]")
        else:
            st.info("No sentiment entities found.")
            
        if "sentiment_error" in results:
            st.error(f"Sentiment Error: {results['sentiment_error']}")

    st.subheader("Graph Data")
    graph_docs = results.get("graph_documents", [])
    if graph_docs:
        nodes = []
        relationships = []
        for doc in graph_docs:
            for node in doc.nodes:
                nodes.append({"id": node.id, "type": node.type})
            for rel in doc.relationships:
                relationships.append({
                    "source": rel.source.id,
                    "target": rel.target.id,
                    "type": rel.type,
                    "properties": rel.properties
                })
        
        st.write(f"**Nodes ({len(nodes)}):**")
        st.dataframe(nodes)
        
        st.write(f"**Relationships ({len(relationships)}):**")
        st.dataframe(relationships)
    else:
        st.info("No graph data extracted.")

    # Confirmation Button
    if st.button("Confirm & Ingest to Neo4j", type="primary"):
        with st.spinner("Saving to Neo4j..."):
            try:
                asyncio.run(save_to_neo4j(results))
                st.success("Successfully ingested into Neo4j!")
                # Clear state
                st.session_state.extraction_results = None
                # Rerun to clear UI
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save to Neo4j: {e}")
