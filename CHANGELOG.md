# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-09-21

### Added

#### Core Features
- **Paper Graph Structure**: NetworkX-based graph system with papers as nodes and tags as attributes
- **AI-Powered Tag Extraction**: Integration with Gemini 2.5 Flash Lite for intelligent tag extraction
- **Multi-Source Paper Search**: Integration with paper-search-mcp for searching across arXiv, PubMed, bioRxiv, etc.
- **Model Context Protocol (MCP) Support**: Full MCP server implementation for LLM integration

#### Data Models
- `PaperNode`: Comprehensive paper representation with metadata and tags
- `GraphTag`: Structured tag system with types (methodology, domain, technique, etc.)
- `TagType`: Enumerated tag categories for consistent classification
- Request/response models for all API operations

#### Graph Operations
- Paper relationship building based on shared tags
- Advanced querying with multiple filter options
- Graph metrics and statistics
- Import/export in multiple formats (JSON, GEXF, GraphML)
- Similarity detection between papers

#### MCP Tools
- `search_papers`: Search and add papers to the graph
- `extract_tags`: AI-powered tag extraction
- `query_graph`: Advanced paper querying
- `get_paper_details`: Detailed paper information
- `get_graph_statistics`: Comprehensive analytics
- `get_similar_papers`: Find related papers
- `export_graph`/`import_graph`: Data persistence
- Additional utility tools for graph management

#### CLI Interface
- Rich command-line interface with progress bars and tables
- `search`: Search for papers with tag extraction
- `extract`: Extract tags from existing papers
- `query`: Query papers with various filters
- `stats`: Display graph statistics
- `config`: Configuration management
- `server`: Start MCP server

#### Configuration System
- Environment variable-based configuration
- API key management for Gemini and Semantic Scholar
- Customizable search and extraction parameters
- Rate limiting and performance tuning options

#### Documentation
- Comprehensive README with examples
- API reference documentation
- Installation guide with multiple setup options
- Integration examples for Claude Desktop

#### Testing
- Unit tests for core models and functionality
- Integration tests for complete workflows
- Graceful degradation when dependencies are missing
- Example scripts demonstrating functionality

### Technical Specifications
- **Python**: 3.10+ required
- **Dependencies**: Minimal core dependencies (pydantic, networkx)
- **Optional Features**: Require additional packages for full functionality
- **Architecture**: Modular design with clear separation of concerns
- **Error Handling**: Graceful failure modes and comprehensive error messages