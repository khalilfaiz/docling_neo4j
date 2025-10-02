# VLM Setup with Python (uv/pip installable)

## Overview

This guide shows how to set up VLM mode using **Python-based** tools that can be installed with `uv` or `pip`, without needing separate GUI applications.

## Important Distinction

**Understanding the Options:**

1. **LM Studio** - Desktop GUI app (NOT Python package)
   - ❌ Cannot install with `uv` or `pip`
   - ✅ Easiest to use (point-and-click)
   - ✅ Good for beginners

2. **VLLM** - Python package (CAN install with uv)
   - ✅ Can install with `uv add vllm`
   - ✅ Best performance
   - ✅ Production-ready
   - ⚠️ Requires GPU (NVIDIA)

3. **Ollama** - Standalone binary (NOT Python package)
   - ❌ Cannot install with `uv` or `pip`
   - ✅ Easy to use
   - ✅ Works on Mac/Linux/Windows

## ✅ Recommended: VLLM (Pure Python)

VLLM is a Python package that can be added to your project!

### Installation

```bash
# Option 1: Add to project dependencies
uv add vllm

# Option 2: Install in current environment
uv pip install vllm

# Option 3: Install optional VLM dependencies
uv sync --extra vlm
```

### Requirements

- **NVIDIA GPU** (CUDA support required)
- At least 8GB VRAM for small models
- Linux or macOS (limited Windows support)

### Usage

**1. Start VLLM Server:**
```bash
# Serve Granite-Docling model
uv run vllm serve ibm-granite/granite-docling-258M --revision untied --port 8000

# Or with specific GPU settings
uv run vllm serve ibm-granite/granite-docling-258M \
    --revision untied \
    --port 8000 \
    --gpu-memory-utilization 0.8 \
    --max-model-len 2048
```

**2. Configure .env:**
```bash
PDF_USE_VLM=true
PDF_VLM_MODEL=ibm-granite/granite-docling-258M
PDF_VLM_ENDPOINT=http://localhost:8000
PDF_VLM_PROMPT=Convert this page to docling.
```

**3. Run Pipeline:**
```bash
make run-pipeline
```

### Check VLLM is Running
```bash
curl http://localhost:8000/v1/models
```

## Alternative 1: Use Ollama (Not uv-installable but simple)

If you don't have an NVIDIA GPU, Ollama works on Mac/Linux:

```bash
# Install Ollama (system package, not Python)
curl -fsSL https://ollama.com/install.sh | sh

# Or with Homebrew
brew install ollama

# Pull Granite model
ollama pull granite3.2-vision:2b

# Ollama runs as a service automatically

# Configure .env
PDF_USE_VLM=true
PDF_VLM_MODEL=granite3.2-vision:2b
PDF_VLM_ENDPOINT=http://localhost:11434
```

## Alternative 2: Use LM Studio (Not uv-installable but easiest)

Best for **beginners** or **non-GPU** setups:

```bash
# Install LM Studio (GUI app, not Python package)
brew install --cask lm-studio

# Then use the GUI to:
# 1. Download granite-docling-258m-mlx
# 2. Start Local Server
```

## Comparison: Which to Choose?

| Method | Install Method | GPU Required | Best For |
|--------|---------------|--------------|----------|
| **VLLM** | `uv add vllm` | ✅ NVIDIA GPU | Production, Python devs |
| **Ollama** | System binary | ❌ Works on CPU | Mac users, no GPU |
| **LM Studio** | GUI app | ❌ Works on CPU | Beginners, ease of use |

## Recommended Setup by Use Case

### For Production (Python-only stack)
```bash
# Add VLLM to your project
uv add vllm

# Start VLLM server
uv run vllm serve ibm-granite/granite-docling-258M --revision untied
```

### For Development (Easy testing)
```bash
# Install Ollama
brew install ollama
ollama pull granite3.2-vision:2b

# Or download LM Studio
brew install --cask lm-studio
```

### For No GPU
```bash
# Use Ollama or LM Studio
# Both work without GPU (slower but functional)
```

## Python-Managed VLM Server

If you want to manage the VLM server entirely in Python, here's a helper script:

```python
# scripts/start_vllm_server.py
import subprocess
import sys
from pathlib import Path

def start_vllm_server(
    model: str = "ibm-granite/granite-docling-258M",
    port: int = 8000,
    gpu_memory: float = 0.8
):
    """Start VLLM server with Granite model."""
    
    cmd = [
        sys.executable, "-m", "vllm.entrypoints.openai.api_server",
        "--model", model,
        "--revision", "untied",
        "--port", str(port),
        "--gpu-memory-utilization", str(gpu_memory),
    ]
    
    print(f"Starting VLLM server on port {port}...")
    print(f"Model: {model}")
    print(f"Command: {' '.join(cmd)}")
    
    subprocess.run(cmd)

if __name__ == "__main__":
    start_vllm_server()
```

Usage:
```bash
uv run python scripts/start_vllm_server.py
```

## Makefile Integration

Add VLM server management to your Makefile:

```makefile
# Start VLLM server (requires NVIDIA GPU)
.PHONY: vllm-start
vllm-start:
	@echo "Starting VLLM server..."
	uv run vllm serve ibm-granite/granite-docling-258M \
		--revision untied \
		--port 8000 \
		--gpu-memory-utilization 0.8

# Check if VLLM is running
.PHONY: vllm-check
vllm-check:
	@curl -s http://localhost:8000/v1/models || echo "VLLM not running"

# Run pipeline with VLM
.PHONY: run-pipeline-vlm
run-pipeline-vlm: vllm-check
	@echo "Running pipeline with VLM..."
	PDF_USE_VLM=true $(MAKE) run-pipeline
```

## Environment Management

Create separate environment profiles:

**`.env.vlm-vllm`** (VLLM configuration)
```bash
PDF_USE_VLM=true
PDF_VLM_MODEL=ibm-granite/granite-docling-258M
PDF_VLM_ENDPOINT=http://localhost:8000
PDF_VLM_PROMPT=Convert this page to docling.
```

**`.env.vlm-ollama`** (Ollama configuration)
```bash
PDF_USE_VLM=true
PDF_VLM_MODEL=granite3.2-vision:2b
PDF_VLM_ENDPOINT=http://localhost:11434
PDF_VLM_PROMPT=OCR the full page to markdown.
```

Switch between them:
```bash
# Use VLLM
cp .env.vlm-vllm .env
make run-pipeline

# Use Ollama
cp .env.vlm-ollama .env
make run-pipeline
```

## Troubleshooting

### VLLM Installation Issues

**Problem:** CUDA not found
```bash
# Check CUDA
nvidia-smi

# Install CUDA toolkit if needed
# https://developer.nvidia.com/cuda-downloads
```

**Problem:** Out of memory
```bash
# Use smaller GPU memory utilization
uv run vllm serve ibm-granite/granite-docling-258M \
    --gpu-memory-utilization 0.5 \
    --max-model-len 1024
```

### VLLM vs LM Studio Performance

| Metric | VLLM | LM Studio |
|--------|------|-----------|
| Setup | Complex | Easy |
| Speed | ⚡⚡⚡ Fastest | ⚡⚡ Fast |
| Memory | Optimized | Higher |
| GPU | Required | Optional |

## Complete Python Setup Example

```bash
# 1. Add VLLM to project
cd /Users/khalilfaiz/Documents/1_tests/docling_neo4j
uv add vllm

# 2. Start VLLM server (separate terminal)
uv run vllm serve ibm-granite/granite-docling-258M --revision untied --port 8000

# 3. Configure for VLM
export PDF_USE_VLM=true
export PDF_VLM_ENDPOINT=http://localhost:8000

# 4. Run pipeline
make run-pipeline
```

## Summary

**For Python-only stack:**
- ✅ Use **VLLM** (can install with `uv add vllm`)
- ✅ Requires NVIDIA GPU
- ✅ Best for production

**For ease of use:**
- ✅ Use **LM Studio** (GUI app, not Python package)
- ✅ Works without GPU
- ✅ Best for development/testing

**For Mac users without NVIDIA GPU:**
- ✅ Use **Ollama** (simple binary)
- ✅ Good performance on Apple Silicon
- ✅ Easy to install

---

**Key Takeaway:** While LM Studio can't be installed via `uv`, you can use **VLLM** as a pure Python alternative that integrates perfectly with your `uv` environment!

