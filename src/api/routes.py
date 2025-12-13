from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from src.graph_db import db

router = APIRouter()

class Article(BaseModel):
    title: str
    date: str
    source: Optional[str] = None
    url: Optional[str] = None
    tier: Optional[str] = None
    status: Optional[str] = None

class GraphNode(BaseModel):
    id: str
    label: str
    color: str

class GraphEdge(BaseModel):
    source: str
    target: str
    label: str

class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

@router.get("/articles", response_model=List[Article])
async def get_articles(
    limit: int = 500,
    date_range: Optional[str] = Query(None),
    tiers: Optional[List[str]] = Query(None),
    news_status: Optional[List[str]] = Query(None),
    sectors: Optional[List[str]] = Query(None),
    entity_search: Optional[str] = Query(None)
):
    # Calculate date threshold
    date_filter_clause = ""
    params = {"limit": limit, "tiers": tiers, "statuses": news_status, "sectors": sectors, "entity_search": entity_search}
    
    if date_range and date_range != "all":
        from datetime import datetime, timedelta
        today = datetime.now()
        if date_range == "7d":
            delta = timedelta(days=7)
        elif date_range == "30d":
            delta = timedelta(days=30)
        elif date_range == "3m":
            delta = timedelta(days=90)
        else:
            delta = timedelta(days=36500)
            
        threshold_date = (today - delta).strftime("%Y-%m-%d")
        date_filter_clause = "AND d.date >= $threshold_date"
        params["threshold_date"] = threshold_date

    # Build Query
    # We need to filter Documents based on their properties AND their relationships to specific nodes (Sectors/Entities)
    
    query = f"""
    MATCH (d:Document)
    WHERE 1=1
    {date_filter_clause}
    AND ($tiers IS NULL OR d.publisher_tier IN $tiers)
    AND ($statuses IS NULL OR d.news_status IN $statuses)
    
    // Filter by Sector (if provided)
    AND ($sectors IS NULL OR EXISTS {{
        MATCH (d)-[:MENTIONS]->(n)
        WHERE (n:Sector AND n.id IN $sectors) 
           OR EXISTS {{ MATCH (n)-[:BELONGS_TO]->(s:Sector) WHERE s.id IN $sectors }}
    }})
    
    // Filter by Entity Search (if provided)
    AND ($entity_search IS NULL OR EXISTS {{
        MATCH (d)-[:MENTIONS]->(n)
        WHERE toLower(COALESCE(n.name, n.id)) CONTAINS toLower($entity_search)
    }})
    
    RETURN d.title as title, d.date as date, d.publisher as source, d.url as url, d.publisher_tier as tier, d.news_status as status 
    ORDER BY d.date DESC 
    LIMIT $limit
    """
    
    results = db.query(query, params)
    articles = []
    for r in results:
        try:
            articles.append(Article(
                title=r.get('title') or "Untitled",
                date=str(r.get('date') or ""),
                source=r.get('source'),
                url=r.get('url'),
                tier=r.get('tier'),
                status=r.get('status')
            ))
        except Exception as e:
            print(f"Error processing article record: {r}, Error: {e}")
            continue
    return articles

@router.get("/graph/search")
async def search_nodes(q: str):
    """
    Searches for graph nodes based on a query string.

    Args:
        q (str): The query string to search for in node names or IDs.

    Returns:
        List[GraphNode]: A list of graph nodes matching the query.
    """

    query = """
    MATCH (n) 
    WHERE toLower(COALESCE(n.name, n.id)) CONTAINS toLower($q) 
    AND NOT n:Document 
    RETURN elementId(n) as id, COALESCE(n.name, n.id) as label, labels(n) as labels 
    LIMIT 200
    """
    results = db.query(query, {"q": q})
    nodes = []
    for r in results:
        lbl = r['labels'][0] if r['labels'] else "Unknown"
        nodes.append({"id": r['id'], "label": r['label'], "type": lbl})
    return nodes

@router.get("/sectors")
async def get_sectors():
    query = "MATCH (n:Sector) RETURN DISTINCT COALESCE(n.name, n.id) as id ORDER BY id"
    results = db.query(query)
    return [r['id'] for r in results]

@router.get("/graph/network", response_model=GraphData)
async def get_network(
    article_titles: Optional[List[str]] = Query(None),
    node_types: Optional[List[str]] = Query(None),
    rel_types: Optional[List[str]] = Query(None),
    date_range: Optional[str] = Query(None), # "7d", "30d", "3m", "all"
    tiers: Optional[List[str]] = Query(None),
    news_status: Optional[List[str]] = Query(None),
    sectors: Optional[List[str]] = Query(None),
    entity_search: Optional[str] = Query(None)
):
    nodes = []
    edges = []
    node_ids = set()

    # Calculate date threshold
    date_filter_clause = ""
    params = {"labels": node_types, "types": rel_types, "tiers": tiers, "statuses": news_status, "sectors": sectors, "entity_search": entity_search}
    
    if date_range and date_range != "all":
        from datetime import datetime, timedelta
        today = datetime.now()
        if date_range == "7d":
            delta = timedelta(days=7)
        elif date_range == "30d":
            delta = timedelta(days=30)
        elif date_range == "3m":
            delta = timedelta(days=90)
        else:
            delta = timedelta(days=36500) # Default to all if unknown
            
        threshold_date = (today - delta).strftime("%Y-%m-%d")
        date_filter_clause = "AND d.date >= $threshold_date"
        params["threshold_date"] = threshold_date

    # Build query based on filters
    if article_titles:
        # Query centered on articles - Induced Subgraph
        cypher_query = """
        MATCH (d:Document)-[:MENTIONS]->(n)
        WHERE d.title IN $titles
        WITH collect(DISTINCT n) as nodes
        UNWIND nodes as n
        MATCH (n)-[r]-(m)
        WHERE m IN nodes
        AND ($labels IS NULL OR any(l IN labels(n) WHERE l IN $labels))
        AND ($labels IS NULL OR any(l IN labels(m) WHERE l IN $labels))
        AND ($types IS NULL OR type(r) IN $types)
        RETURN n, r, m
        """
        params["titles"] = article_titles
    else:
        # Advanced Filtered View
        # 1. Filter Documents first
        # 2. Filter Nodes (Sectors, Entity Search)
        
        cypher_query = f"""
        MATCH (d:Document)
        WHERE 1=1
        {date_filter_clause}
        AND ($tiers IS NULL OR d.publisher_tier IN $tiers)
        AND ($statuses IS NULL OR d.news_status IN $statuses)
        
        MATCH (d)-[r_mentions:MENTIONS]->(n)
        WHERE ($sectors IS NULL OR (n:Sector AND n.id IN $sectors) OR EXISTS {{ MATCH (n)-[:BELONGS_TO]->(:Sector {{id: $sectors[0]}}) }}) -- Simplified sector check for now, ideally iterate
        AND ($entity_search IS NULL OR toLower(COALESCE(n.name, n.id)) CONTAINS toLower($entity_search))
        
        WITH collect(DISTINCT n) as nodes
        UNWIND nodes as n
        MATCH (n)-[r]-(m)
        WHERE m IN nodes
        AND ($labels IS NULL OR any(l IN labels(n) WHERE l IN $labels))
        AND ($labels IS NULL OR any(l IN labels(m) WHERE l IN $labels))
        AND ($types IS NULL OR type(r) IN $types)
        RETURN n, r, m
        LIMIT 500
        """
        
        # Note: The sector logic above is a bit simplified. 
        # If $sectors is a list, we should check if n belongs to ANY of them.
        # Correct Cypher for Sector filtering:
        # AND ($sectors IS NULL OR (n:Sector AND n.id IN $sectors) OR EXISTS { MATCH (n)-[:BELONGS_TO]->(s:Sector) WHERE s.id IN $sectors })
        
        cypher_query = f"""
        MATCH (d:Document)
        WHERE 1=1
        {date_filter_clause}
        AND ($tiers IS NULL OR d.publisher_tier IN $tiers)
        AND ($statuses IS NULL OR d.news_status IN $statuses)
        
        MATCH (d)-[:MENTIONS]->(n)
        WHERE ($sectors IS NULL OR (n:Sector AND n.id IN $sectors) OR EXISTS {{ MATCH (n)-[:BELONGS_TO]->(s:Sector) WHERE s.id IN $sectors }})
        AND ($entity_search IS NULL OR toLower(COALESCE(n.name, n.id)) CONTAINS toLower($entity_search))
        
        WITH collect(DISTINCT n) as nodes
        UNWIND nodes as n
        MATCH (n)-[r]-(m)
        WHERE m IN nodes
        AND ($labels IS NULL OR any(l IN labels(n) WHERE l IN $labels))
        AND ($labels IS NULL OR any(l IN labels(m) WHERE l IN $labels))
        AND ($types IS NULL OR type(r) IN $types)
        RETURN n, r, m
        LIMIT 500
        """

    try:
        results = db.query(cypher_query, params)
    except Exception as e:
        print(f"Query Error: {e}")
        return GraphData(nodes=[], edges=[])

    for record in results:
        if 'nodes' in record and 'relationships' in record: # APOC
            for n in record['nodes']:
                if n.element_id not in node_ids:
                    label = list(n.labels)[0] if n.labels else "Unknown"
                    label = list(n.labels)[0] if n.labels else "Unknown"
                    color_map = {
                        "Company": "#ef4444",  # Red-500
                        "Person": "#22c55e",   # Green-500
                        "Sector": "#f59e0b",   # Amber-500
                        "Product": "#a855f7",  # Purple-500
                        "Document": "#64748b"  # Slate-500
                    }
                    color = color_map.get(label, "#3b82f6") # Blue-500 default
                    node_label = n.get("name", n.get("id", "Unknown"))
                    nodes.append(GraphNode(id=n.element_id, label=node_label, color=color))
                    node_ids.add(n.element_id)
            for r in record['relationships']:
                edges.append(GraphEdge(source=r.start_node.element_id, target=r.end_node.element_id, label=r.type))
        else: # Standard
            n = record.get('n')
            m = record.get('m')
            r = record.get('r')
            
            if n and n.element_id not in node_ids:
                label = list(n.labels)[0] if n.labels else "Unknown"
                label = list(n.labels)[0] if n.labels else "Unknown"
                color_map = {
                    "Company": "#ef4444",
                    "Person": "#22c55e",
                    "Sector": "#f59e0b",
                    "Product": "#a855f7",
                    "Document": "#64748b"
                }
                color = color_map.get(label, "#3b82f6")
                node_label = n.get("name", n.get("id", "Unknown"))
                nodes.append(GraphNode(id=n.element_id, label=node_label, color=color))
                node_ids.add(n.element_id)
            
            if m and m.element_id not in node_ids:
                label = list(m.labels)[0] if m.labels else "Unknown"
                label = list(m.labels)[0] if m.labels else "Unknown"
                color_map = {
                    "Company": "#ef4444",
                    "Person": "#22c55e",
                    "Sector": "#f59e0b",
                    "Product": "#a855f7",
                    "Document": "#64748b"
                }
                color = color_map.get(label, "#3b82f6")
                node_label = m.get("name", m.get("id", "Unknown"))
                nodes.append(GraphNode(id=m.element_id, label=node_label, color=color))
                node_ids.add(m.element_id)
                
            if r is not None:
                edges.append(GraphEdge(source=n.element_id, target=m.element_id, label=r.type))

    return GraphData(nodes=nodes, edges=edges)

@router.get("/analysis/companies")
async def analyze_companies(article_titles: List[str] = Query(...)):
    # 1. Sentiment Analysis (Companies, Products, Sectors)
    sentiment_query = """
    MATCH (d:Document)-[r:MENTIONS]->(n)
    WHERE d.title IN $titles AND (n:Company OR n:Product OR n:Sector)
    RETURN 
        COALESCE(n.name, n.id) as Entity, 
        labels(n)[0] as Type, 
        r.sentiment as Sentiment, 
        count(*) as Count
    """
    sentiment_raw = db.query(sentiment_query, {"titles": article_titles})
    
    # Process into structured data
    entity_stats = {}
    for row in sentiment_raw:
        entity = row['Entity']
        etype = row['Type']
        sentiment = row['Sentiment'] or "Neutral"
        count = row['Count']
        
        if entity not in entity_stats:
            entity_stats[entity] = {"Entity": entity, "Type": etype, "Total": 0, "Positive": 0, "Negative": 0, "Neutral": 0}
        
        entity_stats[entity]["Total"] += count
        if sentiment == "Positive":
            entity_stats[entity]["Positive"] += count
        elif sentiment == "Negative":
            entity_stats[entity]["Negative"] += count
        else:
            entity_stats[entity]["Neutral"] += count
            
    sentiment_data = list(entity_stats.values())
    
    # 2. Connections
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
    LIMIT 200
    """
    connections_data = db.query(connections_query, {"titles": article_titles})
    
    return {
        "sentiment": sentiment_data,
        "connections": [dict(r) for r in connections_data]
    }

@router.get("/articles/mentions")
async def get_article_mentions(title: str):
    query = """
    MATCH (d:Document)-[:MENTIONS]->(n)
    WHERE d.title = $title
    RETURN elementId(n) as id
    """
    results = db.query(query, {"title": title})
    return [r['id'] for r in results]

@router.get("/article/content")
async def get_article_content(title: str):
    query = """
    MATCH (d:Document)
    WHERE d.title = $title
    RETURN d.text as text
    """
    results = db.query(query, {"title": title})
    if results:
        return {"text": results[0].get("text", "")}
    raise HTTPException(status_code=404, detail="Article not found")

# Agent Endpoints
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.config import GOOGLE_API_KEY

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=GOOGLE_API_KEY, temperature=0)
llm_t2g = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY, temperature=0)
class AgentQueryRequest(BaseModel):
    query: str

class AgentInsightRequest(BaseModel):
    article_titles: List[str]
    analysis_type: str = "Summary" # Summary, Risks, Direction

@router.post("/agent/query")
async def agent_query(request: AgentQueryRequest):
    # 1. Generate Cypher
    # We need the schema for better generation
    schema = db.get_schema
    
    template = """
    Task: Generate a Neo4j Cypher query to answer the user's question.
    Schema:
    {schema}
    
    Instructions:
    - Use only the provided schema.
    - Return ONLY the Cypher query, no markdown, no explanation.
    - The query should return nodes and relationships if possible, or specific data if asked.
    - Use COALESCE(n.name, n.id) for names.
    - If the user asks about "investments", look for INVESTS_IN relationships.
    - If the user asks about "partnerships", look for PARTNERS_WITH relationships.
    Question: {question} กราฟ
    Cypher Query:
    """
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm_t2g | StrOutputParser()
    
    try:
        cypher = chain.invoke({"schema": schema, "question": request.query})
        cypher = cypher.replace("```cypher", "").replace("```", "").strip()
        
        # 2. Execute Cypher
        results = db.query(cypher)
        
        # 3. Format Results for Graph (if applicable)
        nodes = []
        edges = []
        node_ids = set()
        
        # Try to parse as graph data if possible
        for record in results:
            # Check for common return patterns
            for key, value in record.items():
                if hasattr(value, 'element_id'): # Node or Relationship
                    if hasattr(value, 'labels'): # Node
                        if value.element_id not in node_ids:
                            label = list(value.labels)[0] if value.labels else "Unknown"
                            label = list(value.labels)[0] if value.labels else "Unknown"
                            color_map = {
                                "Company": "#ef4444",
                                "Person": "#22c55e",
                                "Sector": "#f59e0b",
                                "Product": "#a855f7",
                                "Document": "#64748b"
                            }
                            color = color_map.get(label, "#3b82f6")
                            node_label = value.get("name", value.get("id", "Unknown"))
                            nodes.append(GraphNode(id=value.element_id, label=node_label, color=color))
                            node_ids.add(value.element_id)
                    elif hasattr(value, 'type'): # Relationship
                        edges.append(GraphEdge(source=value.start_node.element_id, target=value.end_node.element_id, label=value.type))
                elif isinstance(value, list): # Path or list of things
                    for item in value:
                         if hasattr(item, 'element_id'):
                            if hasattr(item, 'labels'): # Node
                                if item.element_id not in node_ids:
                                    label = list(item.labels)[0] if item.labels else "Unknown"
                                    label = list(item.labels)[0] if item.labels else "Unknown"
                                    color_map = {
                                        "Company": "#ef4444",
                                        "Person": "#22c55e",
                                        "Sector": "#f59e0b",
                                        "Product": "#a855f7",
                                        "Document": "#64748b"
                                    }
                                    color = color_map.get(label, "#3b82f6")
                                    node_label = item.get("name", item.get("id", "Unknown"))
                                    nodes.append(GraphNode(id=item.element_id, label=node_label, color=color))
                                    node_ids.add(item.element_id)
                            elif hasattr(item, 'type'): # Relationship
                                edges.append(GraphEdge(source=item.start_node.element_id, target=item.end_node.element_id, label=item.type))

        return {
            "cypher": cypher,
            "data": results, # Raw data for table/text view
            "graph": {"nodes": nodes, "edges": edges} # Formatted for visualization
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent/insight")
async def agent_insight(request: AgentInsightRequest):
    # 1. Fetch Article Content (or summaries)
    # We fetch full text (or snippets) from Document nodes and relationships.
    
    # Fetch graph context for these articles
    # We need to collect article text explicitly if available, otherwise fallback to title
    context_query = """
    MATCH (d:Document)
    WHERE d.title IN $titles
    OPTIONAL MATCH (d)-[r]->(n)
    RETURN d.title as Article, d.text as Text, type(r) as Relation, COALESCE(n.name, n.id) as Entity, labels(n)[0] as Type
    LIMIT 500
    """
    context_data = db.query(context_query, {"titles": request.article_titles})
    article_context = "\n".join([
        f"Article: {row['Text']}"
        for row in context_data
    ])
    

    print(article_context)
    graph_context_query = """
    MATCH (d:Document)-[:MENTIONS]->(n)
    WHERE d.title IN $titles
    WITH collect(DISTINCT n) as nodes
    UNWIND nodes as n
    MATCH (n)-[r]-(m)
    WHERE m IN nodes
    RETURN n, type(r) as relationship_type, m
    """
    graph_context_data = db.query(graph_context_query, {"titles": request.article_titles})
    # Combine existing article content with the new graph relationships
    # article_context = "\n\n".join([f"Content:\n{c}" for t, c in articles_map.items()])
    # if graph_relationships:
    #     article_context += "\n\nRelevant Graph Relationships:\n" + "\n".join(graph_relationships)

    graph_relationships = []
    for record in graph_context_data:
        node_n_name = record['n'].get('name', record['n'].get('id', 'Unknown'))
        node_m_name = record['m'].get('name', record['m'].get('id', 'Unknown'))
        relationship_type = record['relationship_type']
        graph_relationships.append(f"{node_n_name} {relationship_type} {node_m_name},")

    relation_ship_node = " ".join(graph_relationships)

    print(article_context)
    print("*"*100)
    print(relation_ship_node)
    # Select Prompt based on Analysis Type

    # Relationship Nodes (Extracted entities, events, and their connections):
    # {relation_ship_node}


    if request.analysis_type == "Risks":
        template = """
        Task: Analyze the financial news context and the extracted relationship nodes to identify and evaluate potential **Key Risks** associated with the situation.

        Response Language: Primary Thai. All explanations and descriptive text must be in Thai. **However, all proper nouns and company names (e.g., Microsoft, Google, Nvidia, OpenAI) must be written in English.**
        Response Format: Strict Markdown to list and detail the identified risks, followed by an explanation and citation (if available).

        Context:
        ---
        News Article:
        {article_context}
        ---

        Instructions for Risk Analysis:

        1.  **Identify Key Risks:** Based on the news context in English, identify at least three major potential risks (e.g., Regulatory Scrutiny, Supply Chain Issues, Intensified Competition, Geopolitical Tension, Economic Downturn, Technology Failure).
        2.  **Provide Detail:**
            * State the risk in bold (e.g., **Regulatory Scrutiny**).
            * Provide a brief **Thai explanation** of *why* this risk is relevant to the context.
            * If the context explicitly mentions a source or impact related to the risk, include it in the explanation.
        3.  **Output Structure:**
            * Start the entire output with the heading: `## ⚠️ ความเสี่ยงที่ควรระวัง`
            * Format each risk as a collapsible section or clearly separate entries using Markdown structure, prioritizing clarity and scannability similar to the example image.

        Analysis (Summary):
        """
    elif request.analysis_type == "Direction":
        template = """
        Task: Analyze the financial news context to summarize the strategic position and key actions of the main companies/entities involved. The output must be structured as individual summaries for each entity.

        Response Language: Primary Thai. All explanations and descriptive text must be in Thai. **However, all proper nouns and company names (e.g., Microsoft, Google, Nvidia, OpenAI) must be written in English.**
        Response Format: Use Markdown to list each entity's strategic summary clearly.

        Context:
        ---
        News Article:
        {article_context}
        ---

        Instructions for Strategic Output:

        1.  **Identify Key Entities:** Identify 3-4 major players (e.g., Microsoft, OpenAI, Nvidia, Google, AMD) from the context.
        2.  **Entity Block:** For each entity, create a block with the following structure:
            * **Header:** Start with the name in bold and use an appropriate icon (e.g., **Microsoft**).
            * **Summary:** Provide a concise, high-level summarizing their strategic focus (e.g., "Aggressively expanding AI capabilities through strategic investments and partnerships.").
            * **Key Actions:** Provide a bulleted list of 3-5 specific actions or capabilities derived from the news (e.g., Expanding Azure AI services, Integrating AI into Windows, Developing custom silicon).

        Analysis (Strategic Summary):
        """
    else: # Default: Summary
        template ="""
        Task: Analyze the financial news context and the extracted relationship nodes to generate a comprehensive analysis. The response must strictly adhere to the specified Thai Markdown structure and focus on high-level strategy.

        Response Language: Primary Thai. All explanations and descriptive text must be in Thai. **However, all proper nouns and company names (e.g., Microsoft, Google, Nvidia, OpenAI) must be written in English.**
        Response Format: Strictly use the two required headers in Markdown (##) followed by synthesized content.

        Context:
        ---
        News Article:
        {article_context}
        ---

        Instructions for Output Generation:

        1.  **Header 1 - ภาพรวมเชิงลึก (Insight Overview):**
            * Start the entire analysis with this header: `## ภาพรวมเชิงลึก (Insight Overview)`
            * Content should be a synthesis of the news and relationships, identifying major market **trends**, **implications**, and the overall competitive landscape or regulatory environment. (Must be a cohesive paragraph or multiple paragraphs, not bullet points).
            * response briefly in 3-4 lines.

        2.  **Header 2 - ทิศทางเชิงกลยุทธ์ของบริษัท:**
            * Follow the first section immediately with this header: `## ทิศทางเชิงกลยุทธ์ของบริษัท`
            * Identify the **key companies** involved.
            * For each company, use **bullet points** (`*`) to clearly describe their **strategic moves, competitive position, investments, or challenges** as indicated by the context.
            * response briefly in 1-2 lines.

        3.  **Do not include any other introductory text, final remarks, or headers besides the two specified ones.**

        Analysis (Summary):
        """

    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    
    try:
        insight = chain.invoke({"article_context": article_context, "relation_ship_node": relation_ship_node})
        return {"insight": insight}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
