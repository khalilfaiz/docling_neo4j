#!/usr/bin/env python3
"""Export PDFs to markdown and chunks without Neo4j ingestion."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.config import INPUT_DIR, OUTPUT_DIR
from src.pipeline.pdf_parser import PDFParser


def main():
    """Export PDFs to markdown and chunks."""
    print("📄 PDF Export Pipeline")
    print("=" * 40)
    
    # Parse PDFs and export files
    parser = PDFParser()
    documents = parser.parse_directory(INPUT_DIR)
    
    if not documents:
        print("✗ No PDF files found in input/ directory")
        return
    
    print("\n" + "=" * 40)
    print("Export Complete!")
    print("=" * 40)
    
    # Show exported files
    print(f"\n📁 Exported to: {OUTPUT_DIR}")
    total_chunks = 0
    
    for doc in documents:
        metadata = doc["metadata"]
        chunks = doc["chunks"]
        total_chunks += len(chunks)
        
        print(f"\n📄 {metadata['filename']}:")
        print(f"  📊 {len(chunks)} chunks")
        
        if metadata.get("markdown_file"):
            print(f"  📝 Markdown: {Path(metadata['markdown_file']).name}")
        if metadata.get("chunks_json_file"):
            print(f"  📊 Chunks JSON: {Path(metadata['chunks_json_file']).name}")
        if metadata.get("chunks_md_file"):
            print(f"  📋 Chunks Markdown: {Path(metadata['chunks_md_file']).name}")
    
    print(f"\n✓ Exported {len(documents)} documents with {total_chunks} total chunks")
    print(f"\n💡 To process with Neo4j, run: make run-pipeline")


if __name__ == "__main__":
    main()
