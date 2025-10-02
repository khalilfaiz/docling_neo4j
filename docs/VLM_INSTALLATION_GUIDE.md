# VLM Installation Guide: uv vs System Installation

## Understanding the Options

When setting up VLM mode, you have different installation methods depending on which tool you choose.

## 📦 Can Install with `uv` or `pip`

### ✅ VLLM (Pure Python Package)

**What it is:** High-performance inference engine for LLMs  
**Installation:** `uv add vllm` or `pip install vllm`  
**Type:** Python package

```bash
# Add to your project
cd /Users/khalilfaiz/Documents/1_tests/docling_neo4j
uv add vllm

# Or install in current environment
uv pip install vllm

# Start server
uv run vllm serve ibm-granite/granite-docling-258M --revision untied --port 8000
```

**Requirements:**
- NVIDIA GPU with CUDA
- Linux or macOS
- At least 8GB VRAM

**Pros:**
- ✅ Installs with `uv`/`pip`
- ✅ Best performance
- ✅ Production-ready
- ✅ Pure Python stack

**Cons:**
- ❌ Requires NVIDIA GPU
- ❌ More complex setup

## 🖥️ System/GUI Installation Only

### ❌ LM Studio (Desktop Application)

**What it is:** GUI application for running LLMs locally  
**Installation:** `brew install --cask lm-studio` (system package)  
**Type:** Desktop application (like VS Code or Chrome)

```bash
# Install as system application (NOT Python package)
brew install --cask lm-studio

# Or download from: https://lmstudio.ai/
```

**Why not uv/pip?**
- LM Studio is a **GUI desktop app**, not a Python library
- Similar to Chrome, Slack, or VS Code
- Has its own installer and runs independently

**Pros:**
- ✅ Easy to use (point-and-click)
- ✅ Works without GPU
- ✅ Great for beginners
- ✅ Visual model management

**Cons:**
- ❌ Cannot install via `uv` or `pip`
- ❌ Not part of Python environment
- ❌ Must install separately

### ❌ Ollama (System Binary)

**What it is:** Command-line tool for running LLMs  
**Installation:** `brew install ollama` or system installer  
**Type:** System binary (like `git` or `docker`)

```bash
# Install as system tool (NOT Python package)
brew install ollama

# Or: curl -fsSL https://ollama.com/install.sh | sh
```

**Why not uv/pip?**
- Ollama is a **system daemon**, not a Python library
- Written in Go, not Python
- Runs as a background service

**Pros:**
- ✅ Simple CLI
- ✅ Works without GPU
- ✅ Good for Mac users
- ✅ Auto-starts on boot

**Cons:**
- ❌ Cannot install via `uv` or `pip`
- ❌ Not part of Python environment

## Comparison Matrix

| Tool | Install Method | Type | Can use `uv add`? | GPU Required |
|------|---------------|------|-------------------|--------------|
| **VLLM** | `uv add vllm` | Python package | ✅ Yes | ✅ NVIDIA |
| **LM Studio** | `brew install --cask` | Desktop app | ❌ No | ❌ No |
| **Ollama** | `brew install` | System binary | ❌ No | ❌ No |

## Recommended Choice by Use Case

### For Python-Only Stack (Your Question!) ⭐
```bash
# Use VLLM - it's a Python package!
uv add vllm

# Add to pyproject.toml optional dependencies
[project.optional-dependencies]
vlm = ["vllm>=0.5.0"]

# Install
uv sync --extra vlm
```

### For Development/Testing
```bash
# Use LM Studio or Ollama
# They're easier but not Python packages
brew install --cask lm-studio
# OR
brew install ollama
```

### For Production with GPU
```bash
# Use VLLM (Python package)
uv add vllm
uv run vllm serve ibm-granite/granite-docling-258M --revision untied
```

### For Production without GPU
```bash
# Deploy Ollama as a service
# It's not Python, but works well in production
docker run -d -p 11434:11434 ollama/ollama
```

## Python Environment Integration

### ✅ With VLLM (Fully Integrated)

Your `pyproject.toml`:
```toml
[project.optional-dependencies]
vlm = [
    "vllm>=0.5.0",
]
```

Your workflow:
```bash
# Install
uv sync --extra vlm

# Use in Python
import vllm

# Start server
uv run vllm serve MODEL_NAME
```

Everything is **managed by uv**! ✅

### ❌ With LM Studio/Ollama (External)

Your `pyproject.toml`:
```toml
# Nothing to add - they're not Python packages
```

Your workflow:
```bash
# Install externally
brew install --cask lm-studio

# Use as separate service
# (Not managed by uv)
```

They're **external dependencies**, like PostgreSQL or Redis.

## Making the Decision

**Question:** Do you have an NVIDIA GPU?

**Yes → Use VLLM**
```bash
uv add vllm
```
✅ Pure Python stack  
✅ Best performance  
✅ Fully integrated with `uv`

**No → Use LM Studio or Ollama**
```bash
brew install --cask lm-studio
# OR
brew install ollama
```
✅ Works without GPU  
✅ Easier setup  
❌ Not Python packages (can't use `uv add`)

## Example: Complete Python Setup with VLLM

```bash
# 1. Add VLLM to project
cd /Users/khalilfaiz/Documents/1_tests/docling_neo4j
uv add vllm

# 2. Update .env
cat >> .env << EOF
PDF_USE_VLM=true
PDF_VLM_MODEL=ibm-granite/granite-docling-258M
PDF_VLM_ENDPOINT=http://localhost:8000
PDF_VLM_PROMPT=Convert this page to docling.
EOF

# 3. Start VLLM server (terminal 1)
uv run vllm serve ibm-granite/granite-docling-258M --revision untied --port 8000

# 4. Run pipeline (terminal 2)
make run-pipeline
```

Everything is **managed by uv**! 🎉

## Summary

### Can Install with `uv`:
- ✅ **VLLM** - `uv add vllm`

### Cannot Install with `uv`:
- ❌ **LM Studio** - Desktop GUI app (like Chrome)
- ❌ **Ollama** - System binary (like Docker)

**For a pure Python/uv stack, use VLLM!** It's the only option that's a true Python package.

However, LM Studio and Ollama are still great choices if:
- You don't have an NVIDIA GPU
- You want easier setup
- You're okay with external dependencies

---

**Your Answer:** Yes, you can use `uv add vllm` for a pure Python solution! LM Studio isn't installable via `uv` because it's a desktop application, not a Python package. Use VLLM for a fully Python-managed VLM setup.

