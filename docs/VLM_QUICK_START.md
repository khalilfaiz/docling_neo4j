# VLM Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install LM Studio

**macOS:**
```bash
brew install --cask lm-studio
```

**Other platforms:** Download from https://lmstudio.ai/

### Step 2: Download Granite Model

1. Open LM Studio
2. Click "Discover" tab
3. Search: `granite-docling`
4. Download: `ibm-granite/granite-docling-258M-mlx`

### Step 3: Start Server

In LM Studio:
1. Click "Local Server" tab
2. Select the model
3. Click "Start Server"

### Step 4: Enable VLM in .env

```bash
# Edit your .env file
PDF_USE_VLM=true
PDF_VLM_MODEL=granite-docling-258m-mlx
PDF_VLM_ENDPOINT=http://localhost:1234
PDF_VLM_PROMPT=Convert this page to docling.

# Disable regular image extraction for speed
PDF_GENERATE_PAGE_IMAGES=false
PDF_GENERATE_PICTURE_IMAGES=false
```

### Step 5: Test It!

```bash
# Test parser
uv run python src/pipeline/pdf_parser.py

# Or run full pipeline
make run-pipeline
```

## 🎯 Alternative: Ollama with Granite Vision

### Quick Setup

```bash
# Install Ollama
brew install ollama  # macOS
# Or: curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull granite3.2-vision:2b

# Configure .env
PDF_USE_VLM=true
PDF_VLM_MODEL=granite3.2-vision:2b
PDF_VLM_ENDPOINT=http://localhost:11434
PDF_VLM_PROMPT=OCR the full page to markdown.

# Test
uv run python src/pipeline/pdf_parser.py
```

## 📊 Quick Comparison

| Method | Setup Time | Speed | Quality | Best For |
|--------|------------|-------|---------|----------|
| **Standard OCR** | 0 min | ⚡⚡⚡ Fast | ⭐⭐⭐ Good | Production RAG |
| **LM Studio** | 5 min | ⚡⚡ Medium | ⭐⭐⭐⭐ Excellent | Complex docs |
| **Ollama** | 3 min | ⚡ Slow | ⭐⭐⭐⭐⭐ Superior | Visual content |

## 🔍 Verify Setup

Test if VLM is working:

```python
from src.pipeline.pdf_parser import PDFParser

parser = PDFParser.from_config()
print(f"VLM enabled: {parser.config.get('use_vlm')}")
print(f"Model: {parser.config.get('vlm_model')}")
```

Expected output:
```
🤖 Initializing VLM pipeline with model: granite-docling-258m-mlx
  Using LM Studio/OpenAI-compatible endpoint
VLM enabled: True
Model: granite-docling-258m-mlx
```

## ⚠️ Troubleshooting

**Problem:** "Connection refused"  
**Solution:** Make sure LM Studio server is running (check port 1234)

**Problem:** "VLM pipeline not available"  
**Solution:** Install VLM extras: `uv pip install docling[vlm]`

**Problem:** Too slow  
**Solution:** Use smaller image scale: `PDF_IMAGES_SCALE=1.5`

## 📚 Full Documentation

See [VLM_SETUP_GUIDE.md](./VLM_SETUP_GUIDE.md) for:
- Detailed setup instructions
- All configuration options
- Performance tuning
- Advanced usage
- Model comparisons

## 💡 Tips

1. **Start with LM Studio** - Easiest setup
2. **Use Granite-Docling** - Best for documents
3. **Lower image scale** - Faster processing (1.5-2.0)
4. **Test on one file first** - Before batch processing
5. **Monitor GPU usage** - Ensure hardware acceleration

## 🎓 Next Steps

1. ✅ Get VLM working with a test file
2. ✅ Compare quality with standard mode
3. ✅ Adjust prompt for your document type
4. ✅ Run full pipeline with your documents
5. ✅ Fine-tune performance settings

Ready to use VLM! 🚀

