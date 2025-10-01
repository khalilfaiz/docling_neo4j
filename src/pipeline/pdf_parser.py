"""PDF parsing module using Docling."""

import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.config import EMBEDDING_MODEL, MAX_CHUNK_SIZE, CHUNK_OVERLAP, OUTPUT_DIR


class PDFParser:
    """Parse PDFs and extract structured chunks with bounding boxes."""
    
    def __init__(self):
        self.converter = DocumentConverter()
        
        # Initialize tokenizer-aware chunker
        self.base_tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)
        self.tokenizer = HuggingFaceTokenizer(
            tokenizer=self.base_tokenizer
        )
        
        self.chunker = HybridChunker(
            tokenizer=self.tokenizer,
            max_chunk_tokens=MAX_CHUNK_SIZE,
            overlap_tokens=CHUNK_OVERLAP
        )
    
    def make_chunk_id(self, text: str, page: int) -> str:
        """Generate a unique ID for a chunk."""
        content = f"{page}:{text[:160]}"
        return "c" + hashlib.sha1(content.encode("utf-8")).hexdigest()[:12]
    
    def make_doc_id(self, file_path: str) -> str:
        """Generate a unique ID for a document."""
        return "doc" + hashlib.sha1(file_path.encode("utf-8")).hexdigest()[:12]
    
    def extract_bbox(self, doc_items: List[Any]) -> Tuple[List[float], int]:
        """Extract bounding box from document items."""
        all_bboxes = []
        page_num = 1
        
        for doc_item in doc_items:
            if hasattr(doc_item, 'prov') and doc_item.prov:
                prov = doc_item.prov[0]
                page_num = getattr(prov, 'page_no', 1)
                
                if hasattr(prov, 'bbox'):
                    bbox_obj = prov.bbox
                    all_bboxes.append([
                        bbox_obj.l,  # left
                        bbox_obj.t,  # top
                        bbox_obj.r,  # right
                        bbox_obj.b   # bottom
                    ])
        
        # Merge all bounding boxes into comprehensive bbox
        if all_bboxes:
            min_l = min(b[0] for b in all_bboxes)
            max_t = max(b[1] for b in all_bboxes)
            max_r = max(b[2] for b in all_bboxes)
            min_b = min(b[3] for b in all_bboxes)
            bbox = [min_l, max_t, max_r, min_b]
        else:
            bbox = [0, 0, 0, 0]
        
        return bbox, page_num
    
    def extract_headings(self, chunk_meta: Any) -> List[str]:
        """Extract headings from chunk metadata."""
        headings = []
        
        if hasattr(chunk_meta, 'headings') and chunk_meta.headings:
            for h in chunk_meta.headings:
                if hasattr(h, 'text'):
                    headings.append(h.text)
                else:
                    headings.append(str(h))
        
        return headings
    
    def export_markdown(self, doc, pdf_path: Path, doc_id: str) -> str:
        """Export document as markdown."""
        try:
            # Export to markdown
            markdown_content = doc.export_to_markdown()
            
            # Create output filename
            output_file = OUTPUT_DIR / f"{pdf_path.stem}_{doc_id}.md"
            
            # Write markdown file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# {pdf_path.stem}\n\n")
                f.write(f"**Document ID**: {doc_id}\n")
                f.write(f"**Source**: {pdf_path.name}\n")
                f.write(f"**Generated**: {self._get_timestamp()}\n\n")
                f.write("---\n\n")
                f.write(markdown_content)
            
            print(f"✓ Exported markdown: {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"⚠ Could not export markdown: {e}")
            return ""
    
    def export_chunks(self, chunks: List[Dict[str, Any]], pdf_path: Path, doc_id: str) -> str:
        """Export chunks to JSON and markdown files."""
        base_name = f"{pdf_path.stem}_{doc_id}"
        
        # Export chunks as JSON
        json_file = OUTPUT_DIR / f"{base_name}_chunks.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "document": {
                    "filename": pdf_path.name,
                    "doc_id": doc_id,
                    "total_chunks": len(chunks),
                    "generated": self._get_timestamp()
                },
                "chunks": chunks
            }, f, indent=2, ensure_ascii=False)
        
        # Export chunks as readable markdown
        md_file = OUTPUT_DIR / f"{base_name}_chunks.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# Chunks: {pdf_path.stem}\n\n")
            f.write(f"**Document ID**: {doc_id}\n")
            f.write(f"**Source**: {pdf_path.name}\n")
            f.write(f"**Total Chunks**: {len(chunks)}\n")
            f.write(f"**Generated**: {self._get_timestamp()}\n\n")
            f.write("---\n\n")
            
            for i, chunk in enumerate(chunks, 1):
                f.write(f"## Chunk {i}: {chunk['chunk_id']}\n\n")
                f.write(f"- **Page**: {chunk['page_num']}\n")
                f.write(f"- **Index**: {chunk['chunk_index']}\n")
                f.write(f"- **Token Count**: {chunk['token_count']}\n")
                f.write(f"- **BBox**: {chunk['bbox']}\n")
                
                if chunk['headings']:
                    f.write(f"- **Section**: {' > '.join(chunk['headings'])}\n")
                
                f.write(f"\n**Content:**\n```\n{chunk['text']}\n```\n\n")
                f.write("---\n\n")
        
        print(f"✓ Exported chunks: {json_file}")
        print(f"✓ Exported chunks markdown: {md_file}")
        
        return str(json_file), str(md_file)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def parse_pdf(self, pdf_path: Path, export_files: bool = True) -> Dict[str, Any]:
        """Parse a PDF and extract structured chunks."""
        print(f"Parsing PDF: {pdf_path}")
        
        # Convert PDF using Docling
        result = self.converter.convert(str(pdf_path))
        doc = result.document
        
        # Generate document ID
        doc_id = self.make_doc_id(str(pdf_path))
        
        # Export markdown if requested
        markdown_file = ""
        if export_files:
            markdown_file = self.export_markdown(doc, pdf_path, doc_id)
        
        # Extract metadata
        metadata = {
            "doc_id": doc_id,
            "filename": pdf_path.name,
            "filepath": str(pdf_path),
            "title": getattr(doc, 'title', pdf_path.stem),
            "page_count": getattr(doc, 'page_count', 0),
            "markdown_file": markdown_file
        }
        
        # Process chunks
        chunks = []
        for idx, chunk in enumerate(self.chunker.chunk(doc)):
            chunk_text = chunk.text.strip()
            if not chunk_text:
                continue
            
            # Extract bounding box and page number
            bbox = [0, 0, 0, 0]
            page_num = 1
            
            if hasattr(chunk.meta, 'doc_items') and chunk.meta.doc_items:
                bbox, page_num = self.extract_bbox(chunk.meta.doc_items)
            
            # Extract headings
            headings = self.extract_headings(chunk.meta)
            
            # Create chunk data
            chunk_data = {
                "chunk_id": self.make_chunk_id(chunk_text, page_num),
                "doc_id": doc_id,
                "text": chunk_text,
                "page_num": page_num,
                "bbox": bbox,
                "headings": headings,
                "chunk_index": idx,
                "token_count": len(self.base_tokenizer.tokenize(chunk_text))
            }
            
            chunks.append(chunk_data)
        
        # Export chunks if requested
        if export_files and chunks:
            json_file, chunks_md_file = self.export_chunks(chunks, pdf_path, doc_id)
            metadata["chunks_json_file"] = json_file
            metadata["chunks_md_file"] = chunks_md_file
        
        print(f"✓ Extracted {len(chunks)} chunks from {pdf_path.name}")
        
        return {
            "metadata": metadata,
            "chunks": chunks
        }
    
    def parse_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """Parse all PDFs in a directory."""
        pdf_files = list(directory.glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {directory}")
            return []
        
        print(f"Found {len(pdf_files)} PDF files to process")
        
        results = []
        for pdf_file in pdf_files:
            try:
                result = self.parse_pdf(pdf_file)
                results.append(result)
            except Exception as e:
                print(f"✗ Error parsing {pdf_file.name}: {e}")
                continue
        
        return results


def main():
    """Test the PDF parser."""
    from src.config import INPUT_DIR
    
    parser = PDFParser()
    
    # Parse all PDFs in input directory
    results = parser.parse_directory(INPUT_DIR)
    
    # Print summary
    for result in results:
        metadata = result["metadata"]
        chunks = result["chunks"]
        
        print(f"\nDocument: {metadata['filename']}")
        print(f"  Doc ID: {metadata['doc_id']}")
        print(f"  Pages: {metadata['page_count']}")
        print(f"  Chunks: {len(chunks)}")
        
        # Show first chunk as example
        if chunks:
            first_chunk = chunks[0]
            print(f"\n  First chunk:")
            print(f"    ID: {first_chunk['chunk_id']}")
            print(f"    Page: {first_chunk['page_num']}")
            print(f"    BBox: {first_chunk['bbox']}")
            print(f"    Text: {first_chunk['text'][:100]}...")


if __name__ == "__main__":
    main()
