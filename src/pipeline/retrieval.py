"""Retrieval module for vector search and context expansion in Neo4j."""

from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.config import (
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD,
    VECTOR_INDEX_NAME, SIMILARITY_THRESHOLD, TOP_K_RESULTS
)
from src.pipeline.embeddings import EmbeddingGenerator


class Retriever:
    """Handle vector search and context expansion in Neo4j."""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        self.embedding_generator = EmbeddingGenerator()
    
    def close(self):
        self.driver.close()
    
    def vector_search(self, query: str, top_k: int = TOP_K_RESULTS) -> List[Dict[str, Any]]:
        """Perform vector similarity search for the query."""
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)
        
        with self.driver.session() as session:
            # Vector similarity search using the index
            result = session.run("""
                CALL db.index.vector.queryNodes($index_name, $top_k, $query_embedding)
                YIELD node as chunk, score
                WHERE score >= $threshold
                MATCH (d:Document)-[:CONTAINS]->(chunk)
                OPTIONAL MATCH (s:Section)-[:INCLUDES]->(chunk)
                RETURN 
                    chunk.chunkId as chunk_id,
                    chunk.text as text,
                    chunk.pageNum as page_num,
                    chunk.bbox as bbox,
                    chunk.chunkIndex as chunk_index,
                    d.docId as doc_id,
                    d.filename as filename,
                    d.filepath as filepath,
                    s.headings as section_headings,
                    score
                ORDER BY score DESC
            """, {
                "index_name": VECTOR_INDEX_NAME,
                "top_k": top_k,
                "query_embedding": query_embedding,
                "threshold": SIMILARITY_THRESHOLD
            })
            
            results = []
            for record in result:
                results.append({
                    "chunk_id": record["chunk_id"],
                    "text": record["text"],
                    "page_num": record["page_num"],
                    "bbox": record["bbox"],
                    "chunk_index": record["chunk_index"],
                    "doc_id": record["doc_id"],
                    "filename": record["filename"],
                    "filepath": record["filepath"],
                    "section_headings": record["section_headings"] or [],
                    "score": float(record["score"])
                })
            
            return results
    
    def expand_context(self, chunk_ids: List[str], window: int = 1) -> List[Dict[str, Any]]:
        """Expand context by fetching neighboring chunks."""
        with self.driver.session() as session:
            # Get chunks with their neighbors
            result = session.run("""
                UNWIND $chunk_ids as chunk_id
                MATCH (target:Chunk {chunkId: chunk_id})
                MATCH (d:Document)-[:CONTAINS]->(target)
                OPTIONAL MATCH path = (target)-[:NEXT*0..""" + str(window) + """]->(next:Chunk)
                OPTIONAL MATCH path2 = (prev:Chunk)-[:NEXT*1..""" + str(window) + """]->(target)
                WITH target, d, 
                     collect(DISTINCT next) as next_chunks,
                     collect(DISTINCT prev) as prev_chunks
                UNWIND (prev_chunks + [target] + next_chunks) as chunk
                WITH DISTINCT chunk, d
                ORDER BY chunk.chunkIndex
                OPTIONAL MATCH (s:Section)-[:INCLUDES]->(chunk)
                RETURN 
                    chunk.chunkId as chunk_id,
                    chunk.text as text,
                    chunk.pageNum as page_num,
                    chunk.bbox as bbox,
                    chunk.chunkIndex as chunk_index,
                    d.docId as doc_id,
                    d.filename as filename,
                    d.filepath as filepath,
                    s.headings as section_headings
            """, {
                "chunk_ids": chunk_ids
            })
            
            expanded = []
            seen_ids = set()
            
            for record in result:
                chunk_id = record["chunk_id"]
                if chunk_id not in seen_ids:
                    seen_ids.add(chunk_id)
                    expanded.append({
                        "chunk_id": chunk_id,
                        "text": record["text"],
                        "page_num": record["page_num"],
                        "bbox": record["bbox"],
                        "chunk_index": record["chunk_index"],
                        "doc_id": record["doc_id"],
                        "filename": record["filename"],
                        "filepath": record["filepath"],
                        "section_headings": record["section_headings"] or [],
                        "is_target": chunk_id in chunk_ids
                    })
            
            return expanded
    
    def retrieve_with_context(self, query: str, top_k: int = TOP_K_RESULTS, 
                            context_window: int = 1, use_query_expansion: bool = False) -> Dict[str, Any]:
        """Retrieve relevant chunks with expanded context."""
        print(f"\nSearching for: '{query}'")
        
        all_results = []
        
        if use_query_expansion:
            # Use LLM to generate query variations
            try:
                from src.pipeline.llm_processor import LLMProcessor
                llm = LLMProcessor(llm_provider="ollama")  # or "openai" with API key
                query_variations = llm.generate_query_variations(query)
                print(f"Generated {len(query_variations)} query variations")
                
                # Search with each variation
                seen_chunks = set()
                for variation in query_variations:
                    results = self.vector_search(variation, top_k)
                    for result in results:
                        if result["chunk_id"] not in seen_chunks:
                            seen_chunks.add(result["chunk_id"])
                            all_results.append(result)
                
                # Re-rank by best score
                all_results.sort(key=lambda x: x["score"], reverse=True)
                all_results = all_results[:top_k]
            except Exception as e:
                print(f"Query expansion failed: {e}, using single query")
                all_results = self.vector_search(query, top_k)
        else:
            # Standard single query search
            all_results = self.vector_search(query, top_k)
        
        if not all_results:
            print("No relevant chunks found")
            return {
                "query": query,
                "results": [],
                "expanded_context": []
            }
        
        print(f"Found {len(all_results)} relevant chunks")
        
        # Get chunk IDs for context expansion
        chunk_ids = [r["chunk_id"] for r in all_results]
        
        # Expand context if requested
        expanded_context = []
        if context_window > 0:
            expanded_context = self.expand_context(chunk_ids, context_window)
            print(f"Expanded to {len(expanded_context)} chunks with context window {context_window}")
        
        return {
            "query": query,
            "results": all_results,
            "expanded_context": expanded_context
        }
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific chunk by its ID."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Chunk {chunkId: $chunk_id})
                MATCH (d:Document)-[:CONTAINS]->(c)
                OPTIONAL MATCH (s:Section)-[:INCLUDES]->(c)
                RETURN 
                    c.chunkId as chunk_id,
                    c.text as text,
                    c.pageNum as page_num,
                    c.bbox as bbox,
                    c.chunkIndex as chunk_index,
                    d.docId as doc_id,
                    d.filename as filename,
                    d.filepath as filepath,
                    s.headings as section_headings
            """, {
                "chunk_id": chunk_id
            })
            
            record = result.single()
            if record:
                return {
                    "chunk_id": record["chunk_id"],
                    "text": record["text"],
                    "page_num": record["page_num"],
                    "bbox": record["bbox"],
                    "chunk_index": record["chunk_index"],
                    "doc_id": record["doc_id"],
                    "filename": record["filename"],
                    "filepath": record["filepath"],
                    "section_headings": record["section_headings"] or []
                }
            
            return None


def main():
    """Test the retrieval system."""
    retriever = Retriever()
    
    try:
        # Test queries
        test_queries = [
            "What is the required slope for ramps?",
            "accessibility standards for handrails",
            "ADA requirements for doorways"
        ]
        
        for query in test_queries:
            results = retriever.retrieve_with_context(query, top_k=5, context_window=1)
            
            print(f"\n{'='*60}")
            print(f"Query: {results['query']}")
            print(f"Found {len(results['results'])} relevant chunks")
            
            # Show top results
            for i, chunk in enumerate(results['results'][:3]):
                print(f"\n--- Result {i+1} (score: {chunk['score']:.3f}) ---")
                print(f"Document: {chunk['filename']}")
                print(f"Page: {chunk['page_num']}")
                print(f"Section: {' > '.join(chunk['section_headings'])}")
                print(f"Text: {chunk['text'][:200]}...")
                print(f"Chunk ID: {chunk['chunk_id']}")
    
    finally:
        retriever.close()


if __name__ == "__main__":
    main()
