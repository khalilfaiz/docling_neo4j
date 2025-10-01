# Quick Start Guide

## Prerequisites Check

1. **Neo4j Database**
   - Install Neo4j 5.23+ from https://neo4j.com/download/
   - Start Neo4j: `neo4j start`
   - Access Neo4j Browser at http://localhost:7474
   - Default credentials: neo4j/neo4j (you'll be prompted to change password)

2. **Python Environment**
   - Ensure Python 3.11+ is installed: `python --version`
   - Install UV if not already installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Step-by-Step Setup

### 1. Configure Environment

```bash
# Copy environment template
cp env.example .env

# Edit .env file with your Neo4j password
# The one you set when first accessing Neo4j Browser
```

### 2. Install Dependencies

```bash
make install
```

### 3. Test Components

```bash
# Run component tests to verify setup
uv run python test_components.py
```

You should see:
- ✓ PDF Parser test (will check for PDFs in input/)
- ✓ Embeddings test 
- ✓ Neo4j Connection test
- ✓ Retrieval test (skipped if no data)

### 4. Process Your PDFs

```bash
# The repository includes a sample PDF (hermes-2pages.pdf)
# Run the pipeline to process it
make run-pipeline
```

This will:
1. Parse the PDF with Docling
2. Extract chunks with bounding boxes
3. Generate embeddings
4. Store everything in Neo4j

### 5. Start the Web Interface

```bash
make run-api
```

Open http://localhost:8000 in your browser.

## Try It Out

1. **Search for information:**
   - Try: "What is Hermes?"
   - Try: "architecture" or "components"

2. **Click "View Evidence in PDF"** to see:
   - The PDF opened at the exact page
   - The relevant text highlighted with a blue box
   - Citation details below the viewer

## Troubleshooting

### Neo4j Connection Error
```
Error: Unable to connect to Neo4j
```
**Solution:**
- Check Neo4j is running: `neo4j status`
- Verify password in `.env` matches your Neo4j password
- Ensure Neo4j is listening on bolt://localhost:7687

### No PDF Files Found
```
✗ No PDF files found in input directory
```
**Solution:**
- Ensure PDFs are in the `input/` directory
- Check file permissions

### Import Errors
```
ModuleNotFoundError: No module named 'docling'
```
**Solution:**
- Run `make install` or `uv sync`
- Ensure you're using the UV virtual environment

### Vector Index Error
```
Error creating vector index
```
**Solution:**
- Ensure Neo4j version is 5.23 or higher
- Check Neo4j logs for detailed error

## Next Steps

1. **Add more PDFs:** Place additional PDFs in the `input/` directory
2. **Re-run pipeline:** `make run-pipeline` to process new files
3. **Customize chunking:** Edit `MAX_CHUNK_SIZE` in `src/config.py`
4. **Change embedding model:** Update `EMBEDDING_MODEL` in `.env`

## Common Commands

```bash
# View all available commands
make help

# Clean and restart
make clean
make neo4j-setup
make run-pipeline

# Check Neo4j data
# Open Neo4j Browser and run:
# MATCH (n) RETURN n LIMIT 50
```
