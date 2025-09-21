# Paper-Graph

A MCP (Model Context Protocol) LLM agent that creates graph structures from scientific papers using Gemini 2.5 Flash Lite for intelligent tag extraction.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg) 
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)

## Overview

Paper-Graph is an intelligent research assistant that:

1. **Searches** for scientific papers across multiple academic databases (arXiv, PubMed, bioRxiv, etc.)
2. **Extracts** meaningful tags from papers using Gemini 2.5 Flash Lite AI
3. **Creates** graph structures where papers are nodes and tags are attributes
4. **Builds** relationships between papers based on shared tags and concepts
5. **Provides** powerful querying and analysis capabilities

## Features

- 🔍 **Multi-source Paper Search**: Integration with [paper-search-mcp](https://github.com/openags/paper-search-mcp) for comprehensive paper discovery
- 🧠 **AI-Powered Tag Extraction**: Uses Gemini 2.5 Flash Lite to extract methodologies, domains, techniques, datasets, and more
- 📊 **Graph-Based Analysis**: NetworkX-powered graph structure for discovering paper relationships
- 🔌 **MCP Compatible**: Full Model Context Protocol support for LLM integration
- 🖥️ **Rich CLI Interface**: Beautiful command-line interface with progress bars and tables
- 📤 **Multiple Export Formats**: JSON, GEXF, GraphML support for data portability
- ⚡ **Async Processing**: Efficient async/await implementation for better performance

## Installation

### Quick Start

```bash
# Clone the repository
git clone https://github.com/H-Gelender/Paper-Graph.git
cd Paper-Graph

# Install with pip
pip install -e .

# Or install with uv (recommended)
uv add -e .
```

### Prerequisites

1. **Python 3.10+**
2. **Gemini API Key** - Get one from [Google AI Studio](https://aistudio.google.com/app/apikey)
3. **Optional**: Semantic Scholar API key for enhanced search

### Configuration

1. Initialize configuration:
```bash
paper-graph config --init
```

2. Edit the generated `.env` file:
```bash
GEMINI_API_KEY=your-gemini-api-key-here
SEMANTIC_SCHOLAR_API_KEY=your-semantic-scholar-api-key  # Optional
DEFAULT_SOURCES=arxiv,pubmed
MAX_RESULTS_PER_SEARCH=20
```

## Usage

### Command Line Interface

#### 1. Search and Process Papers

```bash
# Search for papers on a topic
paper-graph search "transformer neural networks" --max-results 10

# Search specific sources
paper-graph search "CRISPR gene editing" --source pubmed --source biorxiv

# Search without tag extraction (faster)
paper-graph search "quantum computing" --no-extract-tags
```

#### 2. Extract Tags from Papers

```bash
# Extract tags for all papers
paper-graph extract

# Extract tags for specific paper
paper-graph extract --paper-id "arxiv:2301.12345"

# Force re-extraction
paper-graph extract --force
```

#### 3. Query the Graph

```bash
# Query by tags
paper-graph query --tag "transformer" --tag "attention"

# Query by tag types
paper-graph query --type "methodology" --type "technique"

# Query by source
paper-graph query --source "arxiv" --limit 50

# Export results
paper-graph query --tag "deep learning" --output results.json
```

#### 4. View Statistics

```bash
# Show graph statistics
paper-graph stats

# Import existing graph and show stats
paper-graph stats --import my-graph.json
```

### MCP Server

Start the MCP server for integration with LLM clients:

```bash
paper-graph server --host localhost --port 8000
```

#### Claude Desktop Integration

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

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

### Programmatic Usage

```python
from paper_graph import PaperGraphAgent
import asyncio

async def main():
    # Initialize agent
    agent = PaperGraphAgent(gemini_api_key="your-key")
    
    # Search and process papers
    result = await agent.process_search_query(
        query="machine learning interpretability",
        max_results=15,
        sources=["arxiv", "pubmed"]
    )
    
    # Query papers by tags
    papers = agent.graph.get_papers_by_tag("interpretability")
    
    # Get similar papers
    similar = agent.graph.get_similar_papers("paper_id", limit=5)
    
    # Export graph
    agent.export_graph("my_research_graph.json")

# Run
asyncio.run(main())
```

## Tag Types

Paper-Graph extracts tags in the following categories:

- **METHODOLOGY**: Research methods, approaches, frameworks
- **DOMAIN**: Field of study, application domain  
- **TECHNIQUE**: Specific algorithms, models, techniques
- **DATASET**: Named datasets, data sources
- **METRIC**: Evaluation metrics, performance measures
- **RESEARCH_AREA**: Broad research areas and subfields
- **KEYWORD**: Important keywords and concepts
- **CONCEPT**: Theoretical concepts and ideas

## Graph Structure

- **Nodes**: Scientific papers with metadata and extracted tags
- **Edges**: Relationships based on shared tags (weighted by number of shared tags)
- **Attributes**: Rich metadata including authors, abstracts, publication dates, citations

## Available MCP Tools

When running as an MCP server, Paper-Graph provides these tools:

- `search_papers`: Search and add papers to the graph
- `extract_tags`: Extract tags using Gemini AI
- `query_graph`: Query papers with various filters
- `get_paper_details`: Get detailed paper information
- `get_graph_statistics`: Graph analytics and statistics
- `get_papers_by_tag`: Find papers with specific tags
- `get_similar_papers`: Find papers similar to a given paper
- `export_graph`/`import_graph`: Data persistence
- `build_relationships`: Rebuild graph relationships

## Examples

### Research Workflow Example

```bash
# 1. Research transformer architectures
paper-graph search "transformer attention mechanisms" --max-results 20

# 2. Add related work on BERT
paper-graph search "BERT language model" --max-results 15

# 3. Find papers using specific techniques
paper-graph query --tag "self-attention" --tag "multi-head attention"

# 4. Discover related methodologies
paper-graph query --type "methodology" --limit 30

# 5. Export research graph
paper-graph query --output transformer_research.json

# 6. View insights
paper-graph stats
```

### Analysis Example

```python
# Load and analyze existing research
agent = PaperGraphAgent()
agent.import_graph("transformer_research.json")

# Find most connected papers
stats = agent.graph.get_graph_metrics()
print(f"Graph density: {stats['density']}")

# Discover research clusters
components = agent.graph.get_connected_components()
print(f"Found {len(components)} research clusters")

# Find papers bridging different areas
for paper_id in agent.graph._paper_nodes:
    similar = agent.graph.get_similar_papers(paper_id, limit=10)
    if len(similar) > 5:  # Highly connected papers
        paper = agent.graph.get_paper(paper_id)
        print(f"Bridge paper: {paper.title}")
```

## Configuration Options

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| Gemini API Key | `GEMINI_API_KEY` | Required | API key for tag extraction |
| Default Sources | `DEFAULT_SOURCES` | `arxiv,pubmed` | Paper sources to search |
| Max Results | `MAX_RESULTS_PER_SEARCH` | `20` | Maximum papers per search |
| Tag Temperature | `TAG_EXTRACTION_TEMPERATURE` | `0.3` | AI creativity for tag extraction |
| API Delay | `API_DELAY_SECONDS` | `1.0` | Delay between API calls |

## Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Submit a pull request

### Development Setup

```bash
# Clone and setup
git clone https://github.com/H-Gelender/Paper-Graph.git
cd Paper-Graph

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black paper_graph/
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [paper-search-mcp](https://github.com/openags/paper-search-mcp) for paper search functionality
- [Google Gemini](https://ai.google.dev/) for AI-powered tag extraction
- [NetworkX](https://networkx.org/) for graph processing
- [Model Context Protocol](https://modelcontextprotocol.io/) for LLM integration

## Support

If you encounter issues or have questions:

1. Check the [documentation](docs/)
2. Search [existing issues](https://github.com/H-Gelender/Paper-Graph/issues)
3. Create a [new issue](https://github.com/H-Gelender/Paper-Graph/issues/new)

---

**Happy researching with Paper-Graph!** 📚🔬📊