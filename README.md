# ALouette V3

A layout-aware Retrieval-Augmented Generation (RAG) system that processes PDFs into a searchable knowledge graph with semantic vector search using Docling and Neo4j.

## Architecture

### High-Level Flow
```
PDF Files → Docling Parser → Chunks with BBoxes → Embeddings → Neo4j Graph
                                                                    ↓
User Query → Embedding → Vector Search → Context Expansion → Results with Citations
```

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        INGESTION PIPELINE                        │
├─────────────────────────────────────────────────────────────────┤
│  PDF Files (input/)                                             │
│       ↓                                                          │
│  [PDFParser] - Docling-based parsing with OCR/VLM              │
│       ↓                                                          │
│  [HybridChunker] - Structure-aware chunking                     │
│       ↓                                                          │
│  [EmbeddingGenerator] - Sentence transformers                   │
│       ↓                                                          │
│  [Neo4jIngestion] - Graph database storage                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         QUERY PIPELINE                           │
├─────────────────────────────────────────────────────────────────┤
│  User Query (API/Script)                                        │
│       ↓                                                          │
│  [Retriever] - Vector similarity search                         │
│       ↓                                                          │
│  [Context Expansion] - Fetch neighboring chunks                 │
│       ↓                                                          │
│  [LLMProcessor] - Generate natural language answer (optional)   │
│       ↓                                                          │
│  Results with metadata and citations                            │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **PDF parsing** with Docling including OCR, table structure extraction, and optional image extraction
- **VLM parsing mode** using built-in VLMs models for superior document understanding
  - **Apple Silicon GPU support** via MLX framework (10x faster than CPU)
  - **Detailed progress logging** showing model loading, processing stages, and performance metrics
- **Structure-aware chunking** with optional contextualization that adds hierarchical headings to improve RAG retrieval
- **Vector search** with Neo4j's native vector indexes
- **Context expansion** for better retrieval quality
- **LLM integration** for generating natural language answers with citations
- **Query expansion** for improved search recall
- **Docker support** for easy Neo4j deployment
- **Configurable pipeline** with environment-based settings for different use cases

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

3. **Process PDFs**:
```bash
make run-pipeline-reset  # Fresh start with clean database
```

4. **Query your documents** using the Retriever API (see usage examples below)

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

# Individual operations
make neo4j-setup        # Setup database constraints and indexes
make neo4j-clear        # Clear all data from database
make run-pipeline       # Process PDFs (additive - keeps existing data)
make run-vlm            # Process PDFs with VLM (CPU/Transformers)
make run-vlm-mlx        # Process PDFs with VLM (Apple Silicon GPU)
make export-only        # Export PDFs to markdown without Neo4j ingestion
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

## Project Structure

```
docling_neo4j/
├── input/                      # 📁 Input directory for PDF files
├── output/                     # 📁 Generated outputs (markdown, chunks, images)
├── output_archive/             # 📁 Archived outputs from previous runs
├── input_archive/              # 📁 Archived source PDFs
│
├── docs/                       # 📚 Documentation
│   └── PDF_PARSER_ADVANCED.md  #    Advanced PDF parser configuration guide
│
├── scripts/                    # 🛠️  Utility scripts
│   ├── clear-neo4j.py          #    Clear all data from Neo4j database
│   ├── explore-neo4j.py        #    Explore database contents and statistics
│   ├── export-only.py          #    Export PDFs to markdown without Neo4j ingestion
│   ├── setup-neo4j-auth.sh     #    Setup Neo4j authentication
│   └── test-services.sh        #    Health check for all services
│
├── src/                        # 💻 Source code
│   ├── config.py               #    Central configuration from environment variables
│   │
│   ├── pipeline/               # 🔄 Data processing pipeline
│   │   ├── pdf_parser.py       #    PDF parsing with Docling (OCR, VLM, tables)
│   │   ├── embeddings.py       #    Generate vector embeddings (Sentence Transformers)
│   │   ├── neo4j_setup.py      #    Setup database constraints and vector indexes
│   │   ├── neo4j_ingestion.py  #    Ingest documents/chunks into Neo4j graph
│   │   ├── retrieval.py        #    Vector search and context expansion
│   │   └── llm_processor.py    #    LLM integration for answer generation
│   │
│   ├── api/                    # 🌐 REST API (see front.md)
│   └── web/                    # 🎨 Web UI (see front.md)
│
├── run_pipeline.py             # 🚀 Main entry point - full ingestion pipeline
├── test_components.py          # ✅ Component tests for pipeline modules
├── test_vlm_mlx.py             # ✅ VLM with MLX (Apple Silicon GPU) testing
├── main.py                     # 📝 Simple entry point stub
│
├── docker-compose.yml          # 🐳 Neo4j Docker configuration
├── Makefile                    # ⚙️  Project commands and automation
├── pyproject.toml              # 📦 Python dependencies (uv/pip)
├── uv.lock                     # 🔒 Locked dependency versions
├── env.example                 # 📄 Environment variables template
└── README.md                   # 📖 This file
```

### Core Components Explained

#### 1. **PDFParser** (`src/pipeline/pdf_parser.py`)
- Uses Docling for advanced PDF parsing
- Supports OCR for scanned documents
- Extracts tables with structure preservation
- Optional VLM mode for complex layouts
- Hardware acceleration (CPU/MPS/CUDA)
- Outputs: structured chunks with bounding boxes

#### 2. **EmbeddingGenerator** (`src/pipeline/embeddings.py`)
- Generates vector embeddings using Sentence Transformers
- Supports batch processing for efficiency
- Default model: all-MiniLM-L6-v2 (384 dimensions)
- Embeds contextualized text (with document structure)

#### 3. **Neo4jSetup** (`src/pipeline/neo4j_setup.py`)
- Creates database constraints (unique IDs)
- Creates vector indexes for similarity search
- Verifies Neo4j connection and setup

#### 4. **Neo4jIngestion** (`src/pipeline/neo4j_ingestion.py`)
- Ingests documents into Neo4j graph
- Creates relationships: CONTAINS, HAS_SECTION, INCLUDES, NEXT
- Stores chunks with embeddings and bounding boxes
- Provides statistics and health checks

#### 5. **Retriever** (`src/pipeline/retrieval.py`)
- Performs vector similarity search
- Context expansion (fetches neighboring chunks)
- Supports layout-aware filtering
- Returns results with metadata and bounding boxes

#### 6. **LLMProcessor** (`src/pipeline/llm_processor.py`)
- Generates natural language answers
- Supports OpenAI and Ollama providers
- Maintains proper citations with chunk references
- Fallback to keyword-based answers

## Pipeline Flow

### Ingestion Pipeline (`run_pipeline.py`)

```
1. Neo4jSetup
   ├─ Create constraints (unique IDs)
   ├─ Create vector indexes
   └─ Verify connection
          ↓
2. PDFParser
   ├─ Parse PDF with Docling
   ├─ Extract text, tables, images
   ├─ Generate document structure
   └─ Create chunks with bounding boxes
          ↓
3. EmbeddingGenerator
   ├─ Load Sentence Transformer model
   ├─ Generate embeddings for each chunk
   └─ Add embeddings to chunk data
          ↓
4. Neo4jIngestion
   ├─ Create Document nodes
   ├─ Create Chunk nodes (with embeddings)
   ├─ Create Section nodes
   ├─ Create relationships (CONTAINS, HAS_SECTION, INCLUDES, NEXT)
   └─ Export statistics
```

### Query Pipeline (Programmatic Usage)

```
1. User query (Python script or API call)
          ↓
2. EmbeddingGenerator
   └─ Generate embedding for query text
          ↓
3. Retriever
   ├─ Vector similarity search in Neo4j
   ├─ Context expansion (fetch neighboring chunks)
   └─ Return ranked results with metadata
          ↓
4. LLMProcessor (optional)
   ├─ Generate natural language answer
   ├─ Include chunk citations
   └─ Format response
          ↓
5. Return results
   └─ JSON/dict with chunks, scores, metadata
```

### Example Usage

```python
from src.pipeline.retrieval import Retriever
from src.pipeline.llm_processor import LLMProcessor

# Initialize retriever
retriever = Retriever()

# Search documents
results = retriever.vector_search("What are the accessibility requirements?", top_k=5)

# Optional: Generate LLM answer
llm = LLMProcessor(llm_provider="ollama")
answer = llm.generate_answer_with_citations("What are the accessibility requirements?", results)

# Results contain chunk text, bounding boxes, page numbers, etc.
for result in results:
    print(f"Page {result['page_num']}: {result['text'][:100]}...")
    print(f"BBox: {result['bbox']}")
    print(f"Score: {result['score']}")
```

## Data Model

The system uses the following Neo4j graph structure:

```
(Document)-[:CONTAINS]->(Chunk)
(Document)-[:HAS_SECTION]->(Section)-[:INCLUDES]->(Chunk)
(Chunk)-[:NEXT]->(Chunk)
```

### Node Properties

**Document Node:**
- `docId`: Unique document identifier
- `filename`: Original PDF filename
- `pageCount`: Number of pages
- `filepath`: Path to PDF file

**Chunk Node:**
- `chunkId`: Unique identifier
- `text`: Raw chunk text (for display)
- `textForEmbedding`: Contextualized text (used for vector embedding)
- `embedding`: Vector embedding (384 dimensions)
- `pageNum`: Page number
- `bbox`: Bounding box [x0, y0, x1, y1] for evidence highlighting
- `chunkIndex`: Position in document
- `documentTitle`: Document name for context

**Section Node:**
- `sectionId`: Unique identifier
- `heading`: Section heading text
- `level`: Heading level (1-6)

### Relationships

- `CONTAINS`: Document → Chunk (contains chunks)
- `HAS_SECTION`: Document → Section (document structure)
- `INCLUDES`: Section → Chunk (section membership)
- `NEXT`: Chunk → Chunk (sequential ordering for context expansion)

## Configuration

### Chunking Settings

Configure how text chunks are created and embedded:

```bash
# Use contextualized text (with hierarchical headings) for embeddings
# Recommended: true for better RAG retrieval quality
CHUNK_USE_CONTEXTUALIZED=true
```

**Contextualized Chunking** (Recommended):
- Adds document title and section headings to each chunk before embedding
- Improves semantic search by providing hierarchical context
- Based on Docling's hybrid chunking best practices
- Example: `"IBM\n1960s-1980s\nIn 1961, IBM developed..."`
- Minimal performance impact with significant quality improvement

**Raw Chunking** (`CHUNK_USE_CONTEXTUALIZED=false`):
- Embeds only the raw chunk text without additional context
- Faster but may miss document structure relationships
- Use for simple documents or when structure is not important

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

Then use the LLMProcessor in your Python code:

```python
from src.pipeline.llm_processor import LLMProcessor

llm = LLMProcessor(llm_provider="ollama")  # or "openai"
answer = llm.generate_answer_with_citations(query, search_results)
```

### Query Expansion

The Retriever supports query expansion for improved recall:

```python
results = retriever.vector_search(
    query="accessibility requirements",
    top_k=5,
    expand_query=True  # Generates variations
)
```

How it works:
- Generates multiple query variations
- Searches with different phrasings
- Combines and ranks results for better recall

### Multi-Document Search

The system supports multiple documents:
- **Add new PDFs:** Place in `input/` and run `make run-pipeline` (keeps existing)
- **Fresh start:** `make run-pipeline-reset` (clears all data)
- **Search across all:** Retriever automatically searches entire corpus

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

# Check Neo4j
curl http://localhost:7474
```

## Key Features

This implementation includes several enhancements:

### 🤖 **LLM Integration**
- Natural language answer generation with inline citations
- Support for OpenAI and Ollama providers
- Fallback to keyword-based answers when LLM unavailable
- Programmatic API for custom integrations

### 🐳 **Docker Support**
- One-command Neo4j setup with `make docker-up`
- Persistent data storage with Docker volumes
- Automated health checks and service management

### 🔍 **Advanced Search Capabilities**
- Vector similarity search with embeddings
- Query expansion for better retrieval recall
- Context window expansion for richer results
- Multi-document search across entire corpus
- Layout-aware chunk positioning

### 🛠️ **Developer Experience**
- Comprehensive Makefile with all operations
- Component testing and service health checks
- Database exploration and management tools
- Clear separation of concerns in codebase
- Well-documented Python APIs

### 📄 **PDF Processing**
- VLM mode with GraniteDocling for complex documents
- Apple Silicon GPU acceleration (MLX)
- OCR and table structure extraction
- Bounding box preservation for citations
- Contextualized chunking for better retrieval

## License

This project is for educational and demonstration purposes.

## Acknowledgments

Based on the article "Layout-Aware RAG with Evidence Pins" by Vipul Shah and Dinesh Nair, with significant enhancements for production readiness and developer experience.
