# VLM (Vision Language Model) Setup Guide

## Overview

The PDF parser now supports **VLM parsing mode** using IBM Granite models for advanced document understanding. VLM mode uses vision-language models to directly understand document layout, tables, and figures without traditional OCR.

Based on the [official Docling VLM example](https://docling-project.github.io/docling/examples/vlm_pipeline_api_model/).

## What is VLM Mode?

**Standard Mode** (default):
- Uses OCR + layout analysis
- Rule-based table detection
- Traditional PDF extraction

**VLM Mode** (Granite):
- AI-powered visual understanding
- Native table/figure comprehension
- Better handling of complex layouts
- Superior quality on difficult documents

## Supported Models

### 1. **Granite-Docling** (Recommended for documents)
- Model: `granite-docling-258m-mlx` (LM Studio)
- Model: `ibm-granite/granite-docling-258M` (VLLM)
- Optimized for document conversion
- Returns DocTags format
- Best for structured documents

### 2. **Granite Vision** (Better for visual content)
- Model: `granite3.2-vision:2b` (Ollama)
- Model: `ibm/granite-vision-3-2-2b` (Watsonx)
- General-purpose vision model
- Returns Markdown format
- Better for images and diagrams

## Setup Methods

### Option 1: LM Studio (Easiest, macOS/Linux/Windows)

**Step 1: Install LM Studio**
```bash
# Download from https://lmstudio.ai/
# Or with Homebrew (macOS):
brew install --cask lm-studio
```

**Step 2: Download Granite Model**
1. Open LM Studio
2. Go to "Discover" tab
3. Search for "granite-docling"
4. Download: `ibm-granite/granite-docling-258M-mlx`

**Step 3: Start Server**
```bash
# In LM Studio, click "Local Server" tab
# Click "Start Server" (default port: 1234)

# Or via CLI:
lms server start
lms load ibm-granite/granite-docling-258M-mlx
```

**Step 4: Configure .env**
```bash
PDF_USE_VLM=true
PDF_VLM_MODEL=granite-docling-258m-mlx
PDF_VLM_ENDPOINT=http://localhost:1234
PDF_VLM_PROMPT=Convert this page to docling.
```

### Option 2: Ollama (Good for Granite Vision)

**Step 1: Install Ollama**
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or with Homebrew (macOS):
brew install ollama
```

**Step 2: Pull Granite Vision**
```bash
ollama pull granite3.2-vision:2b
```

**Step 3: Start Ollama**
```bash
# Ollama runs automatically as a service
# Or start manually:
ollama serve
```

**Step 4: Configure .env**
```bash
PDF_USE_VLM=true
PDF_VLM_MODEL=granite3.2-vision:2b
PDF_VLM_ENDPOINT=http://localhost:11434
PDF_VLM_PROMPT=OCR the full page to markdown.
```

### Option 3: VLLM (Advanced, best performance)

**Step 1: Install VLLM**
```bash
pip install vllm
```

**Step 2: Serve Granite-Docling**
```bash
vllm serve ibm-granite/granite-docling-258M --revision untied --port 8000
```

**Step 3: Configure .env**
```bash
PDF_USE_VLM=true
PDF_VLM_MODEL=ibm-granite/granite-docling-258M
PDF_VLM_ENDPOINT=http://localhost:8000
PDF_VLM_PROMPT=Convert this page to docling.
```

### Option 4: Watsonx.ai (Cloud, requires account)

**Step 1: Get API Credentials**
1. Sign up at [IBM Cloud](https://cloud.ibm.com/)
2. Create Watsonx.ai instance
3. Get API key and Project ID

**Step 2: Configure .env**
```bash
PDF_USE_VLM=true
PDF_VLM_MODEL=ibm/granite-vision-3-2-2b
PDF_VLM_ENDPOINT=https://us-south.ml.cloud.ibm.com
PDF_VLM_PROMPT=OCR the full page to markdown.

# Additional Watsonx credentials
WX_API_KEY=your-api-key
WX_PROJECT_ID=your-project-id
```

## Configuration Reference

### Environment Variables

```bash
# Enable VLM mode (default: false)
PDF_USE_VLM=true

# Model selection
PDF_VLM_MODEL=granite-docling-258m-mlx
# Options:
#   - granite-docling-258m-mlx (LM Studio)
#   - granite3.2-vision:2b (Ollama)
#   - ibm-granite/granite-docling-258M (VLLM)

# Endpoint configuration
PDF_VLM_ENDPOINT=http://localhost:1234
# Options:
#   - http://localhost:1234 (LM Studio default)
#   - http://localhost:11434 (Ollama default)
#   - http://localhost:8000 (VLLM default)

# Prompt customization
PDF_VLM_PROMPT=Convert this page to docling.
# Alternatives:
#   - "OCR the full page to markdown."
#   - "Extract all text, tables, and figures from this page."
#   - "Convert this technical document page to structured format."
```

### Python API

```python
from src.pipeline.pdf_parser import PDFParser

# Option 1: Use config file
parser = PDFParser.from_config()

# Option 2: Manual configuration
parser = PDFParser(
    use_vlm=True,
    vlm_model="granite-docling-258m-mlx",
    vlm_endpoint="http://localhost:1234",
    vlm_prompt="Convert this page to docling.",
    images_scale=2.0
)

# Parse document
result = parser.parse_pdf("document.pdf")
```

## Usage Examples

### Example 1: Granite-Docling with LM Studio

```bash
# .env configuration
PDF_USE_VLM=true
PDF_VLM_MODEL=granite-docling-258m-mlx
PDF_VLM_ENDPOINT=http://localhost:1234
PDF_VLM_PROMPT=Convert this page to docling.
PDF_IMAGES_SCALE=2.0
```

```bash
# Run pipeline
make run-pipeline
```

### Example 2: Granite Vision with Ollama

```bash
# .env configuration
PDF_USE_VLM=true
PDF_VLM_MODEL=granite3.2-vision:2b
PDF_VLM_ENDPOINT=http://localhost:11434
PDF_VLM_PROMPT=OCR the full page to markdown.
```

### Example 3: Programmatic Usage

```python
from pathlib import Path
from src.pipeline.pdf_parser import PDFParser

# Create VLM parser
parser = PDFParser(
    use_vlm=True,
    vlm_model="granite-docling-258m-mlx",
    vlm_endpoint="http://localhost:1234",
    vlm_prompt="Convert this technical document to structured format."
)

# Parse PDF
result = parser.parse_pdf(Path("input/document.pdf"))

# Access results
print(f"Extracted {len(result['chunks'])} chunks")
for chunk in result['chunks'][:3]:
    print(f"Chunk {chunk['chunk_id']}: {chunk['text'][:100]}...")
```

## Performance Comparison

| Mode | Speed | Quality | Tables | Figures | Best For |
|------|-------|---------|--------|---------|----------|
| **Standard OCR** | Fast | Good | Good | Fair | General documents |
| **Granite-Docling** | Medium | Excellent | Excellent | Excellent | Technical docs |
| **Granite Vision** | Slow | Excellent | Excellent | Excellent | Visual-heavy docs |

### Processing Times (21-page PDF)

- Standard OCR: ~20-30 seconds
- Granite-Docling (LM Studio): ~2-3 minutes
- Granite Vision (Ollama): ~3-5 minutes

## When to Use VLM Mode

✅ **Use VLM Mode When:**
- Documents have complex tables
- Layout is non-standard
- High accuracy is critical
- Documents have technical diagrams
- OCR struggles with the content

⚠️ **Use Standard Mode When:**
- Processing speed is priority
- Documents are simple text
- Batch processing many files
- Resources are limited

## Troubleshooting

### Issue: "VLM pipeline not available"

**Solution:** Install VLM dependencies:
```bash
pip install docling[vlm]
# Or
uv pip install docling[vlm]
```

### Issue: Connection refused to endpoint

**Solution:** Verify service is running:
```bash
# For LM Studio
curl http://localhost:1234/v1/models

# For Ollama
curl http://localhost:11434/api/version
```

### Issue: Slow processing

**Solution:** 
1. Reduce image scale: `PDF_IMAGES_SCALE=1.5`
2. Use smaller model (e.g., 2B vs 7B)
3. Use GPU acceleration if available
4. Process fewer pages at once

### Issue: Poor quality results

**Solution:**
1. Increase image scale: `PDF_IMAGES_SCALE=2.5`
2. Adjust prompt to be more specific
3. Try different model (Docling vs Vision)
4. Verify model is fully loaded

### Issue: Out of memory

**Solution:**
1. Use smaller model
2. Reduce batch size
3. Lower image resolution
4. Close other applications

## Model Comparison

### Granite-Docling vs Granite Vision

**Granite-Docling (258M)**
- ✅ Faster processing
- ✅ Better for documents
- ✅ DocTags format (structured)
- ⚠️ Less general-purpose

**Granite Vision (2B/7B)**
- ✅ Better image understanding
- ✅ More flexible prompts
- ✅ Handles varied content
- ⚠️ Slower processing

### Recommendation Matrix

| Document Type | Recommended Model | Endpoint |
|--------------|-------------------|----------|
| Technical papers | Granite-Docling | LM Studio |
| Research articles | Granite-Docling | LM Studio |
| Presentations | Granite Vision | Ollama |
| Infographics | Granite Vision | Ollama |
| Mixed content | Granite Vision | Ollama |
| Production RAG | Standard OCR | N/A |

## Advanced Configuration

### Custom Prompts

```bash
# For technical documents
PDF_VLM_PROMPT=Extract all text, equations, tables, and figure captions from this technical document page. Preserve mathematical notation.

# For financial documents
PDF_VLM_PROMPT=Convert this financial document page to markdown, preserving all numerical data, tables, and calculations.

# For research papers
PDF_VLM_PROMPT=OCR this academic paper page, maintaining section structure, citations, and figure references.
```

### Hybrid Approach

You can use VLM for specific documents:

```python
from src.pipeline.pdf_parser import PDFParser

# Standard parser for most documents
standard_parser = PDFParser.from_config()

# VLM parser for complex documents
vlm_parser = PDFParser(
    use_vlm=True,
    vlm_model="granite-docling-258m-mlx",
    vlm_endpoint="http://localhost:1234"
)

# Choose based on document type
def parse_document(pdf_path):
    if is_complex_document(pdf_path):
        return vlm_parser.parse_pdf(pdf_path)
    else:
        return standard_parser.parse_pdf(pdf_path)
```

## Resources

- [Docling VLM Documentation](https://docling-project.github.io/docling/examples/vlm_pipeline_api_model/)
- [IBM Granite Models](https://github.com/ibm-granite)
- [LM Studio](https://lmstudio.ai/)
- [Ollama](https://ollama.com/)
- [VLLM](https://github.com/vllm-project/vllm)

## FAQ

**Q: Can I use VLM mode without internet?**  
A: Yes, with LM Studio or Ollama running locally.

**Q: Which is faster, LM Studio or Ollama?**  
A: LM Studio is typically faster for Granite-Docling; Ollama is optimized for Vision models.

**Q: Can I use multiple models?**  
A: Yes, create different parser instances with different configurations.

**Q: Does VLM mode work with the RAG pipeline?**  
A: Yes, it's fully compatible. Just enable VLM in `.env` and run the pipeline.

**Q: What GPU is required?**  
A: Optional. Models work on CPU but GPU (NVIDIA/Apple Silicon) accelerates significantly.

**Q: Can I use OpenAI's GPT-4V?**  
A: The architecture supports it, but you'd need to add OpenAI-specific configuration.

## Next Steps

1. ✅ Choose your deployment method (LM Studio recommended for beginners)
2. ✅ Install and start the service
3. ✅ Configure `.env` with VLM settings
4. ✅ Test with a sample PDF: `uv run python src/pipeline/pdf_parser.py`
5. ✅ Run full pipeline: `make run-pipeline`
6. ✅ Compare results with standard mode

For more information, see:
- [PDF Parser Advanced Guide](./PDF_PARSER_ADVANCED.md)
- [Main README](../README.md)

