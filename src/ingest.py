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
from typing import Optional

class ArticleMetadata(BaseModel):
    title: Optional[str] = Field(description="The headline of the article.")
    source: Optional[str] = Field(description="The publisher or source of the news (e.g., Investing.com, Reuters).")
    url: Optional[str] = Field(description="The URL of the article.")
    date: Optional[str] = Field(description="The publication date in ISO format (YYYY-MM-DD). If not found, return null.")

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

async def process_file(filepath):
    print(f"Processing {filepath}...")
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            text = file.read()
        
        # Extract Metadata using LLM
        try:
            metadata = metadata_chain.invoke({"text": text[:2000]}) # Send first 2000 chars for metadata to save tokens
            title = metadata.title
            source = metadata.source
            url = metadata.url
            date_str = metadata.date
            print(f"Extracted Metadata: {title} | {source} | {date_str} | {url}")
        except Exception as e:
            print(f"Metadata extraction failed for {filepath}: {e}")
            title = "Unknown"
            source = "Unknown"
            url = "Unknown"
            date_str = ""

        doc = Document(page_content=text, metadata={"source": filepath, "title": title, "date": date_str, "publisher": source, "url": url})
        
        # Extract Graph Data
        graph_documents = await graph_transformer.aconvert_to_graph_documents([doc])
        
        # Add to Neo4j
        graph.add_graph_documents(graph_documents, include_source=True)
        print(f"Successfully processed {filepath}")
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

async def main():
    # Get all txt files
    files = glob.glob("data/*.txt")
    if not files:
        files = glob.glob("c:/git/mind-ai/data/*.txt")
        
    print(f"Found {len(files)} files.")
    
    # Process files
    for file in files:
        await process_file(file)
        
    # Post-processing: Label Document nodes as Article for consistency with App
    print("Running post-processing...")
    # graph.query("MATCH (d:Document) SET d:Article")
    
    print("Ingestion complete.")

if __name__ == "__main__":
    asyncio.run(main())
