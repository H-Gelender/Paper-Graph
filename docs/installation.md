# Installation Guide

This guide will walk you through setting up Paper-Graph for different use cases.

## Quick Setup (Core Functionality Only)

For basic graph operations without AI features:

```bash
# Clone repository
git clone https://github.com/H-Gelender/Paper-Graph.git
cd Paper-Graph

# Install core dependencies
pip install pydantic networkx

# Test installation
python example.py
```

## Full Installation (All Features)

For complete functionality including AI tag extraction and paper search:

### 1. Install Python Dependencies

```bash
# Option A: Using pip
pip install -e .

# Option B: Using uv (recommended)
uv add -e .

# Option C: Install from requirements (step by step)
pip install pydantic>=2.0.0 networkx>=3.0
pip install google-generativeai>=0.8.0
pip install paper-search-mcp>=0.1.3
pip install mcp[cli]>=1.6.0 fastmcp
pip install python-dotenv>=1.0.0 rich>=13.0.0 typer>=0.12.0
```

### 2. Get API Keys

#### Gemini API Key (Required for tag extraction)
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Copy the key for configuration

#### Semantic Scholar API Key (Optional)
1. Go to [Semantic Scholar API](https://www.semanticscholar.org/product/api)
2. Register for an account
3. Request an API key

### 3. Configuration

Create configuration file:
```bash
paper-graph config --init
```

Edit the generated `.env` file:
```bash
# Required for tag extraction
GEMINI_API_KEY=your-gemini-api-key-here

# Optional for enhanced paper search
SEMANTIC_SCHOLAR_API_KEY=your-semantic-scholar-key

# Optional: Customize settings
DEFAULT_SOURCES=arxiv,pubmed,biorxiv
MAX_RESULTS_PER_SEARCH=20
```

### 4. Verify Installation

```bash
# Test core functionality
python example.py

# Test CLI
paper-graph stats

# Test search (requires API keys)
paper-graph search "machine learning" --max-results 5
```

## Development Setup

For contributors:

```bash
# Clone and setup
git clone https://github.com/H-Gelender/Paper-Graph.git
cd Paper-Graph

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install

# Run tests
pytest tests/ -v

# Format code
black paper_graph/ tests/
```

## Docker Setup (Optional)

Create a Dockerfile for containerized deployment:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .
RUN pip install -e .

# Set default environment
ENV PYTHONPATH=/app

# Expose port for MCP server
EXPOSE 8000

# Default command
CMD ["paper-graph", "server", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t paper-graph .
docker run -p 8000:8000 -e GEMINI_API_KEY=your-key paper-graph
```

## Claude Desktop Integration

To use Paper-Graph with Claude Desktop:

1. Install Paper-Graph with full dependencies
2. Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "paper_graph": {
      "command": "python",
      "args": ["-m", "paper_graph.server"],
      "env": {
        "GEMINI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

3. Restart Claude Desktop
4. You should see Paper-Graph tools available in the interface

## Troubleshooting

### Common Issues

1. **Import Errors**: Missing dependencies
   - Solution: Install all dependencies with `pip install -e .`

2. **API Key Errors**: Invalid or missing API keys
   - Solution: Check `.env` file and verify API keys

3. **Permission Errors**: Cannot write to cache/export directories
   - Solution: Check file permissions or change directories in config

4. **Rate Limiting**: Too many API requests
   - Solution: Increase `API_DELAY_SECONDS` in configuration

### Getting Help

1. Check the [documentation](../README.md)
2. Search [existing issues](https://github.com/H-Gelender/Paper-Graph/issues)
3. Create a [new issue](https://github.com/H-Gelender/Paper-Graph/issues/new) with:
   - Your Python version
   - Installation method
   - Full error message
   - Steps to reproduce