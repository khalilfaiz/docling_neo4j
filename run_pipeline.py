#!/usr/bin/env python3
"""Main pipeline script to process PDFs and ingest into Neo4j."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.config import INPUT_DIR
from src.pipeline.neo4j_setup import Neo4jSetup
from src.pipeline.pdf_parser import PDFParser
from src.pipeline.embeddings import EmbeddingGenerator
from src.pipeline.neo4j_ingestion import Neo4jIngestion


def main():
    """Run the complete pipeline."""
    print("=" * 60)
    print("Layout-Aware RAG Pipeline")
    print("=" * 60)
    
    # Step 1: Setup Neo4j
    print("\n1. Setting up Neo4j database...")
    setup = Neo4jSetup()
    try:
        setup.create_constraints()
        setup.create_vector_index()
        if not setup.verify_setup():
            print("✗ Neo4j setup failed. Please check your connection settings.")
            return
    finally:
        setup.close()
    
    # Step 2: Parse PDFs
    print("\n2. Parsing PDFs...")
    parser = PDFParser.from_config()
    documents = parser.parse_directory(INPUT_DIR)
    
    if not documents:
        print("✗ No documents found to process.")
        return
    
    # Step 3: Generate embeddings
    print("\n3. Generating embeddings...")
    generator = EmbeddingGenerator()
    documents = generator.add_embeddings_to_documents(documents)
    
    # Step 4: Ingest into Neo4j
    print("\n4. Ingesting into Neo4j...")
    ingestion = Neo4jIngestion()
    try:
        ingestion.ingest_documents(documents)
        
        # Print final statistics
        print("\n" + "=" * 60)
        print("Pipeline Complete!")
        print("=" * 60)
        
        stats = ingestion.get_stats()
        print("\nDatabase Statistics:")
        print(f"  Documents: {stats['document_count']}")
        print(f"  Chunks: {stats['chunk_count']}")
        print(f"  Sections: {stats['section_count']}")
        print(f"  CONTAINS relationships: {stats['contains_count']}")
        print(f"  NEXT relationships: {stats['next_count']}")
        print(f"  HAS_SECTION relationships: {stats['has_section_count']}")
        print(f"  INCLUDES relationships: {stats['includes_count']}")
        
        # Show exported files
        print("\nExported Files:")
        for doc in documents:
            metadata = doc["metadata"]
            print(f"\n📄 {metadata['filename']}:")
            if metadata.get("markdown_file"):
                print(f"  📝 Markdown: {metadata['markdown_file']}")
            if metadata.get("chunks_json_file"):
                print(f"  📊 Chunks JSON: {metadata['chunks_json_file']}")
            if metadata.get("chunks_md_file"):
                print(f"  📋 Chunks Markdown: {metadata['chunks_md_file']}")
            
            # Show extracted images if available
            if metadata.get("images"):
                images = metadata["images"]
                total_images = sum(len(v) for v in images.values())
                if total_images > 0:
                    print(f"  📷 Extracted {total_images} images:")
                    if images.get("page_images"):
                        print(f"    - {len(images['page_images'])} page images")
                    if images.get("table_images"):
                        print(f"    - {len(images['table_images'])} table images")
                    if images.get("picture_images"):
                        print(f"    - {len(images['picture_images'])} picture images")
        
    finally:
        ingestion.close()
    
    print("\n✓ Pipeline completed successfully!")
    print(f"\n📁 Check the output/ directory for exported files")
    print("\nTo start the web interface, run:")
    print("  python -m uvicorn src.api.main:app --reload")
    print("\nThen open http://localhost:8000 in your browser.")


if __name__ == "__main__":
    main()
