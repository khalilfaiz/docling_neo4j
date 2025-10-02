# Advanced PDF Parser Configuration

## Overview

The PDF parser has been enhanced with advanced Docling pipeline options, providing comprehensive document processing capabilities while maintaining its RAG-focused design for Neo4j ingestion.

## Key Enhancements

### 1. **Advanced DocumentConverter Configuration**

The parser now uses `PdfPipelineOptions` with the `PyPdfiumDocumentBackend` for improved performance and features:

- **OCR Support**: Automatically detect and process scanned documents
- **Table Structure Extraction**: Advanced cell matching for better table understanding
- **Image Processing**: Configurable image extraction and scaling
- **Picture Descriptions**: Optional AI-powered image descriptions (requires setup)

### 2. **Configuration Options**

All options can be configured via environment variables in `.env`:

```bash
# Image resolution scale factor (higher = better quality, slower)
PDF_IMAGES_SCALE=2.0

# Generate full page images
PDF_GENERATE_PAGE_IMAGES=false

# Extract picture/figure images
PDF_GENERATE_PICTURE_IMAGES=false

# Enable OCR for scanned documents (recommended)
PDF_DO_OCR=true

# Enable advanced table structure extraction
PDF_DO_TABLE_STRUCTURE=true

# Enable AI-powered image descriptions (requires additional setup)
PDF_DO_PICTURE_DESCRIPTION=false
```

### 3. **Flexible Initialization**

Three ways to create a parser instance:

```python
# Option 1: Use config file settings (recommended)
parser = PDFParser.from_config()

# Option 2: Use defaults
parser = PDFParser()

# Option 3: Custom configuration
parser = PDFParser(
    images_scale=3.0,
    do_ocr=True,
    do_table_structure=True,
    generate_picture_images=True
)
```

## Feature Comparison

| Feature | Basic Parser | Enhanced Parser |
|---------|-------------|-----------------|
| **Backend** | Default | PyPdfiumDocumentBackend (optimized) |
| **OCR** | Limited | Full OCR support with configurable engines |
| **Tables** | Text extraction | Structure-aware with cell matching |
| **Images** | Not extracted | Optional page/picture/table extraction |
| **Image Scale** | Fixed | Configurable (1.0x - 3.0x+) |
| **Picture AI** | None | Optional AI descriptions |
| **Configuration** | Hardcoded | Environment variables |

## Usage Examples

### Basic RAG Pipeline (Default)

```python
from src.pipeline.pdf_parser import PDFParser
from pathlib import Path

# Use default settings optimized for RAG
parser = PDFParser.from_config()

# Parse PDF
result = parser.parse_pdf(Path("document.pdf"))

# Access chunks for embedding
chunks = result["chunks"]
metadata = result["metadata"]
```

### With Image Extraction

```python
# Enable image generation in .env:
# PDF_GENERATE_PICTURE_IMAGES=true

# Create parser
parser = PDFParser.from_config()

# Parse with image extraction
result = parser.parse_pdf(
    Path("document.pdf"),
    export_files=True,
    extract_images=True  # Extract images
)

# Access extracted images
if "images" in result["metadata"]:
    images = result["metadata"]["images"]
    print(f"Table images: {len(images['table_images'])}")
    print(f"Picture images: {len(images['picture_images'])}")
```

### High-Quality OCR for Scanned Documents

```python
# Configure for scanned documents
parser = PDFParser(
    images_scale=3.0,      # High resolution
    do_ocr=True,           # Enable OCR
    do_table_structure=True # Preserve table structure
)

# Parse scanned PDF
result = parser.parse_pdf(Path("scanned_doc.pdf"))
```

### Custom Image Descriptions (Advanced)

```python
# Note: Requires additional AI model setup
parser = PDFParser(
    generate_picture_images=True,
    do_picture_description=True,
    picture_description_prompt="Describe this image in detail, focusing on technical content."
)

result = parser.parse_pdf(Path("technical_doc.pdf"))
```

## Image Extraction

When image extraction is enabled, images are organized in subdirectories:

```
output/
└── document_docXXX_images/
    ├── pages/              # Full page images
    │   ├── document-page-1.png
    │   └── document-page-2.png
    ├── tables/             # Extracted table images
    │   ├── document-table-1.png
    │   └── document-table-2.png
    └── pictures/           # Extracted figure images
        ├── document-picture-1.png
        └── document-picture-2.png
```

## Performance Considerations

### Memory Usage

| Configuration | Memory | Speed | Use Case |
|--------------|--------|-------|----------|
| **Default** | Low | Fast | Standard RAG pipeline |
| **OCR Only** | Medium | Medium | Scanned documents |
| **With Images** | High | Slow | Rich content analysis |
| **High Scale + Images** | Very High | Very Slow | Research/archival |

### Recommendations

**For Production RAG (Default):**
```bash
PDF_DO_OCR=true
PDF_DO_TABLE_STRUCTURE=true
PDF_GENERATE_PAGE_IMAGES=false
PDF_GENERATE_PICTURE_IMAGES=false
```

**For Document Analysis:**
```bash
PDF_IMAGES_SCALE=2.5
PDF_GENERATE_PAGE_IMAGES=true
PDF_GENERATE_PICTURE_IMAGES=true
PDF_DO_OCR=true
PDF_DO_TABLE_STRUCTURE=true
```

**For Fast Processing (Limited Features):**
```bash
PDF_DO_OCR=false
PDF_DO_TABLE_STRUCTURE=false
PDF_GENERATE_PAGE_IMAGES=false
PDF_GENERATE_PICTURE_IMAGES=false
```

## Advanced Features

### 1. OCR Engines

Docling supports multiple OCR engines (configurable via plugin system):
- EasyOCR
- OCRmac (macOS native)
- RapidOCR
- Tesseract/TesserOCR

### 2. Table Structure

With `do_table_structure=True`, the parser:
- Detects table boundaries
- Extracts cell-level structure
- Matches cells with content
- Preserves row/column relationships

### 3. Image Scaling

The `images_scale` parameter affects:
- Resolution of extracted images
- OCR accuracy (higher = better)
- Processing time and memory
- Quality of table/figure extraction

### 4. Picture Descriptions

When enabled, AI models can:
- Generate textual descriptions of images
- Custom prompts for specific domains
- Enhance searchability of visual content
- Requires additional model setup

## Migration from Basic Parser

The enhanced parser is **fully backward compatible**. Existing code works without changes:

```python
# Old code - still works!
parser = PDFParser()
results = parser.parse_directory(input_dir)
```

To leverage new features, simply add configuration:

```python
# New code - enhanced features
parser = PDFParser.from_config()  # Uses .env settings
results = parser.parse_directory(input_dir)
```

## Troubleshooting

### Issue: OCR Not Working

**Solution:** Install OCR backend:
```bash
# For Tesseract
brew install tesseract  # macOS
apt-get install tesseract-ocr  # Linux

# Or use EasyOCR (Python-only)
pip install easyocr
```

### Issue: Out of Memory

**Solution:** Reduce settings:
```bash
PDF_IMAGES_SCALE=1.5  # Lower scale
PDF_GENERATE_PAGE_IMAGES=false
```

### Issue: Slow Processing

**Solution:** Disable heavy features:
```bash
PDF_DO_PICTURE_DESCRIPTION=false
PDF_GENERATE_PAGE_IMAGES=false
```

## API Reference

### PDFParser Class

```python
class PDFParser:
    @classmethod
    def from_config(cls) -> 'PDFParser'
        """Create parser using environment config."""
        
    def __init__(
        self,
        images_scale: float = 2.0,
        generate_page_images: bool = False,
        generate_picture_images: bool = False,
        do_ocr: bool = True,
        do_table_structure: bool = True,
        do_picture_description: bool = False,
        picture_description_prompt: Optional[str] = None
    )
    
    def parse_pdf(
        self,
        pdf_path: Path,
        export_files: bool = True,
        extract_images: bool = False
    ) -> Dict[str, Any]
        """Parse PDF with optional image extraction."""
        
    def extract_images(
        self,
        doc,
        result,
        output_dir: Path
    ) -> Dict[str, List[str]]
        """Extract and save images from document."""
```

## Best Practices

1. **Use `from_config()`** for production to centralize settings
2. **Enable OCR** if processing scanned documents
3. **Keep image generation disabled** for standard RAG pipelines
4. **Use moderate `images_scale`** (2.0-2.5) for balance
5. **Enable table structure** for documents with tables
6. **Monitor memory usage** when processing large documents
7. **Test configurations** with sample documents first

## See Also

- [Docling Documentation](https://github.com/DS4SD/docling)
- [Configuration Guide](../README.md#configuration)
- [Neo4j Integration](./NEO4J_SETUP.md)
- [API Documentation](./API.md)

