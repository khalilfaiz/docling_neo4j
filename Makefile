.PHONY: help setup install neo4j-setup run-pipeline run-pipeline-reset export-only run-api clean test docker-up docker-down neo4j-clear

# Default target
help:
	@echo "Available commands:"
	@echo "  make install         - Install project dependencies"
	@echo "  make docker-up       - Start Neo4j in Docker"
	@echo "  make docker-down     - Stop Neo4j Docker container"
	@echo "  make neo4j-setup     - Setup Neo4j database (constraints and indexes)"
	@echo "  make neo4j-clear     - Clear all data from Neo4j database"
	@echo "  make export-only     - Parse PDFs and export markdown/chunks (no Neo4j)"
	@echo "  make run-pipeline    - Process PDFs and ingest into Neo4j"
	@echo "  make run-pipeline-reset - Clear database then run pipeline"
	@echo "  make run-vlm         - Process PDFs with VLM (Vision Language Model)"
	@echo "  make run-vlm-mlx     - Process PDFs with VLM using Apple Silicon GPU"
	@echo "  make run-api         - Start the FastAPI server"
	@echo "  make test-services   - Test all services"
	@echo "  make clean           - Clean generated files"
	@echo "  make test            - Run component tests"

# Install dependencies
install:
	uv sync

# Docker commands
docker-up:
	docker-compose up -d
	@echo "Waiting for Neo4j to start..."
	@sleep 10
	@echo "Neo4j is running at http://localhost:7474"

docker-down:
	docker-compose down

# Setup Neo4j database
neo4j-setup:
	uv run python src/pipeline/neo4j_setup.py

# Export PDFs to markdown and chunks only (no Neo4j)
export-only:
	uv run python scripts/export-only.py

# Run the complete pipeline
run-pipeline:
	uv run python run_pipeline.py

# Start the API server
run-api:
	uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Test all services
test-services:
	./scripts/test-services.sh

# Clean generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf output/*

# Clear Neo4j database
neo4j-clear:
	uv run python scripts/clear-neo4j.py

# Clear database and run pipeline
run-pipeline-reset: neo4j-clear neo4j-setup run-pipeline
	@echo "✓ Pipeline reset completed!"

# Run component tests
test:
	uv run python test_components.py

# Run VLM pipeline with Transformers (CPU)
run-vlm:
	@echo "🤖 Running VLM pipeline with Transformers (CPU)..."
	PDF_USE_VLM=true PDF_VLM_MODEL_TYPE=transformers uv run python run_pipeline.py

# Run VLM pipeline with MLX (Apple Silicon GPU)
run-vlm-mlx:
	@echo "🍎 Running VLM pipeline with MLX (Apple Silicon GPU)..."
	PDF_USE_VLM=true PDF_VLM_MODEL_TYPE=mlx uv run python run_pipeline.py
