"""Test models for Paper-Graph."""

import pytest
from datetime import datetime
from paper_graph.models import PaperNode, GraphTag, TagType


def test_graph_tag_creation():
    """Test GraphTag creation."""
    tag = GraphTag(
        name="deep learning",
        tag_type=TagType.METHODOLOGY,
        confidence=0.9,
        context="abstract"
    )
    assert tag.name == "deep learning"
    assert tag.tag_type == TagType.METHODOLOGY
    assert tag.confidence == 0.9
    assert tag.context == "abstract"


def test_paper_node_creation():
    """Test PaperNode creation."""
    paper = PaperNode(
        paper_id="test-001",
        title="Test Paper",
        source="test"
    )
    assert paper.paper_id == "test-001"
    assert paper.title == "Test Paper"
    assert paper.source == "test"
    assert isinstance(paper.tags, list)
    assert len(paper.tags) == 0


def test_paper_node_add_tag():
    """Test adding tags to a paper node."""
    paper = PaperNode(
        paper_id="test-001",
        title="Test Paper",
        source="test"
    )
    
    tag = GraphTag(
        name="neural networks",
        tag_type=TagType.TECHNIQUE
    )
    
    paper.add_tag(tag)
    assert len(paper.tags) == 1
    assert paper.tags[0].name == "neural networks"


def test_paper_node_get_tags_by_type():
    """Test filtering tags by type."""
    paper = PaperNode(
        paper_id="test-001",
        title="Test Paper",
        source="test"
    )
    
    tag1 = GraphTag(name="methodology1", tag_type=TagType.METHODOLOGY)
    tag2 = GraphTag(name="technique1", tag_type=TagType.TECHNIQUE)
    tag3 = GraphTag(name="methodology2", tag_type=TagType.METHODOLOGY)
    
    paper.add_tag(tag1)
    paper.add_tag(tag2)
    paper.add_tag(tag3)
    
    methodology_tags = paper.get_tags_by_type(TagType.METHODOLOGY)
    assert len(methodology_tags) == 2
    assert all(tag.tag_type == TagType.METHODOLOGY for tag in methodology_tags)


def test_paper_node_to_dict():
    """Test converting paper node to dictionary."""
    paper = PaperNode(
        paper_id="test-001",
        title="Test Paper",
        source="test",
        authors=["Author 1", "Author 2"]
    )
    
    tag = GraphTag(name="test-tag", tag_type=TagType.KEYWORD)
    paper.add_tag(tag)
    
    paper_dict = paper.to_dict()
    assert isinstance(paper_dict, dict)
    assert paper_dict["paper_id"] == "test-001"
    assert paper_dict["title"] == "Test Paper"
    assert len(paper_dict["tags"]) == 1