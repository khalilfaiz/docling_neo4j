"""Neo4j data ingestion module."""

from typing import List, Dict, Any
from neo4j import GraphDatabase
import hashlib
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


class Neo4jIngestion:
    """Handle data ingestion into Neo4j graph database."""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
    
    def close(self):
        self.driver.close()
    
    def make_section_id(self, doc_id: str, headings: List[str]) -> str:
        """Generate a unique section ID based on document and headings."""
        section_key = f"{doc_id}:{':'.join(headings)}"
        return "s" + hashlib.sha1(section_key.encode("utf-8")).hexdigest()[:12]
    
    def ingest_document(self, metadata: Dict[str, Any], chunks: List[Dict[str, Any]]):
        """Ingest a document with its chunks into Neo4j."""
        with self.driver.session() as session:
            # Create Document node
            session.run("""
                MERGE (d:Document {docId: $doc_id})
                SET d.filename = $filename,
                    d.filepath = $filepath,
                    d.title = $title,
                    d.pageCount = $page_count
            """, {
                "doc_id": metadata["doc_id"],
                "filename": metadata["filename"],
                "filepath": metadata["filepath"],
                "title": metadata["title"],
                "page_count": metadata["page_count"]
            })
            
            # Process chunks and sections
            section_cache = {}  # Cache to avoid recreating sections
            
            for chunk in chunks:
                # Create Chunk node
                session.run("""
                    MERGE (c:Chunk {chunkId: $chunk_id})
                    SET c.text = $text,
                        c.textForEmbedding = $text_for_embedding,
                        c.pageNum = $page_num,
                        c.bbox = $bbox,
                        c.chunkIndex = $chunk_index,
                        c.tokenCount = $token_count,
                        c.embedding = $embedding
                """, {
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "text_for_embedding": chunk.get("text_for_embedding", chunk["text"]),
                    "page_num": chunk["page_num"],
                    "bbox": chunk["bbox"],
                    "chunk_index": chunk["chunk_index"],
                    "token_count": chunk["token_count"],
                    "embedding": chunk.get("embedding", [])
                })
                
                # Create CONTAINS relationship
                session.run("""
                    MATCH (d:Document {docId: $doc_id})
                    MATCH (c:Chunk {chunkId: $chunk_id})
                    MERGE (d)-[:CONTAINS]->(c)
                """, {
                    "doc_id": metadata["doc_id"],
                    "chunk_id": chunk["chunk_id"]
                })
                
                # Create NEXT relationships between consecutive chunks
                if chunk["chunk_index"] > 0:
                    prev_chunk_id = chunks[chunk["chunk_index"] - 1]["chunk_id"]
                    session.run("""
                        MATCH (c1:Chunk {chunkId: $prev_chunk_id})
                        MATCH (c2:Chunk {chunkId: $curr_chunk_id})
                        MERGE (c1)-[:NEXT]->(c2)
                    """, {
                        "prev_chunk_id": prev_chunk_id,
                        "curr_chunk_id": chunk["chunk_id"]
                    })
                
                # Handle sections based on headings
                if chunk.get("headings"):
                    section_id = self.make_section_id(metadata["doc_id"], chunk["headings"])
                    
                    # Create section if not in cache
                    if section_id not in section_cache:
                        session.run("""
                            MERGE (s:Section {sectionId: $section_id})
                            SET s.headings = $headings,
                                s.docId = $doc_id
                        """, {
                            "section_id": section_id,
                            "headings": chunk["headings"],
                            "doc_id": metadata["doc_id"]
                        })
                        
                        # Connect section to document
                        session.run("""
                            MATCH (d:Document {docId: $doc_id})
                            MATCH (s:Section {sectionId: $section_id})
                            MERGE (d)-[:HAS_SECTION]->(s)
                        """, {
                            "doc_id": metadata["doc_id"],
                            "section_id": section_id
                        })
                        
                        section_cache[section_id] = True
                    
                    # Connect chunk to section
                    session.run("""
                        MATCH (s:Section {sectionId: $section_id})
                        MATCH (c:Chunk {chunkId: $chunk_id})
                        MERGE (s)-[:INCLUDES]->(c)
                    """, {
                        "section_id": section_id,
                        "chunk_id": chunk["chunk_id"]
                    })
    
    def ingest_documents(self, documents: List[Dict[str, Any]]):
        """Ingest multiple documents into Neo4j."""
        for doc in documents:
            print(f"\nIngesting document: {doc['metadata']['filename']}")
            self.ingest_document(doc["metadata"], doc["chunks"])
            print(f"✓ Ingested {len(doc['chunks'])} chunks")
        
        print(f"\n✓ Completed ingestion of {len(documents)} documents")
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        with self.driver.session() as session:
            stats = {}
            
            # Count nodes
            for label in ["Document", "Chunk", "Section"]:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                stats[label.lower() + "_count"] = result.single()["count"]
            
            # Count relationships
            for rel_type in ["CONTAINS", "NEXT", "HAS_SECTION", "INCLUDES"]:
                result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                stats[rel_type.lower() + "_count"] = result.single()["count"]
            
            return stats


def main():
    """Test the Neo4j ingestion."""
    from src.pipeline.pdf_parser import PDFParser
    from src.pipeline.embeddings import EmbeddingGenerator
    from src.config import INPUT_DIR
    
    # Parse PDFs
    parser = PDFParser()
    documents = parser.parse_directory(INPUT_DIR)
    
    if not documents:
        print("No documents to ingest")
        return
    
    # Generate embeddings
    generator = EmbeddingGenerator()
    documents = generator.add_embeddings_to_documents(documents)
    
    # Ingest into Neo4j
    ingestion = Neo4jIngestion()
    try:
        ingestion.ingest_documents(documents)
        
        # Print statistics
        stats = ingestion.get_stats()
        print("\nDatabase Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    finally:
        ingestion.close()


if __name__ == "__main__":
    main()
