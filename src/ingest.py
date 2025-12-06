import os
import glob
import asyncio
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.graphs import Neo4jGraph
from src.config import GOOGLE_API_KEY, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

# Initialize Neo4jGraph
# Note: Neo4jGraph expects url, username, password.
graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    refresh_schema=False
)

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=GOOGLE_API_KEY
)

# Define Allowed Nodes and Relationships
allowed_nodes = [
    "Person",
    "Company",
    "Product",
    "Sector",
]

allowed_relationships = [
    "WORKS_AT",
    "DEVELOPS",
    "INVESTS_IN",
    "PARTNERS_WITH",
    "SUPPLIES",
    "COMPETES_WITH",
    "AFFECTS",
]

graph_transformer = LLMGraphTransformer(
    llm=llm, 
    allowed_nodes=allowed_nodes,
    allowed_relationships=allowed_relationships
)

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Metadata Extraction Chain
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Optional, Literal

class ArticleMetadata(BaseModel):
    title: Optional[str] = Field(description="The headline of the article.")
    source: Optional[str] = Field(description="The publisher or source of the news (e.g., Investing.com, Reuters).")
    url: Optional[str] = Field(description="The URL of the article.")
    date: Optional[str] = Field(description="The publication date in ISO format (YYYY-MM-DD). If not found, return null.")
    status: Optional[Literal["Confirmed News", "Speculation", "Analysis/Outlook"]] = Field(
        description="The status of the article. Options: Confirmed News (Facts/Official), Speculation (Unverified/Hearsay), Analysis/Outlook (Expert Prediction/Forecast)."
    )   

metadata_parser = PydanticOutputParser(pydantic_object=ArticleMetadata)

metadata_prompt = PromptTemplate(
    template="""
    Extract the following metadata from the news article text:
    {format_instructions}
    
    Article Content:
    {text}
    
    JSON Output:
    """,
    input_variables=["text"],
    partial_variables={"format_instructions": metadata_parser.get_format_instructions()}
)
metadata_chain = metadata_prompt | llm | metadata_parser

# --- Sentiment Analysis Setup ---

class EntitySentiment(BaseModel):
    entity_name: str = Field(description="The exact name of the entity as found in the text.")
    sentiment: Optional[Literal["Positive", "Negative", "Neutral"]] = Field(description="The sentiment of the text towards this entity. Options: Positive, Negative, Neutral.")

class SentimentResult(BaseModel):
    sentiments: list[EntitySentiment] = Field(description="List of entities and their associated sentiments.")

sentiment_parser = PydanticOutputParser(pydantic_object=SentimentResult)

sentiment_prompt = PromptTemplate(
    template="""
    Analyze the sentiment of the news article towards the following entities: {entities}.
    Determine if the sentiment is Positive, Negative, or Neutral for each entity based on the context provided.
    
    Article Content:
    {text}
    
    {format_instructions}
    """,
    input_variables=["text", "entities"],
    partial_variables={"format_instructions": sentiment_parser.get_format_instructions()}
)

sentiment_chain = sentiment_prompt | llm | sentiment_parser

# --- Publisher Tier Logic ---

def get_publisher_tier(publisher: str) -> str:
    if not publisher:
        return "Tier C"
    
    publisher_lower = publisher.lower()
    
    tier_a = [
        "bloomberg", "wall street journal", "wsj", "financial times", "ft", 
        "new york times", "nyt", "reuters", "investing.com", 
    ]
    
    tier_b = [
        "techcrunch", "the information", "cnbc", "forbes", "business insider", 
        "axios", "wired", "the verge"
    ]
    
    for p in tier_a:
        if p in publisher_lower:
            return "A"
            
    for p in tier_b:
        if p in publisher_lower:
            return "B"
            
    return "C"

async def process_file(filepath):
    print(f"Processing {filepath}...")
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            text = file.read()
        
        # Extract Metadata using LLM
        try:
            metadata = metadata_chain.invoke({"text": text}) # Send first 2000 chars for metadata to save tokens
            title = metadata.title
            source = metadata.source
            url = metadata.url
            date_str = metadata.date
            news_status = metadata.status
            
            # Determine Publisher Tier
            publisher_tier = get_publisher_tier(source)
            
            print(f"Extracted Metadata: {title} | {source} ({publisher_tier}) | {date_str} | {url} | {news_status}")
        except Exception as e:
            print(f"Metadata extraction failed for {filepath}: {e}")
            title = "Unknown"
            source = "Unknown"
            publisher_tier = "C"
            url = "Unknown"
            date_str = ""
            news_status = "Unknown"

        doc = Document(page_content=text, metadata={"source": filepath, "title": title, "date": date_str, "publisher": source, "publisher_tier": publisher_tier, "url": url, "news_status": news_status})
        
        # Extract Graph Data
        graph_documents = await graph_transformer.aconvert_to_graph_documents([doc])
        
        # Inject Metadata into Relationships
        for graph_doc in graph_documents:
            for relationship in graph_doc.relationships:
                relationship.properties["title"] = title
                relationship.properties["date"] = date_str
                relationship.properties["publisher_tier"] = publisher_tier
                relationship.properties["news_status"] = news_status
        
        # Add to Neo4j
        graph.add_graph_documents(graph_documents, include_source=True)
        print(f"Successfully processed {filepath}")
        
        # --- Sentiment Analysis ---
        # Identify relevant entities for sentiment analysis
        relevant_entities = []
        for doc_graph in graph_documents:
            for node in doc_graph.nodes:
                if node.type in ["Company", "Product", "Sector"]:
                    relevant_entities.append(node.id)
        
        # Remove duplicates
        relevant_entities = list(set(relevant_entities))
        
        if relevant_entities:
            print(f"Analyzing sentiment for: {relevant_entities}")
            try:
                sentiment_result = sentiment_chain.invoke({"text": text[:3000], "entities": relevant_entities})
                
                for entity_sentiment in sentiment_result.sentiments:
                    # Update the relationship in Neo4j
                    # We assume the relationship is MENTIONS from the Document to the Entity
                    # Note: The graph transformer creates MENTIONS relationships between Document and Nodes
                    
                    query = """
                    MATCH (d:Document {source: $source})-[r:MENTIONS]->(n)
                    WHERE n.id = $entity_id
                    SET r.sentiment = $sentiment
                    """
                    
                    graph.query(query, params={
                        "source": filepath,
                        "entity_id": entity_sentiment.entity_name,
                        "sentiment": entity_sentiment.sentiment
                    })
                    print(f"Updated sentiment for {entity_sentiment.entity_name}: {entity_sentiment.sentiment}")
                    
            except Exception as e:
                print(f"Sentiment analysis failed for {filepath}: {e}")
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

async def main():
    files = glob.glob(r"data\batch3\*.txt")
    
    print(f"Found {len(files)} files.")
    
    # Process files
    for file in files:
        # print(f"Processing {file}...")
        await process_file(file)
        
    # Post-processing: Label Document nodes as Article for consistency with App
    print("Running post-processing...")
    # graph.query("MATCH (d:Document) SET d:Article")
    
    print("Ingestion complete.")

if __name__ == "__main__":
    asyncio.run(main())
