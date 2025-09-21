"""
Data models for the Paper-Graph system.
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class TagType(str, Enum):
    """Types of tags that can be extracted from papers."""
    METHODOLOGY = "methodology"
    DOMAIN = "domain"
    TECHNIQUE = "technique"
    DATASET = "dataset"
    METRIC = "metric"
    RESEARCH_AREA = "research_area"
    KEYWORD = "keyword"
    CONCEPT = "concept"


class GraphTag(BaseModel):
    """Represents a tag extracted from a paper."""
    name: str = Field(..., description="The tag name")
    tag_type: TagType = Field(..., description="The type of tag")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score for the tag")
    context: Optional[str] = Field(default=None, description="Context where the tag was found")


class PaperNode(BaseModel):
    """Represents a paper node in the graph structure."""
    # Core paper information
    paper_id: str = Field(..., description="Unique identifier for the paper")
    title: str = Field(..., description="Title of the paper")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    abstract: str = Field(default="", description="Abstract of the paper")
    doi: str = Field(default="", description="Digital Object Identifier")
    published_date: Optional[datetime] = Field(default=None, description="Publication date")
    pdf_url: str = Field(default="", description="URL to PDF")
    url: str = Field(default="", description="URL to paper page")
    source: str = Field(..., description="Source platform (arxiv, pubmed, etc.)")
    
    # Graph-specific attributes
    tags: List[GraphTag] = Field(default_factory=list, description="Extracted tags")
    processing_status: str = Field(default="pending", description="Processing status")
    created_at: datetime = Field(default_factory=datetime.now, description="When node was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When node was last updated")
    
    # Additional metadata
    categories: List[str] = Field(default_factory=list, description="Paper categories")
    keywords: List[str] = Field(default_factory=list, description="Original keywords")
    citations: int = Field(default=0, description="Citation count")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Extra metadata")

    def add_tag(self, tag: GraphTag) -> None:
        """Add a tag to the paper node."""
        self.tags.append(tag)
        self.updated_at = datetime.now()

    def get_tags_by_type(self, tag_type: TagType) -> List[GraphTag]:
        """Get all tags of a specific type."""
        return [tag for tag in self.tags if tag.tag_type == tag_type]

    def get_tag_names(self) -> List[str]:
        """Get all tag names."""
        return [tag.name for tag in self.tags]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "doi": self.doi,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "pdf_url": self.pdf_url,
            "url": self.url,
            "source": self.source,
            "tags": [tag.model_dump() for tag in self.tags],
            "processing_status": self.processing_status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "categories": self.categories,
            "keywords": self.keywords,
            "citations": self.citations,
            "extra": self.extra
        }


class SearchRequest(BaseModel):
    """Request model for paper search."""
    query: str = Field(..., description="Search query")
    max_results: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    sources: List[str] = Field(
        default_factory=lambda: ["arxiv", "pubmed"],
        description="Paper sources to search"
    )


class TagExtractionRequest(BaseModel):
    """Request model for tag extraction."""
    paper_id: str = Field(..., description="Paper ID to extract tags from")
    force_reextract: bool = Field(default=False, description="Force re-extraction even if tags exist")


class GraphQueryRequest(BaseModel):
    """Request model for graph queries."""
    tag_filter: Optional[List[str]] = Field(default=None, description="Filter by tag names")
    tag_type_filter: Optional[List[TagType]] = Field(default=None, description="Filter by tag types")
    source_filter: Optional[List[str]] = Field(default=None, description="Filter by paper sources")
    date_from: Optional[datetime] = Field(default=None, description="Filter papers from this date")
    date_to: Optional[datetime] = Field(default=None, description="Filter papers to this date")