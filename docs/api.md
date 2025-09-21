# API Reference

## Core Classes

### PaperNode

Represents a scientific paper in the graph.

```python
from paper_graph.models import PaperNode

paper = PaperNode(
    paper_id="unique-id",
    title="Paper Title",
    source="arxiv"
)
```

**Attributes:**
- `paper_id: str` - Unique identifier
- `title: str` - Paper title  
- `authors: List[str]` - Author names
- `abstract: str` - Paper abstract
- `doi: str` - Digital Object Identifier
- `published_date: Optional[datetime]` - Publication date
- `pdf_url: str` - PDF download URL
- `url: str` - Paper page URL
- `source: str` - Source platform (arxiv, pubmed, etc.)
- `tags: List[GraphTag]` - Extracted tags
- `processing_status: str` - Processing status
- `categories: List[str]` - Paper categories
- `keywords: List[str]` - Original keywords
- `citations: int` - Citation count

**Methods:**
- `add_tag(tag: GraphTag)` - Add a tag
- `get_tags_by_type(tag_type: TagType)` - Get tags of specific type
- `get_tag_names()` - Get all tag names
- `to_dict()` - Convert to dictionary

### GraphTag

Represents a tag extracted from a paper.

```python
from paper_graph.models import GraphTag, TagType

tag = GraphTag(
    name="machine learning",
    tag_type=TagType.METHODOLOGY,
    confidence=0.9
)
```

**Attributes:**
- `name: str` - Tag name
- `tag_type: TagType` - Tag category
- `confidence: float` - Confidence score (0.0-1.0)
- `context: Optional[str]` - Context where found

### TagType

Enumeration of tag categories.

```python
from paper_graph.models import TagType

# Available types:
TagType.METHODOLOGY      # Research methods, approaches
TagType.DOMAIN          # Field of study
TagType.TECHNIQUE       # Algorithms, models
TagType.DATASET         # Named datasets
TagType.METRIC          # Evaluation metrics
TagType.RESEARCH_AREA   # Research areas
TagType.KEYWORD         # Important keywords
TagType.CONCEPT         # Theoretical concepts
```

### PaperGraph

Manages the graph structure and relationships.

```python
from paper_graph.graph import PaperGraph

graph = PaperGraph()
graph.add_paper(paper)
graph.build_tag_relationships()
```

**Methods:**

#### Paper Management
- `add_paper(paper: PaperNode)` - Add paper to graph
- `get_paper(paper_id: str)` - Get paper by ID
- `remove_paper(paper_id: str)` - Remove paper
- `update_paper_tags(paper_id: str, new_tags: List[GraphTag])` - Update tags

#### Graph Operations
- `build_tag_relationships(min_shared_tags: int = 1)` - Build edges
- `get_similar_papers(paper_id: str, limit: int = 10)` - Find similar papers
- `get_connected_components()` - Get graph components
- `get_graph_metrics()` - Get graph statistics

#### Querying
- `query_papers(request: GraphQueryRequest)` - Query with filters
- `get_papers_by_tag(tag_name: str)` - Papers with specific tag
- `get_papers_by_type(tag_type: TagType)` - Papers with tag type
- `get_tag_statistics()` - Tag usage statistics

#### Import/Export
- `export_graph(filepath: Path, format: str)` - Export graph
- `import_graph(filepath: Path, format: str)` - Import graph

## Agent Classes

### PaperGraphAgent

Main agent coordinating all functionality.

```python
from paper_graph.agent import PaperGraphAgent

agent = PaperGraphAgent(gemini_api_key="your-key")
```

**Methods:**

#### Search and Processing
```python
# Search for papers and add to graph
result = await agent.process_search_query(
    query="machine learning",
    max_results=10,
    sources=["arxiv", "pubmed"]
)

# Add papers from search results
papers = await agent.search_and_add_papers(search_request)
```

#### Tag Extraction
```python
# Extract tags for specific paper
success = await agent.extract_tags_for_paper(paper_id)

# Extract tags for all papers
results = await agent.extract_tags_for_all_papers()
```

#### Analysis
```python
# Get graph summary
summary = agent.get_graph_summary()

# Export/import
agent.export_graph("graph.json")
agent.import_graph("graph.json")
```

### GeminiTagExtractor

Handles AI-powered tag extraction.

```python
from paper_graph.agent import GeminiTagExtractor

extractor = GeminiTagExtractor(api_key="your-key")
tags = await extractor.extract_tags(paper)
```

### PaperSearchInterface

Interface to paper-search-mcp functionality.

```python
from paper_graph.agent import PaperSearchInterface

searcher = PaperSearchInterface()
papers = searcher.search_papers(search_request)
```

## Request/Response Models

### SearchRequest

```python
from paper_graph.models import SearchRequest

request = SearchRequest(
    query="transformer neural networks",
    max_results=20,
    sources=["arxiv", "pubmed"]
)
```

### GraphQueryRequest

```python
from paper_graph.models import GraphQueryRequest

query = GraphQueryRequest(
    tag_filter=["deep learning", "transformer"],
    tag_type_filter=[TagType.METHODOLOGY],
    source_filter=["arxiv"]
)
```

## MCP Tools

When running as MCP server, these tools are available:

### search_papers
Search for papers and add to graph.
```python
result = await search_papers(
    query="machine learning",
    max_results=10,
    sources=["arxiv", "pubmed"]
)
```

### extract_tags
Extract tags using AI.
```python
# For all papers
result = await extract_tags()

# For specific paper
result = await extract_tags(
    paper_id="arxiv:2301.12345",
    force_reextract=False
)
```

### query_graph
Query papers with filters.
```python
papers = await query_graph(
    tag_filter=["transformer"],
    tag_type_filter=["methodology"],
    limit=50
)
```

### get_paper_details
Get detailed paper information.
```python
details = await get_paper_details(paper_id="arxiv:2301.12345")
```

### get_graph_statistics
Get comprehensive graph statistics.
```python
stats = await get_graph_statistics()
```

### get_papers_by_tag
Find papers with specific tag.
```python
papers = await get_papers_by_tag(tag_name="transformer")
```

### get_similar_papers
Find similar papers.
```python
similar = await get_similar_papers(
    paper_id="arxiv:2301.12345",
    limit=10
)
```

### export_graph / import_graph
Save/load graph data.
```python
# Export
result = await export_graph(
    filepath="my_graph.json",
    format="json"
)

# Import
result = await import_graph(
    filepath="my_graph.json",
    format="json"
)
```

### build_relationships
Rebuild graph relationships.
```python
result = await build_relationships(min_shared_tags=2)
```

## Configuration

### Config Class

```python
from paper_graph.config import Config

# Load from environment
config = Config.load_from_env()

# Validate API keys
status = config.validate_api_keys()

# Create directories
config.create_directories()
```

**Configuration Options:**
- `gemini_api_key: str` - Gemini API key
- `semantic_scholar_api_key: str` - Semantic Scholar key
- `default_sources: List[str]` - Default paper sources
- `max_results_per_search: int` - Max results per search
- `tag_extraction_temperature: float` - AI creativity level
- `max_tags_per_paper: int` - Max tags to extract
- `min_tag_confidence: float` - Minimum tag confidence
- `min_shared_tags_for_edge: int` - Edge creation threshold
- `auto_build_relationships: bool` - Auto-build graph edges
- `default_export_path: str` - Export directory
- `cache_directory: str` - Cache location
- `api_delay_seconds: float` - Rate limiting delay
- `max_concurrent_requests: int` - Concurrent request limit

## Error Handling

### Common Exceptions

```python
from paper_graph.models import PaperNode

try:
    paper = PaperNode(paper_id="test", title="", source="test")
except ValueError as e:
    print(f"Validation error: {e}")

try:
    from paper_graph.agent import PaperGraphAgent
    agent = PaperGraphAgent()  # No API key
except ValueError as e:
    print(f"Missing API key: {e}")
```

### Graceful Degradation

The package is designed to work with missing dependencies:

- Core functionality (models, graph) works without external APIs
- Agent features require API keys but fail gracefully
- Config and CLI require additional packages but are optional

## Examples

See the [main README](../README.md) for complete usage examples.