# Paper Search MCP Server

A Model Context Protocol (MCP) server that provides comprehensive academic paper search and download capabilities across multiple scholarly platforms.

## Overview

This MCP server enables AI assistants to search, discover, and download academic papers from various academic databases and preprint servers. It acts as a unified interface to multiple academic platforms, making scholarly research more accessible to AI agents.

## Features

### 🔍 Multi-Platform Search
- **arXiv**: Preprint server for physics, mathematics, computer science, and more
- **PubMed**: Biomedical and life sciences literature database
- **bioRxiv**: Preprint server for biology
- **medRxiv**: Preprint server for health sciences
- **Google Scholar**: Comprehensive academic search engine
- **Semantic Scholar**: AI-powered academic search with citations and metrics
- **IACR ePrint Archive**: Cryptology research papers
- **CrossRef**: DOI-based academic metadata search

### 📄 Paper Operations
- Search papers by keywords, authors, titles, and topics
- Download full-text PDFs when available
- Retrieve detailed paper metadata including abstracts, authors, publication dates
- Access citation information and metrics
- Get paper recommendations and related works

### 🎯 Advanced Search Capabilities
- Filter by publication date ranges
- Search within specific academic disciplines
- Sort results by relevance, date, or citation count
- Handle complex queries with boolean operators
- Support for DOI and paper ID lookups

## Available Tools

### Search Tools

#### `search_arxiv`
Search arXiv preprint server for papers in physics, math, CS, and related fields.

**Parameters:**
- `query` (string): Search terms, keywords, or paper title
- `max_results` (integer, optional): Maximum number of results (default: 10)
- `sort_by` (string, optional): Sort order - "relevance", "lastUpdatedDate", "submittedDate"

#### `search_pubmed`
Search PubMed database for biomedical and life sciences literature.

**Parameters:**
- `query` (string): Medical subject headings, keywords, or author names
- `max_results` (integer, optional): Maximum number of results (default: 10)
- `sort` (string, optional): Sort order - "relevance", "date", "author"

#### `search_biorxiv`
Search bioRxiv for biology preprints.

**Parameters:**
- `query` (string): Search terms related to biological research
- `max_results` (integer, optional): Maximum number of results (default: 10)

#### `search_medrxiv`
Search medRxiv for health sciences preprints.

**Parameters:**
- `query` (string): Health and medical research terms
- `max_results` (integer, optional): Maximum number of results (default: 10)

#### `search_google_scholar`
Search Google Scholar for academic papers across all disciplines.

**Parameters:**
- `query` (string): Academic search terms, author names, or paper titles
- `max_results` (integer, optional): Maximum number of results (default: 10)
- `year_low` (integer, optional): Earliest publication year
- `year_high` (integer, optional): Latest publication year

#### `search_semantic_scholar`
Search Semantic Scholar with AI-powered academic search.

**Parameters:**
- `query` (string): Research topics, paper titles, or semantic concepts
- `max_results` (integer, optional): Maximum number of results (default: 10)
- `fields` (array, optional): Metadata fields to include in results

#### `search_iacr`
Search IACR ePrint Archive for cryptology research.

**Parameters:**
- `query` (string): Cryptography and security research terms
- `max_results` (integer, optional): Maximum number of results (default: 10)

#### `search_crossref`
Search CrossRef database using DOI and metadata.

**Parameters:**
- `query` (string): DOI, title, or bibliographic information
- `max_results` (integer, optional): Maximum number of results (default: 10)

### Download Tools

#### `download_paper`
Download full-text PDF of a paper when available.

**Parameters:**
- `paper_id` (string): Unique identifier for the paper (arXiv ID, DOI, etc.)
- `source` (string): Source platform ("arxiv", "pubmed", "biorxiv", etc.)
- `filename` (string, optional): Custom filename for the downloaded PDF

#### `get_paper_metadata`
Retrieve detailed metadata for a specific paper.

**Parameters:**
- `paper_id` (string): Unique identifier for the paper
- `source` (string): Source platform where the paper is hosted

## Installation

### Via Smithery (Recommended)
```bash
npx @smithery/cli install paper-search-mcp --client claude
```

### Manual Installation
1. Clone the repository:
```bash
git clone https://github.com/your-username/paper-search-mcp.git
cd paper-search-mcp
```

2. Install dependencies:
```bash
uv sync
```

3. Run the server:
```bash
uv run paper_search_mcp
```

## Configuration

### Claude Desktop
Add the server to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "paper-search": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/paper-search-mcp",
        "run",
        "paper_search_mcp"
      ]
    }
  }
}
```

### Environment Variables
Some platforms may require API keys for enhanced access:

```bash
# Optional: For enhanced Google Scholar access
export GOOGLE_SCHOLAR_API_KEY="your-api-key"

# Optional: For Semantic Scholar API
export SEMANTIC_SCHOLAR_API_KEY="your-api-key"
```

## Usage Examples

### Basic Paper Search
```
Search for recent papers on "machine learning transformers" from arXiv
```

### Targeted Research
```
Find biomedical papers about "CRISPR gene editing" published after 2020 in PubMed
```

### Cross-Platform Discovery
```
Search for papers by "Geoffrey Hinton" across all available academic platforms
```

### Paper Download
```
Download the full PDF of arXiv paper "2017.10002v1"
```

### Metadata Retrieval
```
Get detailed citation information and abstract for DOI "10.1038/nature12373"
```

## Data Format

All search results return standardized `Paper` objects with the following structure:

```json
{
  "paper_id": "unique-identifier",
  "title": "Paper Title",
  "authors": ["Author 1", "Author 2"],
  "abstract": "Paper abstract text...",
  "published_date": "2024-01-15",
  "doi": "10.1000/journal.doi",
  "url": "https://platform.com/paper-url",
  "source": "arxiv",
  "categories": ["cs.AI", "cs.LG"],
  "citation_count": 42,
  "venue": "Conference/Journal Name",
  "pdf_url": "https://platform.com/pdf-url"
}
```

## Supported Platforms

| Platform | Search | Download | Metadata | API Required |
|----------|--------|----------|----------|--------------|
| arXiv | ✅ | ✅ | ✅ | No |
| PubMed | ✅ | ⚠️ | ✅ | No |
| bioRxiv | ✅ | ✅ | ✅ | No |
| medRxiv | ✅ | ✅ | ✅ | No |
| Google Scholar | ✅ | ❌ | ✅ | Optional |
| Semantic Scholar | ✅ | ⚠️ | ✅ | Optional |
| IACR ePrint | ✅ | ✅ | ✅ | No |
| CrossRef | ✅ | ❌ | ✅ | No |

**Legend:**
- ✅ Fully supported
- ⚠️ Limited availability (depends on publisher)
- ❌ Not available

## Technical Details

### Architecture
- **FastMCP Framework**: Built on the FastMCP Python SDK for MCP server development
- **Async Operations**: All search and download operations are asynchronous for better performance
- **Error Handling**: Comprehensive error handling with graceful fallbacks
- **Rate Limiting**: Respects platform rate limits and implements backoff strategies

### Dependencies
- `fastmcp`: MCP server framework
- `httpx`: Async HTTP client for API requests
- `beautifulsoup4`: HTML parsing for web scraping
- `requests`: HTTP library for file downloads

### Platform Integration
Each academic platform is implemented as a separate searcher class with standardized interfaces:
- `ArxivSearcher`: arXiv API integration
- `PubmedSearcher`: PubMed E-utilities API
- `BiorxivSearcher`: bioRxiv API and web scraping
- `GoogleScholarSearcher`: Google Scholar web scraping
- `SemanticScholarSearcher`: Semantic Scholar API
- And more...

## Contributing

We welcome contributions to expand platform support and improve functionality:

1. **Adding New Platforms**: Implement new searcher classes following the existing patterns
2. **Feature Enhancements**: Improve search capabilities, metadata extraction, or download options
3. **Bug Fixes**: Report and fix issues with existing platform integrations
4. **Documentation**: Improve documentation and usage examples

### Development Setup
```bash
# Clone and setup
git clone https://github.com/your-username/paper-search-mcp.git
cd paper-search-mcp
uv sync

# Run tests
uv run pytest

# Format code
uv run ruff format
uv run ruff check
```

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Model Context Protocol

This server implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), an open standard for connecting AI applications to external data sources and tools. MCP enables:

- **Standardized Integration**: Consistent interface across different AI applications
- **Secure Access**: Controlled access to external resources with proper authentication
- **Extensible Architecture**: Easy to add new platforms and capabilities
- **Tool Composability**: Combine with other MCP servers for enhanced functionality

## Related Projects

- [Model Context Protocol](https://modelcontextprotocol.io/) - Official MCP documentation
- [FastMCP](https://github.com/punkpeye/fastmcp) - Python framework for building MCP servers
- [Claude Desktop](https://claude.ai/desktop) - AI assistant with MCP support
- [MCP Servers](https://github.com/modelcontextprotocol/servers) - Official MCP server implementations

---

*This MCP server makes academic research more accessible to AI assistants, enabling them to discover, analyze, and retrieve scholarly literature across multiple platforms with a unified interface.*