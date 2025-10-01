#!/usr/bin/env python3
"""Test individual components of the pipeline."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.config import INPUT_DIR


def test_pdf_parser():
    """Test PDF parsing functionality."""
    print("\n=== Testing PDF Parser ===")
    try:
        from src.pipeline.pdf_parser import PDFParser
        
        parser = PDFParser()
        pdf_files = list(INPUT_DIR.glob("*.pdf"))
        
        if not pdf_files:
            print("✗ No PDF files found in input directory")
            return False
        
        print(f"Found {len(pdf_files)} PDF file(s)")
        
        # Test parsing first PDF
        pdf_file = pdf_files[0]
        print(f"Testing with: {pdf_file.name}")
        
        result = parser.parse_pdf(pdf_file)
        metadata = result["metadata"]
        chunks = result["chunks"]
        
        print(f"✓ Parsed successfully")
        print(f"  - Doc ID: {metadata['doc_id']}")
        print(f"  - Pages: {metadata['page_count']}")
        print(f"  - Chunks: {len(chunks)}")
        
        if chunks:
            first_chunk = chunks[0]
            print(f"  - First chunk:")
            print(f"    - ID: {first_chunk['chunk_id']}")
            print(f"    - Page: {first_chunk['page_num']}")
            print(f"    - BBox: {first_chunk['bbox']}")
            print(f"    - Text preview: {first_chunk['text'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ PDF parser test failed: {e}")
        return False


def test_embeddings():
    """Test embedding generation."""
    print("\n=== Testing Embeddings ===")
    try:
        from src.pipeline.embeddings import EmbeddingGenerator
        
        generator = EmbeddingGenerator()
        
        # Test single embedding
        test_text = "This is a test sentence for embedding generation."
        embedding = generator.generate_embedding(test_text)
        
        print(f"✓ Generated embedding")
        print(f"  - Dimension: {len(embedding)}")
        print(f"  - Sample values: [{embedding[0]:.4f}, {embedding[1]:.4f}, ...]")
        
        # Test batch embeddings
        test_texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence."
        ]
        embeddings = generator.generate_embeddings_batch(test_texts)
        
        print(f"✓ Generated batch embeddings")
        print(f"  - Count: {len(embeddings)}")
        print(f"  - All same dimension: {all(len(e) == len(embeddings[0]) for e in embeddings)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Embeddings test failed: {e}")
        return False


def test_neo4j_connection():
    """Test Neo4j connection."""
    print("\n=== Testing Neo4j Connection ===")
    try:
        from src.pipeline.neo4j_setup import Neo4jSetup
        
        setup = Neo4jSetup()
        success = setup.verify_setup()
        setup.close()
        
        if success:
            print("✓ Neo4j connection successful")
            return True
        else:
            print("✗ Neo4j connection failed")
            return False
            
    except Exception as e:
        print(f"✗ Neo4j connection test failed: {e}")
        return False


def test_retrieval():
    """Test retrieval functionality (requires data in Neo4j)."""
    print("\n=== Testing Retrieval ===")
    try:
        from src.pipeline.retrieval import Retriever
        
        retriever = Retriever()
        
        # Check if we have data
        stats = retriever.driver.session().run(
            "MATCH (c:Chunk) RETURN count(c) as count"
        ).single()
        
        chunk_count = stats["count"]
        
        if chunk_count == 0:
            print("⚠ No chunks in database, skipping retrieval test")
            retriever.close()
            return True
        
        print(f"Found {chunk_count} chunks in database")
        
        # Test search
        test_query = "accessibility requirements"
        results = retriever.vector_search(test_query, top_k=3)
        
        print(f"✓ Search completed for: '{test_query}'")
        print(f"  - Results: {len(results)}")
        
        if results:
            top_result = results[0]
            print(f"  - Top result:")
            print(f"    - Score: {top_result['score']:.3f}")
            print(f"    - File: {top_result['filename']}")
            print(f"    - Page: {top_result['page_num']}")
            print(f"    - Text preview: {top_result['text'][:50]}...")
        
        retriever.close()
        return True
        
    except Exception as e:
        print(f"✗ Retrieval test failed: {e}")
        return False


def main():
    """Run all component tests."""
    print("Testing Layout-Aware RAG Components")
    print("=" * 40)
    
    tests = [
        ("PDF Parser", test_pdf_parser),
        ("Embeddings", test_embeddings),
        ("Neo4j Connection", test_neo4j_connection),
        ("Retrieval", test_retrieval),
    ]
    
    results = []
    for name, test_func in tests:
        success = test_func()
        results.append((name, success))
    
    # Summary
    print("\n" + "=" * 40)
    print("Test Summary:")
    print("=" * 40)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{name:.<30} {status}")
    
    total_passed = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} passed")
    
    if total_passed == total_tests:
        print("\n✓ All tests passed! Ready to run the pipeline.")
    else:
        print("\n✗ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()
