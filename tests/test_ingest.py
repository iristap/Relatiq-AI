import asyncio
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.ingest import process_file, graph

async def test_ingest():
    # Test with the first file found
    files = [f for f in os.listdir("data/batch1") if f.endswith(".txt")]
    if files:
        test_file = os.path.join("data/batch1", files[1])
        print(f"Testing ingestion on {test_file}")
        await process_file(test_file)
        
        # Post-processing test
        print("Running post-processing query...")
        graph.query("MATCH (d:Document) SET d:Article")
        
        # Verify Publisher Tier
        print("Verifying Publisher Tier...")
        tier_result = graph.query("MATCH (d:Document) WHERE d.source CONTAINS $source RETURN d.tier LIMIT 1", params={"source": test_file})
        print(f"Tier Result: {tier_result}")

        # Verify Sentiment
        print("Verifying Sentiment...")
        sentiment_result = graph.query("MATCH (d:Document)-[r:MENTIONS]->(n) WHERE d.source CONTAINS $source AND r.sentiment IS NOT NULL RETURN n.id, r.sentiment LIMIT 5", params={"source": test_file})
        print(f"Sentiment Result: {sentiment_result}")

        # Verify Relationship Metadata
        print("Verifying Relationship Metadata...")
        rel_metadata_result = graph.query("""
            MATCH (n)-[r]->(m) 
            WHERE r.source CONTAINS $source AND type(r) <> 'MENTIONS'
            RETURN type(r), r.source, r.date, r.tier LIMIT 1
            """, params={"source": test_file})
        print(f"Relationship Metadata Result: {rel_metadata_result}")
        
        print("Test complete.")
    else:
        print("No files found in data/")

if __name__ == "__main__":
    asyncio.run(test_ingest())
