# Web Interface Documentation

> ⚠️ **Note:** The web interface is currently under development and not fully tested yet.

## Overview

The Layout-Aware RAG system includes a web interface that provides an intuitive way to search documents and view results with clickable citations that highlight exact PDF regions.

## Architecture

### Web Interface Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         WEB INTERFACE                            │
├─────────────────────────────────────────────────────────────────┤
│  [FastAPI] - REST API endpoints                                 │
│  [Static Templates] - Search & PDF viewer UI                    │
│  [Evidence Pins] - Clickable citations with PDF highlighting    │
└─────────────────────────────────────────────────────────────────┘
```

### Request Flow

```
User Browser
      ↓
[index.html] Search Interface
      ↓
POST /api/search
      ↓
[FastAPI Backend]
      ├─ EmbeddingGenerator → Query embedding
      ├─ Retriever → Vector search
      ├─ LLMProcessor → Generate answer (optional)
      └─ Return JSON response
      ↓
[JavaScript] Render results
      ↓
User clicks citation
      ↓
[viewer.html] PDF Viewer
      ├─ Load PDF
      └─ Highlight bbox region
```

## Features

### 🔍 Search Interface
- **Full-text search** across all ingested documents
- **Vector similarity search** using embeddings
- **Query expansion** for improved recall
- **LLM-powered answers** with inline citations
- **Real-time search** as you type

### 📌 Evidence Pins
- **Clickable citations** in search results
- **Exact PDF region highlighting** using bounding boxes
- **Page-level navigation** to cited content
- **Visual evidence** for answer verification

### 📤 PDF Upload (Background Processing)
- **Drag & drop** PDF upload
- **Background processing** with status tracking
- **Real-time progress** updates
- **Automatic ingestion** into knowledge graph

### 🎨 Modern UI
- **Responsive design** for desktop and mobile
- **Toggle switches** for LLM and query expansion
- **Loading indicators** for better UX
- **Error handling** with user-friendly messages

## Project Structure

### Web-Related Files

```
src/
├── api/                           # 🌐 FastAPI REST backend
│   └── main.py                    #    API endpoints (search, upload, health)
│
└── web/                           # 🎨 Web interface
    ├── static/                    #    Static assets (CSS, JS)
    │   ├── css/
    │   │   └── styles.css         #    Custom styles
    │   └── js/
    │       ├── search.js          #    Search functionality
    │       └── viewer.js          #    PDF viewer with highlighting
    └── templates/                 #    HTML templates
        ├── index.html             #    Search interface with upload
        └── viewer.html            #    PDF viewer with evidence highlighting
```

## FastAPI Backend (`src/api/main.py`)

### Responsibilities
- **REST API endpoints** for search and upload
- **Background PDF processing** with status tracking
- **Serve PDF files** and chunk metadata
- **Health checks** for all services
- **CORS handling** for web requests

### Key Components
- **Search endpoint** - Vector search with optional LLM
- **Upload endpoint** - PDF file upload with validation
- **Status endpoint** - Track processing progress
- **Chunk endpoint** - Get chunk details with bbox
- **Document endpoint** - Serve PDF files
- **Health endpoint** - Service availability checks

## API Endpoints

### Search & Query

#### `POST /api/search`
Vector search with optional LLM answer generation.

**Request:**
```json
{
  "query": "What are the requirements for ramp slopes?",
  "top_k": 5,
  "use_llm": true,
  "query_expansion": false
}
```

**Response:**
```json
{
  "query": "What are the requirements for ramp slopes?",
  "answer": "According to the documents, ramp slopes must...",
  "results": [
    {
      "chunk_id": "doc123_chunk_42",
      "text": "Ramp slopes shall not exceed...",
      "score": 0.89,
      "page_num": 12,
      "bbox": [100, 200, 400, 250],
      "filename": "ada-guidelines.pdf",
      "doc_id": "doc123"
    }
  ],
  "metadata": {
    "result_count": 5,
    "search_time_ms": 245
  }
}
```

### File Management

#### `POST /api/upload`
Upload and process PDF files.

**Request:**
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "file_id": "uuid-1234",
  "filename": "document.pdf",
  "status": "processing",
  "message": "File uploaded successfully"
}
```

#### `GET /api/status/{file_id}`
Check upload processing status.

**Response:**
```json
{
  "file_id": "uuid-1234",
  "status": "completed",
  "progress": 100,
  "doc_id": "doc456",
  "chunks_created": 142
}
```

### Document Access

#### `GET /api/chunk/{chunk_id}`
Get chunk details with metadata.

**Response:**
```json
{
  "chunk_id": "doc123_chunk_42",
  "text": "Full chunk text...",
  "page_num": 12,
  "bbox": [100, 200, 400, 250],
  "doc_id": "doc123",
  "filename": "ada-guidelines.pdf"
}
```

#### `GET /api/document/{doc_id}/pdf`
Serve PDF file for viewing.

**Response:** Binary PDF file stream

### Health & Status

#### `GET /health`
Service health check.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "neo4j": "connected",
    "embeddings": "ready"
  }
}
```

#### `GET /`
Main search interface (HTML page).

#### `GET /viewer`
PDF viewer with evidence highlighting (HTML page).

## Usage

### Starting the Web Interface

```bash
# Start FastAPI server
make run-api

# Or manually
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000 in your browser.

### Available Make Commands

```bash
make run-api            # Start the web interface
make test-services      # Test all services including API
```

### Example Workflow

1. **Start the pipeline and API:**
```bash
make run-pipeline-reset  # Process PDFs
make run-api            # Start web interface
```

2. **Open browser** to http://localhost:8000

3. **Search your documents:**
   - Type a question in the search box
   - Toggle "Use LLM for answers" for AI-generated responses
   - Toggle "Query expansion" for better recall

4. **View results:**
   - See ranked search results with snippets
   - Click citations to open PDF viewer
   - View highlighted regions in the PDF

5. **Upload new PDFs:**
   - Click "Upload PDF" button
   - Drag & drop or select file
   - Wait for processing to complete
   - Search the new document

## Advanced Features

### LLM Integration

Enable AI-powered answers in the web interface:

1. **Setup LLM provider:**

```bash
# Option 1: Ollama (local)
brew install ollama
ollama serve
ollama pull llama2

# Option 2: OpenAI (cloud)
export OPENAI_API_KEY="your-api-key"
```

2. **Configure in `.env`:**
```bash
LLM_PROVIDER=ollama  # or 'openai'
LLM_MODEL=llama2     # or 'gpt-3.5-turbo'
```

3. **Use in web interface:**
   - Check "Use LLM for answers" toggle
   - Submit your query
   - Get natural language answers with citations

### Query Expansion

Improve search results by enabling query expansion:

1. **Check "Query expansion"** toggle in the web interface
2. **How it works:**
   - Generates multiple query variations
   - Searches with different phrasings
   - Combines and ranks results
   - Better recall for complex queries

### Multi-Document Search

The web interface supports searching across multiple documents:

- **Add new PDFs:** Upload via web interface
- **Search all documents:** No filtering needed
- **Filter by document:** (Coming soon)
- **View document statistics:** (Coming soon)

## Example Queries

Try these queries in the search interface:

- "What are the requirements for ramp slopes?"
- "What are the accessibility standards for handrails?"
- "What are the ADA requirements for doorways?"
- "Explain the Hermes vehicle architecture"
- "What is the navigation system?"

## Troubleshooting

### Web Interface Not Loading

```bash
# Check if API is running
curl http://localhost:8000/health

# Check logs
uv run uvicorn src.api.main:app --reload

# Restart API
# Press Ctrl+C and run again
make run-api
```

### Search Not Returning Results

```bash
# Check database contents
uv run python scripts/explore-neo4j.py

# Verify embeddings are generated
# Check Neo4j browser at http://localhost:7474

# Try broader search terms or enable query expansion
```

### PDF Upload Failing

```bash
# Check file size limits (default: 50MB)
# Check file format (must be PDF)
# Check disk space in output/ directory
# Verify Neo4j is running and accessible
```

### Evidence Pins Not Highlighting

```bash
# Verify bounding boxes exist in chunks
# Check browser console for JavaScript errors
# Ensure PDF.js library is loaded
# Try refreshing the page
```

### LLM Answers Not Working

```bash
# Check LLM provider is running
ollama list  # For Ollama

# Check API key for OpenAI
echo $OPENAI_API_KEY

# Check configuration in .env
cat .env | grep LLM

# Test LLM directly
curl http://localhost:11434/api/generate  # Ollama
```

## Development

### Running in Development Mode

```bash
# With auto-reload
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# With debug logging
uv run uvicorn src.api.main:app --reload --log-level debug
```

### Testing the API

```bash
# Health check
curl http://localhost:8000/health

# Search test
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "top_k": 5}'

# Upload test
curl -X POST http://localhost:8000/api/upload \
  -F "file=@test.pdf"
```

### Frontend Development

The frontend uses vanilla JavaScript with no build step required:

1. **Edit templates:** `src/web/templates/*.html`
2. **Edit styles:** `src/web/static/css/styles.css`
3. **Edit scripts:** `src/web/static/js/*.js`
4. **Refresh browser** to see changes

### Adding New Endpoints

1. **Define route** in `src/api/main.py`:
```python
@app.get("/api/my-endpoint")
async def my_endpoint():
    return {"message": "Hello"}
```

2. **Update frontend** to call new endpoint:
```javascript
const response = await fetch('/api/my-endpoint');
const data = await response.json();
```

## Security Considerations

> ⚠️ **Important:** The current implementation is for development/demo purposes.

For production deployment:

1. **Add authentication:**
   - Implement user authentication
   - Use JWT tokens or session management
   - Protect sensitive endpoints

2. **Add rate limiting:**
   - Limit requests per IP/user
   - Prevent abuse of upload endpoint
   - Throttle expensive operations

3. **Validate inputs:**
   - Sanitize user queries
   - Validate file uploads
   - Check file types and sizes

4. **Use HTTPS:**
   - Enable SSL/TLS
   - Secure cookie flags
   - HSTS headers

5. **Configure CORS properly:**
   - Restrict allowed origins
   - Set appropriate headers
   - Validate referers

## Future Enhancements

Planned features for the web interface:

- [ ] Document filtering and faceting
- [ ] Advanced search operators
- [ ] Search history and saved queries
- [ ] Document comparison view
- [ ] Annotation and highlighting tools
- [ ] Export search results
- [ ] User accounts and preferences
- [ ] Mobile app
- [ ] Real-time collaboration
- [ ] Custom styling themes

## Contributing

To contribute to the web interface:

1. Review the codebase structure
2. Test your changes thoroughly
3. Follow existing code style
4. Update documentation
5. Submit detailed pull request

## Support

For web interface issues:
- Check this documentation
- Review API logs
- Test with curl/Postman
- Report bugs with screenshots and browser info

