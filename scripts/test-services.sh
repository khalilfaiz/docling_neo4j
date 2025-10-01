#!/bin/bash

# Test script for Layout-Aware RAG services

echo "========================================="
echo "Testing Layout-Aware RAG Services"
echo "========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Neo4j is running
echo -n "Checking Neo4j connection... "
if curl -s -f http://localhost:7474 > /dev/null; then
    echo -e "${GREEN}✓ Neo4j is running${NC}"
else
    echo -e "${RED}✗ Neo4j is not accessible${NC}"
    echo "  Start Neo4j with: docker-compose up -d"
    exit 1
fi

# Check if API is running
echo -n "Checking API health... "
if curl -s -f http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ API is healthy${NC}"
else
    echo -e "${YELLOW}⚠ API is not running${NC}"
    echo "  Start API with: make run-api"
fi

# Test Neo4j data
echo -n "Checking Neo4j data... "
CHUNK_COUNT=$(curl -s -X POST http://localhost:7474/db/neo4j/tx/commit \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'neo4j:your_secure_password' | base64)" \
  -d '{"statements":[{"statement":"MATCH (c:Chunk) RETURN count(c) as count"}]}' \
  | grep -o '"count":[0-9]*' | grep -o '[0-9]*' || echo "0")

if [ "$CHUNK_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $CHUNK_COUNT chunks in database${NC}"
else
    echo -e "${YELLOW}⚠ No chunks found in database${NC}"
    echo "  Run pipeline with: make run-pipeline"
fi

# Test search endpoint
if [ "$CHUNK_COUNT" -gt 0 ]; then
    echo -n "Testing search endpoint... "
    SEARCH_RESPONSE=$(curl -s -X POST http://localhost:8000/api/search \
      -H "Content-Type: application/json" \
      -d '{"query": "test search", "top_k": 3}')
    
    if echo "$SEARCH_RESPONSE" | grep -q "results"; then
        echo -e "${GREEN}✓ Search endpoint working${NC}"
    else
        echo -e "${RED}✗ Search endpoint failed${NC}"
    fi
fi

# Test upload endpoint
echo -n "Testing upload endpoint... "
if curl -s -f -X POST http://localhost:8000/api/upload \
  -F "file=@/dev/null" 2>/dev/null | grep -q "Only PDF files"; then
    echo -e "${GREEN}✓ Upload endpoint validation working${NC}"
else
    echo -e "${YELLOW}⚠ Upload endpoint not responding correctly${NC}"
fi

echo ""
echo "========================================="
echo "Test Summary:"
echo "========================================="

if [ "$CHUNK_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ System is ready for use${NC}"
    echo ""
    echo "Try these commands:"
    echo "  - Open http://localhost:8000 in your browser"
    echo "  - Search for information in your documents"
    echo "  - Upload new PDFs through the API"
else
    echo -e "${YELLOW}⚠ System needs data${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Place PDFs in the input/ directory"
    echo "  2. Run: make run-pipeline"
    echo "  3. Start API: make run-api"
fi
