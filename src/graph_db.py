from neo4j import GraphDatabase
from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

class GraphDB:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]

    def clear_database(self):
        """CAUTION: Deletes all nodes and relationships."""
        query = "MATCH (n) DETACH DELETE n"
        self.query(query)

    def create_constraints(self):
        """Create constraints to ensure data integrity."""
        queries = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Article) REQUIRE a.url IS UNIQUE"
        ]
        for q in queries:
            self.query(q)

    @property
    def get_schema(self):
        """Returns the graph schema."""
        query = """
        CALL apoc.meta.schema() YIELD value as schema
        RETURN schema
        """
        try:
            result = self.query(query)
            if result:
                return result[0]['schema']
        except Exception:
            # Fallback if APOC is not available
            node_labels = self.query("CALL db.labels()")
            rel_types = self.query("CALL db.relationshipTypes()")
            return {
                "node_labels": [r[0] for r in node_labels],
                "relationship_types": [r[0] for r in rel_types]
            }
        return {}

# Singleton instance
db = GraphDB()
