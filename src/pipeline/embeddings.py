"""Embedding generation module using sentence-transformers."""

from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.config import EMBEDDING_MODEL, EMBEDDING_DIMENSION


class EmbeddingGenerator:
    """Generate embeddings for text chunks using sentence-transformers."""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # Verify embedding dimension
        test_embedding = self.model.encode("test")
        actual_dim = len(test_embedding)
        
        if actual_dim != EMBEDDING_DIMENSION:
            print(f"Warning: Model produces {actual_dim}-dim embeddings, "
                  f"but config expects {EMBEDDING_DIMENSION}-dim")
        
        print(f"✓ Loaded model with {actual_dim}-dimensional embeddings")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        # Convert to list of floats for Neo4j
        return embedding.tolist()
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts in batch."""
        if not texts:
            return []
        
        # Generate embeddings in batch
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        
        # Convert to list of lists for Neo4j
        return embeddings.tolist()
    
    def add_embeddings_to_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add embeddings to a list of chunks."""
        if not chunks:
            return chunks
        
        print(f"Generating embeddings for {len(chunks)} chunks...")
        
        # Extract texts for embedding (use text_for_embedding if available, else fallback to text)
        # text_for_embedding contains contextualized text with hierarchical headings
        texts = [chunk.get("text_for_embedding", chunk["text"]) for chunk in chunks]
        
        # Generate embeddings in batch
        embeddings = self.generate_embeddings_batch(texts)
        
        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding
        
        print(f"✓ Generated embeddings for {len(chunks)} chunks")
        
        return chunks
    
    def add_embeddings_to_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add embeddings to all chunks in multiple documents."""
        for doc in documents:
            doc["chunks"] = self.add_embeddings_to_chunks(doc["chunks"])
        
        total_chunks = sum(len(doc["chunks"]) for doc in documents)
        print(f"✓ Processed {len(documents)} documents with {total_chunks} total chunks")
        
        return documents


def main():
    """Test the embedding generator."""
    # Create sample chunks
    sample_chunks = [
        {
            "chunk_id": "c1",
            "text": "This is a test chunk about building accessibility standards.",
            "page_num": 1
        },
        {
            "chunk_id": "c2", 
            "text": "Ramps shall have a slope not steeper than 1:12.",
            "page_num": 2
        },
        {
            "chunk_id": "c3",
            "text": "Handrails shall be provided on both sides of ramps.",
            "page_num": 2
        }
    ]
    
    # Generate embeddings
    generator = EmbeddingGenerator()
    chunks_with_embeddings = generator.add_embeddings_to_chunks(sample_chunks)
    
    # Print results
    for chunk in chunks_with_embeddings:
        embedding = chunk.get("embedding", [])
        print(f"\nChunk: {chunk['chunk_id']}")
        print(f"Text: {chunk['text'][:50]}...")
        print(f"Embedding dimension: {len(embedding)}")
        if embedding:
            print(f"Embedding sample: [{embedding[0]:.4f}, {embedding[1]:.4f}, {embedding[2]:.4f}, ...]")


if __name__ == "__main__":
    main()
