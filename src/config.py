"""Configuration module for the Docling-Neo4j RAG system."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_secure_password")

# Embedding Model Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DIMENSION = 384  # for all-MiniLM-L6-v2

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
STATIC_DIR = PROJECT_ROOT / "src" / "web" / "static"
TEMPLATES_DIR = PROJECT_ROOT / "src" / "web" / "templates"

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Chunking Configuration
MAX_CHUNK_SIZE = 512  # tokens
CHUNK_OVERLAP = 50  # tokens

# PDF Parsing Configuration (Docling)
PDF_IMAGES_SCALE = float(os.getenv("PDF_IMAGES_SCALE", "2.0"))
PDF_GENERATE_PAGE_IMAGES = os.getenv("PDF_GENERATE_PAGE_IMAGES", "false").lower() == "true"
PDF_GENERATE_PICTURE_IMAGES = os.getenv("PDF_GENERATE_PICTURE_IMAGES", "false").lower() == "true"
PDF_DO_OCR = os.getenv("PDF_DO_OCR", "true").lower() == "true"
PDF_DO_TABLE_STRUCTURE = os.getenv("PDF_DO_TABLE_STRUCTURE", "true").lower() == "true"
PDF_DO_PICTURE_DESCRIPTION = os.getenv("PDF_DO_PICTURE_DESCRIPTION", "false").lower() == "true"

# VLM (Vision Language Model) Configuration - Built-in GraniteDocling
PDF_USE_VLM = os.getenv("PDF_USE_VLM", "false").lower() == "true"
# Default to 'mlx' for Apple Silicon Macs (10x faster than transformers)
PDF_VLM_MODEL_TYPE = os.getenv("PDF_VLM_MODEL_TYPE", "mlx")  # 'transformers' or 'mlx'

# Accelerator Configuration
PDF_ACCELERATOR_DEVICE = os.getenv("PDF_ACCELERATOR_DEVICE", "auto")  # 'auto', 'cpu', 'mps', 'cuda'
PDF_ACCELERATOR_THREADS = int(os.getenv("PDF_ACCELERATOR_THREADS", "8"))

# Vector Index Configuration
VECTOR_INDEX_NAME = "chunk_embeddings"
SIMILARITY_THRESHOLD = 0.7
TOP_K_RESULTS = 10

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
