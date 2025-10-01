"""FastAPI backend for the Layout-Aware RAG system."""

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path
import sys
import shutil
import uuid

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.config import API_HOST, API_PORT, TEMPLATES_DIR, STATIC_DIR, INPUT_DIR
from src.pipeline.retrieval import Retriever


# Initialize FastAPI app
app = FastAPI(
    title="Layout-Aware RAG with Evidence Pins",
    description="Search documents with clickable citations that highlight exact PDF regions",
    version="1.0.0"
)

# Setup templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Initialize retriever
retriever = Retriever()


# Request/Response models
class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    context_window: int = 1
    use_llm: bool = False
    use_query_expansion: bool = False
    llm_provider: str = "ollama"


class ChunkInfo(BaseModel):
    chunk_id: str
    text: str
    page_num: int
    bbox: List[float]
    chunk_index: int
    doc_id: str
    filename: str
    filepath: str
    section_headings: List[str]
    score: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    results: List[ChunkInfo]
    expanded_context: Optional[List[ChunkInfo]] = None
    answer: Optional[str] = None
    answer_with_citations: Optional[str] = None


# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main search interface."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/viewer", response_class=HTMLResponse)
async def viewer(request: Request):
    """Serve the PDF viewer interface."""
    return templates.TemplateResponse("viewer.html", {"request": request})


@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Perform vector search on the documents."""
    try:
        # Perform retrieval with optional query expansion
        results = retriever.retrieve_with_context(
            query=request.query,
            top_k=request.top_k,
            context_window=request.context_window,
            use_query_expansion=request.use_query_expansion
        )
        
        # Convert to response format
        response_data = {
            "query": results["query"],
            "results": [ChunkInfo(**r) for r in results["results"]],
            "expanded_context": [ChunkInfo(**r) for r in results["expanded_context"]] if results["expanded_context"] else None
        }
        
        # Generate LLM answer if requested
        if request.use_llm and results["results"]:
            try:
                from src.pipeline.llm_processor import LLMProcessor
                llm = LLMProcessor(llm_provider=request.llm_provider)
                
                # Generate answer with citations
                answer = llm.generate_answer_with_citations(
                    request.query, 
                    results["results"]
                )
                response_data["answer"] = answer
                response_data["answer_with_citations"] = create_clickable_citations(answer, results["results"])
                
            except Exception as llm_error:
                print(f"LLM generation failed: {llm_error}")
                # Continue without LLM answer
        
        return SearchResponse(**response_data)
        
    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def create_clickable_citations(text: str, chunks: List[Dict[str, Any]]) -> str:
    """Convert [chunk_id] citations to clickable links."""
    import re
    
    # Create mapping of chunk_id to chunk data
    chunk_map = {chunk["chunk_id"]: chunk for chunk in chunks}
    
    # Replace [chunk_id] with clickable links
    def replace_citation(match):
        chunk_id = match.group(1)
        if chunk_id in chunk_map:
            chunk = chunk_map[chunk_id]
            url = f"/viewer?doc={chunk['doc_id']}&page={chunk['page_num']}&bbox={','.join(map(str, chunk['bbox']))}&chunk={chunk_id}"
            return f'<a href="{url}" target="_blank">[{chunk_id}]</a>'
        return match.group(0)
    
    return re.sub(r'\[([^\]]+)\]', replace_citation, text)


@app.get("/api/chunk/{chunk_id}")
async def get_chunk(chunk_id: str):
    """Get details for a specific chunk."""
    try:
        chunk = retriever.get_chunk_by_id(chunk_id)
        
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")
        
        return chunk
        
    except Exception as e:
        print(f"Error fetching chunk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/document/{doc_id}/pdf")
async def get_document_pdf(doc_id: str):
    """Serve the PDF file for a document."""
    try:
        # Get document info from Neo4j
        with retriever.driver.session() as session:
            result = session.run("""
                MATCH (d:Document {docId: $doc_id})
                RETURN d.filepath as filepath, d.filename as filename
            """, {"doc_id": doc_id})
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Document not found")
            
            filepath = record["filepath"]
            filename = record["filename"]
        
        # Check if file exists
        pdf_path = Path(filepath)
        if not pdf_path.exists():
            # Try relative to input directory
            pdf_path = INPUT_DIR / filename
            if not pdf_path.exists():
                raise HTTPException(status_code=404, detail="PDF file not found")
        
        # Return the PDF file
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error serving PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process a PDF file."""
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_path = INPUT_DIR / f"{file_id}_{file.filename}"
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process in background
        background_tasks.add_task(process_uploaded_pdf, file_path, file_id)
        
        return JSONResponse({
            "message": "File uploaded successfully. Processing started.",
            "file_id": file_id,
            "filename": file.filename
        })
        
    except Exception as e:
        # Clean up on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


async def process_uploaded_pdf(file_path: Path, file_id: str):
    """Process uploaded PDF in background."""
    try:
        from src.pipeline.pdf_parser import PDFParser
        from src.pipeline.embeddings import EmbeddingGenerator
        from src.pipeline.neo4j_ingestion import Neo4jIngestion
        
        # Parse PDF
        parser = PDFParser()
        result = parser.parse_pdf(file_path)
        
        # Generate embeddings
        generator = EmbeddingGenerator()
        result["chunks"] = generator.add_embeddings_to_chunks(result["chunks"])
        
        # Ingest into Neo4j
        ingestion = Neo4jIngestion()
        try:
            ingestion.ingest_document(result["metadata"], result["chunks"])
        finally:
            ingestion.close()
            
        print(f"✓ Successfully processed uploaded file: {file_id}")
        
    except Exception as e:
        print(f"✗ Error processing uploaded file {file_id}: {e}")


@app.get("/api/status/{file_id}")
async def check_upload_status(file_id: str):
    """Check the status of an uploaded file."""
    # Simple implementation - in production, use a task queue
    with retriever.driver.session() as session:
        result = session.run("""
            MATCH (d:Document)
            WHERE d.docId CONTAINS $file_id
            RETURN d.docId as doc_id, d.filename as filename
            LIMIT 1
        """, {"file_id": file_id})
        
        record = result.single()
        if record:
            return {
                "status": "completed",
                "doc_id": record["doc_id"],
                "filename": record["filename"]
            }
        else:
            return {"status": "processing"}


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown."""
    retriever.close()


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "layout-aware-rag"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
