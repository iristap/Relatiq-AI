from src.graph_db import db

query = "MATCH (n) WHERE NOT n:Document RETURN n LIMIT 1"
result = db.query(query)

print(result)

if result:
    node = result[0]['n']
    print(f"Labels: {node.labels}")
    print(f"Properties: {dict(node)}")
else:
    print("No nodes found.")
