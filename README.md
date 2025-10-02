# Layout-Aware RAG with Evidence Pins

A layout-aware Retrieval-Augmented Generation (RAG) system that provides clickable citations with exact PDF region highlighting using Docling and Neo4j.

## Features

- **Advanced PDF parsing** with Docling including OCR, table structure extraction, and optional image extraction
- **VLM parsing mode** using built-in GraniteDocling model for superior document understanding
  - **Apple Silicon GPU support** via MLX framework (10x faster than CPU)
  - **Detailed progress logging** showing model loading, processing stages, and performance metrics
  - No external server required
- **Structure-aware chunking** that respects document structure with hierarchical headings
- **Vector search** with Neo4j's native vector indexes
- **Clickable evidence pins** that open PDFs with highlighted regions
- **Context expansion** for better retrieval quality
- **Web interface** for search and PDF viewing
- **LLM integration** for generating natural language answers with citations
- **Query expansion** for improved search recall
- **PDF upload** through web interface with background processing
- **Docker support** for easy Neo4j deployment
- **Configurable pipeline** with environment-based settings for different use cases

## Architecture

```
PDF Files → Docling Parser → Chunks with BBoxes → Embeddings → Neo4j Graph
                                                                    ↓
User Query → Embedding → Vector Search → Context Expansion → Results with Citations
```

## Prerequisites

- Python 3.11+
- Neo4j 5.23+ (with vector index support)
- UV package manager

## Quick Start

1. **Clone and setup**:
```bash
cd docling_neo4j
make install
```

2. **Start Neo4j with Docker**:
```bash
make docker-up
```

3. **Process PDFs and start the system**:
```bash
make run-pipeline-reset  # Fresh start
make run-api            # Start web interface
```

4. **Open http://localhost:8000** in your browser

## Manual Installation

If you prefer manual setup:

1. Install dependencies:
```bash
make install
```

2. Configure Neo4j connection:
```bash
# Copy the example config
cp env.example .env

# Edit .env with your Neo4j credentials
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your_secure_password
```

3. Start Neo4j (Docker or local installation)

## Usage

### Available Commands

```bash
# Quick start commands
make docker-up           # Start Neo4j in Docker
make run-pipeline-reset  # Clear database and process all PDFs
make run-api            # Start the web interface

# Individual operations
make neo4j-setup        # Setup database constraints and indexes
make neo4j-clear        # Clear all data from database
make run-pipeline       # Process PDFs (additive - keeps existing data)
make run-vlm            # Process PDFs with VLM (CPU/Transformers)
make run-vlm-mlx        # Process PDFs with VLM (Apple Silicon GPU)
make test-services      # Test all services health
make clean              # Clean generated files

# Development
make test               # Run component tests
make help               # Show all available commands
```

### Processing PDFs

1. **Place PDFs** in the `input/` directory
2. **Choose your parsing mode**:
   - **Standard mode** (default): Fast, OCR-based parsing
   - **VLM mode**: Advanced AI understanding with GraniteDocling
     - **CPU**: `make run-vlm` (works everywhere)
     - **GPU**: `make run-vlm-mlx` (10x faster on Apple Silicon M1/M2/M3/M4)
3. **Choose your approach**:
   - **Fresh start**: `make run-pipeline-reset` (clears existing data)
   - **Add to existing**: `make run-pipeline` (keeps existing data)

**Example with detailed logging:**
```bash
# Standard parsing
make run-pipeline

# VLM with Apple Silicon GPU (recommended for Macs)
make run-vlm-mlx

# VLM with CPU
make run-vlm
```

### Web Interface Features

Open http://localhost:8000 to access:

- **Search Interface**: Ask questions about your documents
- **Evidence Pins**: Click citations to see exact PDF regions highlighted
- **PDF Upload**: Upload new PDFs directly through the web interface
- **LLM Integration**: Enable AI-powered answers with citations
- **Query Expansion**: Improve search results with query variations

## Project Structure

```
docling_neo4j/
├── input/               # Place PDF files here
├── output/              # Generated outputs (markdown, chunks, images)
├── docs/                # Documentation
│   ├── PDF_PARSER_ADVANCED.md  # Advanced parser guide
│   └── VLM_SETUP_GUIDE.md      # VLM/Granite setup guide
├── scripts/             # Utility scripts
│   ├── clear-neo4j.py          # Database clearing
│   ├── explore-neo4j.py        # Database exploration
│   ├── demo_advanced_parser.py # Parser demo script
│   └── test-services.sh        # Service health checks
├── src/
│   ├── api/            # FastAPI backend
│   │   └── main.py     # API endpoints and file upload
│   ├── pipeline/       # Data processing pipeline
│   │   ├── pdf_parser.py      # Advanced Docling PDF parsing (enhanced)
│   │   ├── embeddings.py      # Sentence transformers
│   │   ├── llm_processor.py   # LLM integration
│   │   ├── neo4j_setup.py     # Database setup
│   │   ├── neo4j_ingestion.py # Data ingestion
│   │   └── retrieval.py       # Vector search & context expansion
│   ├── web/            # Web interface
│   │   └── templates/
│   │       ├── index.html     # Search interface with upload
│   │       └── viewer.html    # PDF viewer with highlights
│   └── config.py       # Configuration (with PDF parser settings)
├── docker-compose.yml  # Neo4j Docker setup
├── run_pipeline.py     # Main pipeline script
├── test_components.py  # Component testing
├── env.example         # Environment variables template
├── Makefile           # Project commands
└── README.md
```

## Data Model

The system uses the following Neo4j graph structure:

```
(Document)-[:CONTAINS]->(Chunk)
(Document)-[:HAS_SECTION]->(Section)-[:INCLUDES]->(Chunk)
(Chunk)-[:NEXT]->(Chunk)
```

Each Chunk node contains:
- `chunkId`: Unique identifier
- `text`: The chunk text
- `pageNum`: Page number
- `bbox`: Bounding box [x0, y0, x1, y1]
- `embedding`: Vector embedding
- `chunkIndex`: Position in document

## API Endpoints

- `GET /`: Main search interface with upload capability
- `GET /viewer`: PDF viewer with evidence highlighting
- `POST /api/search`: Vector search with LLM integration
- `POST /api/upload`: Upload and process PDF files
- `GET /api/status/{file_id}`: Check upload processing status
- `GET /api/chunk/{chunk_id}`: Get chunk details
- `GET /api/document/{doc_id}/pdf`: Serve PDF files
- `GET /health`: Service health check

## Configuration

### PDF Parser Settings

The parser supports advanced Docling features configurable via `.env`:

```bash
# OCR and table extraction (recommended defaults)
PDF_DO_OCR=true                    # Enable OCR for scanned documents
PDF_DO_TABLE_STRUCTURE=true        # Extract table structure with cell matching
PDF_IMAGES_SCALE=2.0               # Image resolution scale factor

# Image extraction (optional, increases processing time)
PDF_GENERATE_PAGE_IMAGES=false     # Extract full page images
PDF_GENERATE_PICTURE_IMAGES=false  # Extract figure/picture images

# VLM Mode - Built-in GraniteDocling (optional, superior quality, no server needed)
PDF_USE_VLM=false                  # Enable VLM parsing mode
PDF_VLM_MODEL_TYPE=transformers    # 'transformers' or 'mlx' (macOS MPS)

# Accelerator Configuration (CPU/GPU acceleration)
PDF_ACCELERATOR_DEVICE=auto        # 'auto', 'cpu', 'mps' (macOS), 'cuda' (NVIDIA)
PDF_ACCELERATOR_THREADS=8          # Number of CPU threads
```

**Parsing Modes:**

1. **Standard Mode (Default)** - Fast, good quality
   - Uses OCR + layout analysis
   - Hardware acceleration support (CPU/MPS/CUDA)
   - Best for: General documents, production RAG
   
2. **VLM Mode (GraniteDocling)** - Slower, excellent quality
   - Uses built-in vision-language model
   - No external server required (runs locally)
   - MLX support for macOS MPS acceleration
   - Best for: Complex layouts, technical documents, tables

**For standard RAG pipelines (recommended):**
- Keep OCR and table structure enabled
- Use hardware acceleration (auto-detect)
- Keep VLM disabled for speed

**For complex documents needing superior quality:**
- Enable VLM mode: `PDF_USE_VLM=true`
- Use MLX on macOS: `PDF_VLM_MODEL_TYPE=mlx`
- No external setup required!

See [docs/PDF_PARSER_ADVANCED.md](docs/PDF_PARSER_ADVANCED.md) for detailed configuration guide.

### Demo Script

Test different parser configurations:
```bash
uv run python scripts/demo_advanced_parser.py
```

## Advanced Features

### LLM Integration

Enable AI-powered answers with proper citations:

```bash
# Option 1: Use Ollama (local)
brew install ollama
ollama serve
ollama pull llama2

# Option 2: Use OpenAI (cloud)
export OPENAI_API_KEY="your-api-key"
```

Then check "Use LLM for answers" in the web interface.

### Query Expansion

Improve search results by checking "Query expansion" which:
- Generates multiple query variations
- Searches with different phrasings
- Combines results for better recall

### Multi-Document Search

The system supports multiple documents:
- Add new PDFs: `make run-pipeline` (keeps existing)
- Fresh start: `make run-pipeline-reset` (clears all)
- Upload via web: Click "Upload PDF" button

## Example Queries

- "What are the requirements for ramp slopes?"
- "What are the accessibility standards for handrails?"
- "What are the ADA requirements for doorways?"
- "Explain the Hermes vehicle architecture"
- "What is the navigation system?"

## Troubleshooting

### Neo4j Connection Issues
```bash
# Check if Neo4j is running
make test-services

# Restart Neo4j
make docker-down && make docker-up

# Check credentials in .env file
cat .env
```

### PDF Parsing Issues
```bash
# Test individual components
make test

# Check Docling installation
uv run docling --version

# Ensure PDFs are not encrypted or corrupted
```

### Search Not Finding Results
```bash
# Check database contents
uv run python scripts/explore-neo4j.py

# Verify embeddings are generated
# Check Neo4j browser at http://localhost:7474

# Try broader search terms or enable query expansion
```

### Service Health
```bash
# Comprehensive service check
make test-services

# Individual health checks
curl http://localhost:8000/health
curl http://localhost:7474
```

## Recent Improvements

This implementation includes several enhancements over the original concept:

### 🤖 **LLM Integration**
- Natural language answer generation with inline citations
- Support for OpenAI and Ollama providers
- Fallback to keyword-based answers when LLM unavailable

### 📤 **File Upload System**
- Upload PDFs directly through web interface
- Background processing with status tracking
- No need to manually place files in directories

### 🐳 **Docker Support**
- One-command Neo4j setup with `make docker-up`
- Persistent data storage with Docker volumes
- Automated health checks and service management

### 🔍 **Enhanced Search**
- Query expansion for better retrieval recall
- Context window expansion for richer results
- Multi-document search across entire corpus

### 🛠️ **Developer Experience**
- Comprehensive Makefile with all operations
- Component testing and service health checks
- Database exploration and management tools
- Clear separation of concerns in codebase

### 🎨 **Improved Web Interface**
- Modern, responsive design
- Real-time upload progress and status
- Toggle switches for LLM and query expansion features
- Better error handling and user feedback

## License

This project is for educational and demonstration purposes.

## Acknowledgments

Based on the article "Layout-Aware RAG with Evidence Pins" by Vipul Shah and Dinesh Nair, with significant enhancements for production readiness and developer experience.
