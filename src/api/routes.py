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
async def get_articles(limit: int = 500):
    query = "MATCH (d:Document) RETURN d.title as title, d.date as date, d.publisher as source, d.url as url ORDER BY d.date DESC LIMIT $limit"
    results = db.query(query, {"limit": limit})
    articles = []
    for r in results:
        try:
            articles.append(Article(
                title=r.get('title') or "Untitled",
                date=str(r.get('date') or ""),
                source=r.get('source'),
                url=r.get('url')
            ))
        except Exception as e:
            print(f"Error processing article record: {r}, Error: {e}")
            continue
    return articles

@router.get("/graph/search")
async def search_nodes(q: str):
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

@router.get("/graph/network", response_model=GraphData)
async def get_network(
    article_titles: Optional[List[str]] = Query(None),
    node_types: Optional[List[str]] = Query(None),
    rel_types: Optional[List[str]] = Query(None),
    min_degree: int = 1
):
    nodes = []
    edges = []
    node_ids = set()

    # Build query based on filters
    if article_titles:
        # Query centered on articles - Induced Subgraph
        # Shows only nodes mentioned in the articles and relationships between them
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
        params = {"titles": article_titles, "labels": node_types, "types": rel_types}
    else:
        # Default view
        cypher_query = f"""
        MATCH (n)-[r]->(m)
        WHERE ($labels IS NULL OR any(l IN labels(n) WHERE l IN $labels))
        AND ($labels IS NULL OR any(l IN labels(m) WHERE l IN $labels))
        AND ($types IS NULL OR type(r) IN $types)
        RETURN n, r, m
        LIMIT 200
        """
        params = {"labels": node_types, "types": rel_types}

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
                    color = "#ff0000" if label == "Company" else "#00ff00" if label == "Person" else "#0000ff"
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
                color = "#ff0000" if label == "Company" else "#00ff00" if label == "Person" else "#0000ff"
                node_label = n.get("name", n.get("id", "Unknown"))
                nodes.append(GraphNode(id=n.element_id, label=node_label, color=color))
                node_ids.add(n.element_id)
            
            if m and m.element_id not in node_ids:
                label = list(m.labels)[0] if m.labels else "Unknown"
                color = "#ff0000" if label == "Company" else "#00ff00" if label == "Person" else "#0000ff"
                node_label = m.get("name", m.get("id", "Unknown"))
                nodes.append(GraphNode(id=m.element_id, label=node_label, color=color))
                node_ids.add(m.element_id)
                
            if r is not None:
                edges.append(GraphEdge(source=n.element_id, target=m.element_id, label=r.type))

    return GraphData(nodes=nodes, edges=edges)

@router.get("/analysis/companies")
async def analyze_companies(article_titles: List[str] = Query(...)):
    # 1. Companies mentioned
    companies_query = """
    MATCH (d:Document)-[:MENTIONS]->(c:Company)
    WHERE d.title IN $titles
    RETURN DISTINCT COALESCE(c.name, c.id) as Company, d.title as Article
    ORDER BY Company
    """
    companies_data = db.query(companies_query, {"titles": article_titles})
    
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
        "companies": [dict(r) for r in companies_data],
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

# Agent Endpoints
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.config import GOOGLE_API_KEY

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY, temperature=0)

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
    
    Question: {question}
    Cypher Query:
    """
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    
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
                            color = "#ff0000" if label == "Company" else "#00ff00" if label == "Person" else "#0000ff"
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
                                    color = "#ff0000" if label == "Company" else "#00ff00" if label == "Person" else "#0000ff"
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
    # In a real app, we might fetch full text. Here we'll use titles and maybe some metadata.
    # Or fetch from Neo4j if we stored text (we didn't store full text in Document nodes, just metadata).
    # Let's assume we can get enough from titles and graph connections.
    
    # Fetch graph context for these articles
    context_query = """
    MATCH (d:Document)-[r]->(n)
    WHERE d.title IN $titles
    RETURN d.title as Article, type(r) as Relation, COALESCE(n.name, n.id) as Entity, labels(n)[0] as Type
    LIMIT 200
    """
    context_data = db.query(context_query, {"titles": request.article_titles})
    
    context_str = "\n".join([f"- Article '{r['Article']}' mentions {r['Type']} '{r['Entity']}' ({r['Relation']})" for r in context_data])
    
    # Select Prompt based on Analysis Type
    if request.analysis_type == "Risks":
        template = """
        Task: Analyze the following financial news context and identify potential risks and challenges. Response in Thai using Markdown.
        
        Context:
        {context}
        
        Instructions:
        - Identify negative indicators, market risks, or operational challenges.
        - Highlight any legal issues or competitive threats.
        - Format as a Markdown list with headers.
        
        Analysis (Risks):
        """
    elif request.analysis_type == "Direction":
        template = """
        Task: Analyze the following financial news context and determine the strategic direction of the companies. Response in Thai using Markdown.
        
        Context:
        {context}
        
        Instructions:
        - Identify future plans, new products, or expansion strategies.
        - Analyze investment trends and partnerships.
        - Format as a Markdown list with headers.
        
        Analysis (Company Direction):
        """
    else: # Default: Summary
        template = """
        Task: Analyze the following financial news context and provide key insights and a summary. Response in Thai using Markdown.
        
        Context:
        {context}
        
        Instructions:
        - Identify major trends or events (e.g., big investments, new partnerships).
        - Highlight key companies and people involved.
        - Provide a concise summary of the situation.
        - Format with Markdown headers and bullet points.
        
        Analysis (Summary):
        """

    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    
    try:
        insight = chain.invoke({"context": context_str})
        return {"insight": insight}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
