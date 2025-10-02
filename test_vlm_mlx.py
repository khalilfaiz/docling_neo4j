#!/usr/bin/env python3
"""
Test VLM with MLX (Apple Silicon GPU) acceleration.
This script demonstrates the enhanced logging and GPU acceleration.
"""

from pathlib import Path
from src.pipeline.pdf_parser import PDFParser
from src.config import INPUT_DIR

def main():
    """Test VLM parsing with detailed logging."""
    
    print("\n" + "="*70)
    print("🧪 Testing VLM with MLX (Apple Silicon GPU Acceleration)")
    print("="*70)
    
    # Find first PDF in input directory
    pdf_files = list(INPUT_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print("\n❌ No PDF files found in input/ directory")
        print("   Please add a PDF file to test with.")
        return
    
    pdf_path = pdf_files[0]
    print(f"\n📄 Test file: {pdf_path.name}")
    print(f"   Location: {pdf_path}")
    
    # Test 1: VLM with MLX (Apple Silicon GPU)
    print("\n" + "-"*70)
    print("Test 1: VLM with MLX (Apple Silicon GPU)")
    print("-"*70)
    
    parser_mlx = PDFParser(
        use_vlm=True,
        vlm_model_type="mlx",
        generate_page_images=True,
        generate_picture_images=True
    )
    
    result_mlx = parser_mlx.parse_pdf(
        pdf_path,
        export_files=True,
        extract_images=False
    )
    
    # Test 2: VLM with Transformers (CPU) for comparison
    print("\n" + "-"*70)
    print("Test 2: VLM with Transformers (CPU) - For Comparison")
    print("-"*70)
    
    parser_cpu = PDFParser(
        use_vlm=True,
        vlm_model_type="transformers",
        generate_page_images=False,
        generate_picture_images=False
    )
    
    result_cpu = parser_cpu.parse_pdf(
        pdf_path,
        export_files=False,
        extract_images=False
    )
    
    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    print(f"\n✅ MLX (GPU) Results:")
    print(f"   - Chunks: {len(result_mlx['chunks'])}")
    print(f"   - Pages: {result_mlx['metadata']['page_count']}")
    
    print(f"\n✅ Transformers (CPU) Results:")
    print(f"   - Chunks: {len(result_cpu['chunks'])}")
    print(f"   - Pages: {result_cpu['metadata']['page_count']}")
    
    print(f"\n💡 Note: Check the timing information above to see GPU acceleration benefits!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

