"""PDF parsing module using Docling."""

import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, VlmPipelineOptions
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel import vlm_model_specs
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.config import EMBEDDING_MODEL, MAX_CHUNK_SIZE, CHUNK_OVERLAP, OUTPUT_DIR


class PDFParser:
    """Parse PDFs and extract structured chunks with bounding boxes."""
    
    @classmethod
    def from_config(cls):
        """Create PDFParser instance using settings from config file."""
        from src.config import (
            PDF_IMAGES_SCALE,
            PDF_GENERATE_PAGE_IMAGES,
            PDF_GENERATE_PICTURE_IMAGES,
            PDF_DO_OCR,
            PDF_DO_TABLE_STRUCTURE,
            PDF_DO_PICTURE_DESCRIPTION,
            PDF_USE_VLM,
            PDF_VLM_MODEL_TYPE,
            PDF_ACCELERATOR_DEVICE,
            PDF_ACCELERATOR_THREADS
        )
        
        return cls(
            images_scale=PDF_IMAGES_SCALE,
            generate_page_images=PDF_GENERATE_PAGE_IMAGES,
            generate_picture_images=PDF_GENERATE_PICTURE_IMAGES,
            do_ocr=PDF_DO_OCR,
            do_table_structure=PDF_DO_TABLE_STRUCTURE,
            do_picture_description=PDF_DO_PICTURE_DESCRIPTION,
            use_vlm=PDF_USE_VLM,
            vlm_model_type=PDF_VLM_MODEL_TYPE,
            accelerator_device=PDF_ACCELERATOR_DEVICE,
            accelerator_threads=PDF_ACCELERATOR_THREADS
        )
    
    def __init__(
        self,
        images_scale: float = 2.0,
        generate_page_images: bool = False,
        generate_picture_images: bool = False,
        do_ocr: bool = True,
        do_table_structure: bool = True,
        do_picture_description: bool = False,
        picture_description_prompt: Optional[str] = None,
        use_vlm: bool = False,
        vlm_model_type: str = "transformers",
        accelerator_device: str = "auto",
        accelerator_threads: int = 8
    ):
        """
        Initialize PDF parser with advanced Docling options.
        
        Args:
            images_scale: Image resolution scale factor (default: 2.0)
            generate_page_images: Whether to generate full page images
            generate_picture_images: Whether to extract picture images
            do_ocr: Enable OCR for scanned documents
            do_table_structure: Enable table structure extraction
            do_picture_description: Enable AI picture descriptions (requires setup)
            picture_description_prompt: Custom prompt for picture descriptions
            use_vlm: Use Vision Language Model pipeline (GraniteDocling)
            vlm_model_type: VLM model type ('transformers' or 'mlx' for macOS)
            accelerator_device: Accelerator device ('auto', 'cpu', 'mps', 'cuda')
            accelerator_threads: Number of threads for CPU acceleration
        """
        # Determine which pipeline mode to use
        vlm_initialized = False
        
        # Check if using VLM pipeline mode
        if use_vlm:
            # VLM Pipeline Mode - uses built-in GraniteDocling model
            print(f"🤖 Initializing VLM pipeline with GraniteDocling ({vlm_model_type})")
            
            # Get VLM pipeline class
            pipeline_cls = self._get_vlm_pipeline_class()
            if not pipeline_cls:
                print("⚠️  VLM pipeline not available, falling back to standard mode")
                print("  Install with: uv add 'docling[vlm]'")
                use_vlm = False
            else:
                # Create VLM pipeline options with GraniteDocling
                pipeline_options = self._create_vlm_pipeline(vlm_model_type)
                
                # Initialize DocumentConverter with VLM pipeline
                self.converter = DocumentConverter(
                    format_options={
                        InputFormat.PDF: PdfFormatOption(
                            pipeline_cls=pipeline_cls,
                            pipeline_options=pipeline_options
                        )
                    }
                )
                vlm_initialized = True
        
        # Standard PDF Pipeline Mode (if VLM not used or failed to initialize)
        if not vlm_initialized:
            pipeline_options = PdfPipelineOptions()
            pipeline_options.images_scale = images_scale
            pipeline_options.generate_page_images = generate_page_images
            pipeline_options.generate_picture_images = generate_picture_images
            pipeline_options.do_ocr = do_ocr
            
            # Configure accelerator
            accelerator_options = self._create_accelerator_options(
                accelerator_device, accelerator_threads
            )
            pipeline_options.accelerator_options = accelerator_options
            
            # Configure table structure extraction
            if do_table_structure:
                pipeline_options.table_structure_options.do_cell_matching = True
            
            # Configure picture descriptions (if enabled)
            if do_picture_description:
                try:
                    pipeline_options.do_picture_description = True
                    if picture_description_prompt:
                        pipeline_options.picture_description_options.prompt = picture_description_prompt
                except Exception as e:
                    print(f"⚠ Picture description not available: {e}")
                    print("  Continuing without picture descriptions...")
            
            # Standard mode with PyPdfiumDocumentBackend
            self.converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=pipeline_options,
                        backend=PyPdfiumDocumentBackend
                    )
                }
            )
        
        # Store configuration
        self.config = {
            "images_scale": images_scale,
            "generate_page_images": generate_page_images,
            "generate_picture_images": generate_picture_images,
            "do_ocr": do_ocr,
            "do_table_structure": do_table_structure,
            "do_picture_description": do_picture_description,
            "use_vlm": use_vlm,
            "vlm_model_type": vlm_model_type if use_vlm else None,
            "accelerator_device": accelerator_device,
            "accelerator_threads": accelerator_threads
        }
        
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
    
    def _create_accelerator_options(
        self, device: str, num_threads: int
    ) -> AcceleratorOptions:
        """Create accelerator options based on device type."""
        # Map string to AcceleratorDevice enum
        device_map = {
            "auto": AcceleratorDevice.AUTO,
            "cpu": AcceleratorDevice.CPU,
            "mps": AcceleratorDevice.MPS,
            "cuda": AcceleratorDevice.CUDA,
        }
        
        device_enum = device_map.get(device.lower(), AcceleratorDevice.AUTO)
        
        accelerator_options = AcceleratorOptions(
            num_threads=num_threads,
            device=device_enum
        )
        
        # Log accelerator configuration
        print(f"  Accelerator: {device.upper()} with {num_threads} threads")
        
        return accelerator_options
    
    def _get_vlm_pipeline_class(self):
        """Get VLM pipeline class."""
        try:
            from docling.pipeline.vlm_pipeline import VlmPipeline
            return VlmPipeline
        except ImportError as e:
            print(f"⚠ VLM pipeline not available: {e}")
            return None
    
    def _create_vlm_pipeline(self, vlm_model_type: str) -> Optional[VlmPipelineOptions]:
        """
        Create VLM pipeline options using built-in GraniteDocling model.
        
        Based on: https://docling-project.github.io/docling/examples/minimal_vlm_pipeline/
        
        Args:
            vlm_model_type: Model type - 'transformers' (default) or 'mlx' (macOS only)
        """
        # Select model based on type
        if vlm_model_type.lower() == "mlx":
            # Use MLX for macOS with MPS acceleration
            try:
                vlm_options = vlm_model_specs.GRANITEDOCLING_MLX
                print("  Using GraniteDocling with MLX (macOS MPS acceleration)")
            except AttributeError:
                print("  ⚠️  MLX model not available, using default Transformers")
                vlm_options = None
        else:
            # Use default Transformers (no explicit options needed)
            vlm_options = None
            print("  Using GraniteDocling with Transformers (default)")
        
        # Create VLM pipeline options
        if vlm_options:
            pipeline_options = VlmPipelineOptions(vlm_options=vlm_options)
        else:
            # Use default VLM options (GraniteDocling with Transformers)
            pipeline_options = None
        
        return pipeline_options
    
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
    
    def extract_images(self, doc, result, output_dir: Path) -> Dict[str, List[str]]:
        """
        Extract and save images from the document.
        
        Args:
            doc: Parsed document object
            result: Parsing result from DocumentConverter
            output_dir: Directory to save images
            
        Returns:
            Dictionary with lists of saved image paths
        """
        from docling_core.types.doc import TableItem, PictureItem
        
        images_data = {
            "page_images": [],
            "table_images": [],
            "picture_images": []
        }
        
        # Create subdirectories
        pages_dir = output_dir / "pages"
        tables_dir = output_dir / "tables"
        pictures_dir = output_dir / "pictures"
        
        pages_dir.mkdir(parents=True, exist_ok=True)
        tables_dir.mkdir(parents=True, exist_ok=True)
        pictures_dir.mkdir(parents=True, exist_ok=True)
        
        doc_name = output_dir.name
        
        # Save page images
        if self.config.get("generate_page_images", False):
            try:
                for page_no, page in doc.pages.items():
                    if hasattr(page, 'image') and page.image:
                        page_image_path = pages_dir / f"{doc_name}-page-{page_no}.png"
                        with page_image_path.open("wb") as fp:
                            page.image.pil_image.save(fp, format="PNG")
                        images_data["page_images"].append(str(page_image_path))
            except Exception as e:
                print(f"⚠ Could not extract page images: {e}")
        
        # Save tables and pictures
        table_counter = 0
        picture_counter = 0
        
        try:
            for element, _level in doc.iterate_items():
                if isinstance(element, TableItem):
                    table_counter += 1
                    table_image_path = tables_dir / f"{doc_name}-table-{table_counter}.png"
                    try:
                        with table_image_path.open("wb") as fp:
                            element.get_image(doc).save(fp, "PNG")
                        images_data["table_images"].append(str(table_image_path))
                    except Exception as e:
                        print(f"⚠ Could not extract table {table_counter}: {e}")
                
                elif isinstance(element, PictureItem):
                    picture_counter += 1
                    picture_image_path = pictures_dir / f"{doc_name}-picture-{picture_counter}.png"
                    try:
                        with picture_image_path.open("wb") as fp:
                            element.get_image(doc).save(fp, "PNG")
                        images_data["picture_images"].append(str(picture_image_path))
                    except Exception as e:
                        print(f"⚠ Could not extract picture {picture_counter}: {e}")
        except Exception as e:
            print(f"⚠ Error iterating document items: {e}")
        
        # Print summary
        total_images = sum(len(v) for v in images_data.values())
        if total_images > 0:
            print(f"✓ Extracted {total_images} images:")
            if images_data["page_images"]:
                print(f"  - {len(images_data['page_images'])} page images")
            if images_data["table_images"]:
                print(f"  - {len(images_data['table_images'])} table images")
            if images_data["picture_images"]:
                print(f"  - {len(images_data['picture_images'])} picture images")
        
        return images_data

    def parse_pdf(
        self,
        pdf_path: Path,
        export_files: bool = True,
        extract_images: bool = False
    ) -> Dict[str, Any]:
        """
        Parse a PDF and extract structured chunks.
        
        Args:
            pdf_path: Path to the PDF file
            export_files: Whether to export markdown and chunk files
            extract_images: Whether to extract and save images (requires generation enabled in __init__)
            
        Returns:
            Dictionary containing metadata, chunks, and optional image paths
        """
        import time
        
        print(f"\n{'='*60}")
        print(f"📄 Parsing PDF: {pdf_path.name}")
        print(f"{'='*60}")
        
        # Log pipeline configuration
        print(f"\n🔧 Pipeline Configuration:")
        if self.config.get('use_vlm'):
            print(f"  ✓ Mode: VLM (Vision Language Model)")
            print(f"  ✓ Model: GraniteDocling")
            model_type = self.config.get('vlm_model_type', 'transformers')
            if model_type.lower() == 'mlx':
                print(f"  ✓ Framework: MLX (Apple Silicon GPU)")
                print(f"  ✓ Acceleration: MPS (Metal Performance Shaders)")
            else:
                print(f"  ✓ Framework: Transformers (PyTorch)")
                print(f"  ✓ Acceleration: CPU")
        else:
            print(f"  ✓ Mode: Standard (OCR + Layout Analysis)")
            print(f"  ✓ OCR: {self.config.get('do_ocr')}")
            print(f"  ✓ Table Structure: {self.config.get('do_table_structure')}")
            print(f"  ✓ Accelerator: {self.config.get('accelerator_device')} ({self.config.get('accelerator_threads')} threads)")
        
        print(f"  ✓ Images Scale: {self.config.get('images_scale')}x")
        print(f"  ✓ Generate Page Images: {self.config.get('generate_page_images')}")
        print(f"  ✓ Generate Picture Images: {self.config.get('generate_picture_images')}")
        print(f"  ✓ Extract Images: {extract_images}")
        print(f"  ✓ Export Files: {export_files}")
        
        # Start conversion
        print(f"\n⏳ Starting document conversion...")
        if self.config.get('use_vlm'):
            if self.config.get('vlm_model_type', '').lower() == 'mlx':
                print(f"  🍎 Loading GraniteDocling model with Apple Silicon GPU...")
            else:
                print(f"  🤖 Loading GraniteDocling model with Transformers...")
        else:
            print(f"  📖 Initializing standard PDF pipeline...")
        
        start_time = time.time()
        
        # Convert PDF using Docling with advanced options
        print(f"  🔄 Processing document pages...")
        result = self.converter.convert(str(pdf_path))
        doc = result.document
        
        conversion_time = time.time() - start_time
        print(f"\n✅ Conversion completed in {conversion_time:.2f}s")
        print(f"  📄 Pages processed: {getattr(doc, 'page_count', 'unknown')}")
        print(f"  ⚡ Speed: {conversion_time / max(getattr(doc, 'page_count', 1), 1):.2f}s per page")
        
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
            "markdown_file": markdown_file,
            "parser_config": self.config.copy()
        }
        
        # Extract images if requested
        if extract_images and (self.config.get("generate_page_images") or 
                              self.config.get("generate_picture_images")):
            print(f"\n📸 Extracting images...")
            images_dir = OUTPUT_DIR / f"{pdf_path.stem}_{doc_id}_images"
            images_data = self.extract_images(doc, result, images_dir)
            metadata["images"] = images_data
        
        # Process chunks
        print(f"\n✂️  Processing document into chunks...")
        chunks = []
        chunk_start_time = time.time()
        
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
                "section": " > ".join(headings) if headings else "",
                "chunk_index": idx,
                "token_count": len(self.base_tokenizer.tokenize(chunk_text))
            }
            
            chunks.append(chunk_data)
        
        chunk_time = time.time() - chunk_start_time
        print(f"  ✓ Created {len(chunks)} chunks in {chunk_time:.2f}s")
        
        # Export chunks if requested
        if export_files and chunks:
            print(f"\n💾 Exporting files...")
            json_file, chunks_md_file = self.export_chunks(chunks, pdf_path, doc_id)
            metadata["chunks_json_file"] = json_file
            metadata["chunks_md_file"] = chunks_md_file
        
        total_time = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"✅ Parsing Complete!")
        print(f"  📄 Document: {pdf_path.name}")
        print(f"  ⏱️  Total time: {total_time:.2f}s")
        print(f"  📊 {len(chunks)} chunks extracted")
        if metadata.get('images'):
            total_images = sum(len(v) for v in metadata['images'].values() if isinstance(v, list))
            print(f"  🖼️  {total_images} images extracted")
        print(f"{'='*60}\n")
        
        return {
            "metadata": metadata,
            "chunks": chunks
        }
    
    def parse_directory(
        self,
        directory: Path,
        export_files: bool = True,
        extract_images: bool = None
    ) -> List[Dict[str, Any]]:
        """
        Parse all PDFs in a directory.
        
        Args:
            directory: Directory containing PDF files
            export_files: Whether to export markdown and chunk files
            extract_images: Whether to extract images (None = auto-detect from config)
        """
        pdf_files = list(directory.glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {directory}")
            return []
        
        print(f"Found {len(pdf_files)} PDF files to process")
        
        # Auto-detect if images should be extracted based on config
        if extract_images is None:
            extract_images = (
                self.config.get("generate_page_images", False) or
                self.config.get("generate_picture_images", False)
            )
        
        if extract_images:
            print("📷 Image extraction: ENABLED")
        
        results = []
        for pdf_file in pdf_files:
            try:
                result = self.parse_pdf(
                    pdf_file,
                    export_files=export_files,
                    extract_images=extract_images
                )
                results.append(result)
            except Exception as e:
                print(f"✗ Error parsing {pdf_file.name}: {e}")
                continue
        
        return results


def main():
    """Test the PDF parser with advanced features."""
    from src.config import INPUT_DIR
    
    print("=" * 60)
    print("PDF Parser - Enhanced with Advanced Docling Features")
    print("=" * 60)
    
    # Create parser using config file settings
    parser = PDFParser.from_config()
    
    print(f"\nParser Configuration:")
    for key, value in parser.config.items():
        print(f"  {key}: {value}")
    print()
    
    # Parse all PDFs in input directory
    results = parser.parse_directory(INPUT_DIR)
    
    # Print detailed summary
    print("\n" + "=" * 60)
    print("PARSING RESULTS")
    print("=" * 60)
    
    for result in results:
        metadata = result["metadata"]
        chunks = result["chunks"]
        
        print(f"\nDocument: {metadata['filename']}")
        print(f"  Doc ID: {metadata['doc_id']}")
        print(f"  Pages: {metadata['page_count']}")
        print(f"  Chunks: {len(chunks)}")
        
        # Show image extraction results if available
        if "images" in metadata:
            images = metadata["images"]
            total_images = sum(len(v) for v in images.values())
            print(f"  Extracted Images: {total_images}")
            if images["page_images"]:
                print(f"    - Page images: {len(images['page_images'])}")
            if images["table_images"]:
                print(f"    - Table images: {len(images['table_images'])}")
            if images["picture_images"]:
                print(f"    - Picture images: {len(images['picture_images'])}")
        
        # Show first chunk as example
        if chunks:
            first_chunk = chunks[0]
            print(f"\n  First chunk example:")
            print(f"    ID: {first_chunk['chunk_id']}")
            print(f"    Page: {first_chunk['page_num']}")
            print(f"    Tokens: {first_chunk['token_count']}")
            print(f"    BBox: {first_chunk['bbox']}")
            if first_chunk['headings']:
                print(f"    Section: {' > '.join(first_chunk['headings'])}")
            print(f"    Text preview: {first_chunk['text'][:100]}...")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
