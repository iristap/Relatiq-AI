import streamlit as st
import pandas as pd
from streamlit_agraph import agraph, Node, Edge, Config
from src.graph_db import db

st.set_page_config(layout="wide", page_title="Financial News Knowledge Graph")

st.title("Financial News Knowledge Graph")

# Sidebar
st.sidebar.header("Filters")

# Article Selection
article_query = "MATCH (d:Document) RETURN d.title as title ORDER BY d.date DESC"
article_results = db.query(article_query)
article_titles = [r['title'] for r in article_results]
# Changed to multiselect
selected_articles = st.sidebar.multiselect("Select Articles", article_titles, default=[])

# Search Entity
search_query = st.sidebar.text_input("Search Entity (Company, Person, Topic)", "")
min_degree = st.sidebar.slider("Minimum Degree of Separation", 1, 5, 1)

# Node & Relationship Filters
# Fetch available labels and types
labels_query = "CALL db.labels()"
types_query = "CALL db.relationshipTypes()"
available_labels = [r['label'] for r in db.query(labels_query) if r['label'] not in ['Document', 'Article']] 
available_types = [r['relationshipType'] for r in db.query(types_query)]

selected_labels = st.sidebar.multiselect("Filter Node Types", available_labels, default=available_labels)
selected_types = st.sidebar.multiselect("Filter Relationship Types", available_types, default=available_types)

# Date Filter
# Get min/max date from DB
date_range_query = "MATCH (d:Document) RETURN min(d.date) as min_date, max(d.date) as max_date"
date_result = db.query(date_range_query)
if date_result and date_result[0]['min_date']:
    min_date_str = date_result[0]['min_date'].split('T')[0]
    max_date_str = date_result[0]['max_date'].split('T')[0]
    try:
        min_date = pd.to_datetime(min_date_str).date()
        max_date = pd.to_datetime(max_date_str).date()
    except:
        min_date = pd.to_datetime("2024-01-01").date()
        max_date = pd.to_datetime("2025-12-31").date()
    
    start_date, end_date = st.sidebar.date_input(
        "Select Date Range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
else:
    st.sidebar.write("No data found.")
    start_date, end_date = None, None

# Tabs
tab1, tab2, tab3 = st.tabs(["Graph View", "Timeline View", "Company Analysis"])

with tab1:
    st.subheader("Network Visualization")
    
    # Graph Query Logic
    path_length = f"1..{min_degree}"
    
    if selected_articles:
        # Query centered on the selected articles
        # Find entities mentioned in ANY of the selected articles
        cypher_query = f"""
        MATCH (d:Document)-[:MENTIONS]->(start_node)
        WHERE d.title IN $titles
        AND labels(start_node)[0] IN $labels
        CALL apoc.path.subgraphAll(start_node, {{
            minLevel: 0,
            maxLevel: {min_degree},
            labelFilter: '+' + apoc.text.join($labels, '|+'),
            relationshipFilter: apoc.text.join($types, '|')
        }})
        YIELD nodes, relationships
        RETURN nodes, relationships
        """
        # Fallback
        cypher_query_fallback = f"""
        MATCH (d:Document)-[:MENTIONS]->(n)
        WHERE d.title IN $titles
        AND any(l IN labels(n) WHERE l IN $labels)
        OPTIONAL MATCH p = (n)-[*1..{min_degree}]-(m)
        WHERE all(x IN nodes(p) WHERE any(l IN labels(x) WHERE l IN $labels))
        AND all(x IN relationships(p) WHERE type(x) IN $types)
        RETURN p
        LIMIT 500
        """
        params = {"titles": selected_articles, "labels": selected_labels, "types": selected_types}
        
    elif search_query:
        cypher_query = f"""
        MATCH p = (n)-[*1..{min_degree}]-(m)
        WHERE toLower(n.name) CONTAINS toLower($search)
        AND all(x IN nodes(p) WHERE any(l IN labels(x) WHERE l IN $labels))
        AND all(x IN relationships(p) WHERE type(x) IN $types)
        RETURN p
        LIMIT 100
        """
        params = {"search": search_query, "labels": selected_labels, "types": selected_types}
    else:
        # Default view
        cypher_query = f"""
        MATCH (n)-[r]->(m)
        WHERE any(l IN labels(n) WHERE l IN $labels)
        AND any(l IN labels(m) WHERE l IN $labels)
        AND type(r) IN $types
        RETURN n, r, m
        LIMIT 50
        """
        params = {"labels": selected_labels, "types": selected_types}

    try:
        results = db.query(cypher_query, params)
    except Exception as e:
        st.error(f"Query Error (trying fallback): {e}")
        if selected_articles:
            try:
                results = db.query(cypher_query_fallback, params)
            except Exception as e2:
                st.error(f"Fallback Error: {e2}")
                results = []
        else:
            results = []
    
    nodes = []
    edges = []
    node_ids = set()

    for record in results:
        # Handle different return formats (Path vs n,r,m)
        if 'p' in record:
            path = record['p']
            if path:
                for n in path.nodes:
                    if n.element_id not in node_ids:
                        label = list(n.labels)[0] if n.labels else "Unknown"
                        color = "#ff0000" if label == "Company" else "#00ff00" if label == "Person" else "#0000ff"
                        node_label = n.get("name", n.get("id", "Unknown"))
                        nodes.append(Node(id=n.element_id, label=node_label, size=20, color=color))
                        node_ids.add(n.element_id)
                for r in path.relationships:
                    edges.append(Edge(source=r.start_node.element_id, target=r.end_node.element_id, label=r.type))
        
        elif 'nodes' in record and 'relationships' in record: # APOC style
            for n in record['nodes']:
                if n.element_id not in node_ids:
                    label = list(n.labels)[0] if n.labels else "Unknown"
                    color = "#ff0000" if label == "Company" else "#00ff00" if label == "Person" else "#0000ff"
                    node_label = n.get("name", n.get("id", "Unknown"))
                    nodes.append(Node(id=n.element_id, label=node_label, size=20, color=color))
                    node_ids.add(n.element_id)
            for r in record['relationships']:
                edges.append(Edge(source=r.start_node.element_id, target=r.end_node.element_id, label=r.type))

        else: # Standard n,r,m
            n = record.get('n')
            m = record.get('m')
            r = record.get('r')
            
            if n and n.element_id not in node_ids:
                label = list(n.labels)[0] if n.labels else "Unknown"
                color = "#ff0000" if label == "Company" else "#00ff00" if label == "Person" else "#0000ff"
                node_label = n.get("name", n.get("id", "Unknown"))
                nodes.append(Node(id=n.element_id, label=node_label, size=20, color=color))
                node_ids.add(n.element_id)
            
            if m and m.element_id not in node_ids:
                label = list(m.labels)[0] if m.labels else "Unknown"
                color = "#ff0000" if label == "Company" else "#00ff00" if label == "Person" else "#0000ff"
                node_label = m.get("name", m.get("id", "Unknown"))
                nodes.append(Node(id=m.element_id, label=node_label, size=20, color=color))
                node_ids.add(m.element_id)
                
            if r:
                if isinstance(r, list):
                    for rel in r:
                        edges.append(Edge(source=rel.start_node.element_id, target=rel.end_node.element_id, label=rel.type))
                else:
                    edges.append(Edge(source=n.element_id, target=m.element_id, label=r.type))

    config = Config(width=900, height=600, directed=True, nodeHighlightBehavior=True, highlightColor="#F7A7A6", collapsible=True)
    
    if nodes:
        return_value = agraph(nodes=nodes, edges=edges, config=config)
    else:
        st.write("No graph data to display.")

with tab2:
    st.subheader("News Timeline")
    timeline_query = """
    MATCH (d:Document)
    WHERE date(d.date) >= date($start) AND date(d.date) <= date($end)
    RETURN d.date as Date, d.title as Title, d.publisher as Source, d.url as URL
    ORDER BY d.date DESC
    """
    if start_date and end_date:
        timeline_data = db.query(timeline_query, {"start": start_date.isoformat(), "end": end_date.isoformat()})
        df = pd.DataFrame([dict(record) for record in timeline_data])
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
            st.dataframe(df, use_container_width=True, column_config={"URL": st.column_config.LinkColumn("Link")})
        else:
            st.write("No articles found in this range.")
    else:
        st.write("Please select a date range.")

with tab3:
    st.subheader("Company Analysis")
    if selected_articles:
        st.write(f"Analyzing connections for: {', '.join(selected_articles)}")
        
        # 1. Companies mentioned in these articles
        companies_query = """
        MATCH (d:Document)-[:MENTIONS]->(c:Company)
        WHERE d.title IN $titles
        RETURN DISTINCT COALESCE(c.name, c.id) as Company, d.title as Article
        ORDER BY Company
        """
        companies_data = db.query(companies_query, {"titles": selected_articles})
        if companies_data:
            df_comp = pd.DataFrame([dict(r) for r in companies_data])
            st.write("### Companies Mentioned")
            st.dataframe(df_comp, use_container_width=True)
            
            # 2. Connections between these companies
            # Find paths between any pair of companies mentioned in the selected articles
            # Limit path length to avoid explosion
            connections_query = """
            MATCH (d:Document)-[:MENTIONS]->(c:Company)
            WHERE d.title IN $titles
            WITH collect(DISTINCT c) as companies
            UNWIND companies as c1
            UNWIND companies as c2
            MATCH p = (c1)-[*1..3]-(c2)
            WHERE elementId(c1) < elementId(c2)
            RETURN COALESCE(c1.name, c1.id) as Company1, COALESCE(c2.name, c2.id) as Company2, [r in relationships(p) | type(r)] as Relationships, length(p) as Distance
            ORDER BY Distance ASC
            LIMIT 50
            """
            connections_data = db.query(connections_query, {"titles": selected_articles})
            if connections_data:
                df_conn = pd.DataFrame([dict(r) for r in connections_data])
                st.write("### Connections Between Companies")
                st.dataframe(df_conn, use_container_width=True)
            else:
                st.write("No direct connections found between these companies within 3 hops.")
        else:
            st.write("No companies found in the selected articles.")
    else:
        st.write("Please select articles from the sidebar to analyze.")
