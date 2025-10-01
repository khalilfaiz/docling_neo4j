#!/usr/bin/env python3
"""Clear all data from Neo4j database."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


def clear_database():
    """Clear all nodes and relationships from Neo4j."""
    print("🗑️  Clearing Neo4j database...")
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            # Get current counts before clearing
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = result.single()["node_count"]
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            rel_count = result.single()["rel_count"]
            
            print(f"Found {node_count} nodes and {rel_count} relationships")
            
            if node_count > 0 or rel_count > 0:
                # Clear all data
                session.run("MATCH (n) DETACH DELETE n")
                print("✓ All data cleared from Neo4j database")
            else:
                print("✓ Database was already empty")
                
    except Exception as e:
        print(f"✗ Error clearing database: {e}")
        raise
    finally:
        driver.close()


if __name__ == "__main__":
    clear_database()
