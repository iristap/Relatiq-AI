import asyncio
import os
from src.ingest import process_file, graph

async def test_ingest():
    # Test with the first file found
    files = [f for f in os.listdir("data") if f.endswith(".txt")]
    if files:
        test_file = os.path.join("data", files[0])
        print(f"Testing ingestion on {test_file}")
        await process_file(test_file)
        
        # Post-processing test
        print("Running post-processing query...")
        graph.query("MATCH (d:Document) SET d:Article")
        
        print("Test complete.")
    else:
        print("No files found in data/")

if __name__ == "__main__":
    asyncio.run(test_ingest())
