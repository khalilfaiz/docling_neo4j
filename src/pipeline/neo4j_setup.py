"""Neo4j database setup and configuration."""

from neo4j import GraphDatabase
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config import (
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, 
    VECTOR_INDEX_NAME, EMBEDDING_DIMENSION
)


class Neo4jSetup:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
    
    def close(self):
        self.driver.close()
    
    def create_constraints(self):
        """Create uniqueness constraints for nodes."""
        with self.driver.session() as session:
            # Document constraint
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) 
                REQUIRE d.docId IS UNIQUE
            """)
            
            # Chunk constraint
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (c:Chunk) 
                REQUIRE c.chunkId IS UNIQUE
            """)
            
            # Section constraint
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (s:Section) 
                REQUIRE s.sectionId IS UNIQUE
            """)
            
            print("✓ Created uniqueness constraints")
    
    def create_vector_index(self):
        """Create vector index for chunk embeddings."""
        with self.driver.session() as session:
            # Drop existing index if it exists
            session.run(f"DROP INDEX {VECTOR_INDEX_NAME} IF EXISTS")
            
            # Create new vector index
            session.run(f"""
                CREATE VECTOR INDEX {VECTOR_INDEX_NAME} IF NOT EXISTS
                FOR (c:Chunk) ON (c.embedding)
                OPTIONS {{
                    indexConfig: {{
                        `vector.dimensions`: {EMBEDDING_DIMENSION},
                        `vector.similarity_function`: 'cosine'
                    }}
                }}
            """)
            
            print(f"✓ Created vector index '{VECTOR_INDEX_NAME}' with {EMBEDDING_DIMENSION} dimensions")
    
    def clear_database(self):
        """Clear all nodes and relationships (use with caution!)."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("✓ Cleared database")
    
    def verify_setup(self):
        """Verify database connection and configuration."""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                if result.single()["test"] == 1:
                    print("✓ Neo4j connection successful")
                
                # Check constraints
                constraints = session.run("SHOW CONSTRAINTS").data()
                print(f"✓ Found {len(constraints)} constraints")
                
                # Check indexes
                indexes = session.run("SHOW INDEXES").data()
                vector_indexes = [idx for idx in indexes if idx.get('type') == 'VECTOR']
                print(f"✓ Found {len(vector_indexes)} vector indexes")
                
                return True
        except Exception as e:
            print(f"✗ Neo4j setup verification failed: {e}")
            return False


def main():
    """Run Neo4j setup."""
    print("Setting up Neo4j database...")
    
    setup = Neo4jSetup()
    try:
        # Optional: Clear database (uncomment if needed)
        # setup.clear_database()
        
        # Create constraints and indexes
        setup.create_constraints()
        setup.create_vector_index()
        
        # Verify setup
        setup.verify_setup()
        
        print("\n✓ Neo4j setup completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
        raise
    finally:
        setup.close()


if __name__ == "__main__":
    main()
