#!/usr/bin/env python3
"""
Integration test for Paper-Graph functionality.
This script tests the core features without requiring API keys.
"""

import sys
import traceback
from datetime import datetime

def test_models():
    """Test the core models."""
    print("Testing models...")
    
    from paper_graph.models import PaperNode, GraphTag, TagType
    
    # Test tag creation
    tag = GraphTag(
        name="machine learning",
        tag_type=TagType.METHODOLOGY,
        confidence=0.9,
        context="abstract"
    )
    assert tag.name == "machine learning"
    assert tag.tag_type == TagType.METHODOLOGY
    
    # Test paper creation
    paper = PaperNode(
        paper_id="test-001",
        title="Test Paper on Machine Learning",
        authors=["John Doe", "Jane Smith"],
        abstract="This is a test paper about machine learning techniques.",
        source="test",
        published_date=datetime(2023, 1, 15)
    )
    
    # Test adding tags
    paper.add_tag(tag)
    assert len(paper.tags) == 1
    assert paper.get_tag_names() == ["machine learning"]
    
    # Test tag filtering
    methodology_tags = paper.get_tags_by_type(TagType.METHODOLOGY)
    assert len(methodology_tags) == 1
    
    # Test conversion to dict
    paper_dict = paper.to_dict()
    assert paper_dict["paper_id"] == "test-001"
    assert paper_dict["title"] == "Test Paper on Machine Learning"
    
    print("✅ Models test passed")


def test_graph():
    """Test the graph functionality."""
    print("Testing graph...")
    
    from paper_graph.models import PaperNode, GraphTag, TagType
    from paper_graph.graph import PaperGraph
    
    # Create graph
    graph = PaperGraph()
    
    # Create test papers
    paper1 = PaperNode(
        paper_id="test-001",
        title="Deep Learning Fundamentals",
        source="test"
    )
    paper1.add_tag(GraphTag(name="deep learning", tag_type=TagType.METHODOLOGY))
    paper1.add_tag(GraphTag(name="neural networks", tag_type=TagType.TECHNIQUE))
    
    paper2 = PaperNode(
        paper_id="test-002", 
        title="Machine Learning Applications",
        source="test"
    )
    paper2.add_tag(GraphTag(name="machine learning", tag_type=TagType.METHODOLOGY))
    paper2.add_tag(GraphTag(name="deep learning", tag_type=TagType.METHODOLOGY))
    
    # Add papers to graph
    graph.add_paper(paper1)
    graph.add_paper(paper2)
    
    assert len(graph._paper_nodes) == 2
    
    # Test paper retrieval
    retrieved_paper = graph.get_paper("test-001")
    assert retrieved_paper is not None
    assert retrieved_paper.title == "Deep Learning Fundamentals"
    
    # Test tag-based querying
    dl_papers = graph.get_papers_by_tag("deep learning")
    assert len(dl_papers) == 2
    
    # Test tag type querying
    method_papers = graph.get_papers_by_type(TagType.METHODOLOGY)
    assert len(method_papers) == 2
    
    # Build relationships
    graph.build_tag_relationships()
    
    # Test similarity
    similar = graph.get_similar_papers("test-001", limit=5)
    assert len(similar) == 1  # paper2 should be similar
    assert similar[0][0] == "test-002"
    assert similar[0][1] == 1  # 1 shared tag
    
    # Test statistics
    stats = graph.get_tag_statistics()
    assert stats["total_papers"] == 2
    assert stats["unique_tags"] == 3
    
    # Test graph metrics
    metrics = graph.get_graph_metrics()
    assert metrics["num_nodes"] == 2
    assert metrics["num_edges"] == 1
    
    print("✅ Graph test passed")


def test_query_functionality():
    """Test advanced querying functionality."""
    print("Testing query functionality...")
    
    from paper_graph.models import PaperNode, GraphTag, TagType, GraphQueryRequest
    from paper_graph.graph import PaperGraph
    
    # Create graph with multiple papers
    graph = PaperGraph()
    
    # Paper 1: NLP
    paper1 = PaperNode(paper_id="nlp-001", title="NLP Research", source="arxiv")
    paper1.add_tag(GraphTag(name="natural language processing", tag_type=TagType.DOMAIN))
    paper1.add_tag(GraphTag(name="transformer", tag_type=TagType.TECHNIQUE))
    paper1.add_tag(GraphTag(name="bert", tag_type=TagType.TECHNIQUE))
    
    # Paper 2: Computer Vision
    paper2 = PaperNode(paper_id="cv-001", title="Computer Vision Study", source="pubmed")
    paper2.add_tag(GraphTag(name="computer vision", tag_type=TagType.DOMAIN))
    paper2.add_tag(GraphTag(name="convolutional neural networks", tag_type=TagType.TECHNIQUE))
    
    # Paper 3: Mixed
    paper3 = PaperNode(paper_id="mixed-001", title="Multimodal Learning", source="arxiv")
    paper3.add_tag(GraphTag(name="natural language processing", tag_type=TagType.DOMAIN))
    paper3.add_tag(GraphTag(name="computer vision", tag_type=TagType.DOMAIN))
    paper3.add_tag(GraphTag(name="transformer", tag_type=TagType.TECHNIQUE))
    
    for paper in [paper1, paper2, paper3]:
        graph.add_paper(paper)
    
    # Test tag filter
    query1 = GraphQueryRequest(tag_filter=["transformer"])
    results1 = graph.query_papers(query1)
    assert len(results1) == 2  # paper1 and paper3
    
    # Test tag type filter
    query2 = GraphQueryRequest(tag_type_filter=[TagType.DOMAIN])
    results2 = graph.query_papers(query2)
    assert len(results2) == 3  # all papers have domain tags
    
    # Test source filter
    query3 = GraphQueryRequest(source_filter=["arxiv"])
    results3 = graph.query_papers(query3)
    assert len(results3) == 2  # paper1 and paper3
    
    # Test combined filters
    query4 = GraphQueryRequest(
        tag_filter=["natural language processing"],
        source_filter=["arxiv"]
    )
    results4 = graph.query_papers(query4)
    assert len(results4) == 2  # paper1 and paper3
    
    print("✅ Query functionality test passed")


def test_import_export():
    """Test graph import/export functionality."""
    print("Testing import/export...")
    
    import tempfile
    import os
    from pathlib import Path
    from paper_graph.models import PaperNode, GraphTag, TagType
    from paper_graph.graph import PaperGraph
    
    # Create a test graph
    graph1 = PaperGraph()
    
    paper = PaperNode(
        paper_id="export-test-001",
        title="Export Test Paper",
        source="test"
    )
    paper.add_tag(GraphTag(name="test tag", tag_type=TagType.KEYWORD))
    graph1.add_paper(paper)
    graph1.build_tag_relationships()
    
    # Export to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        graph1.export_graph(temp_path, format="json")
        assert temp_path.exists()
        
        # Import into new graph
        graph2 = PaperGraph()
        graph2.import_graph(temp_path, format="json")
        
        # Verify imported data
        assert len(graph2._paper_nodes) == 1
        imported_paper = graph2.get_paper("export-test-001")
        assert imported_paper is not None
        assert imported_paper.title == "Export Test Paper"
        assert len(imported_paper.tags) == 1
        assert imported_paper.tags[0].name == "test tag"
        
    finally:
        # Clean up
        if temp_path.exists():
            os.unlink(temp_path)
    
    print("✅ Import/export test passed")


def test_package_structure():
    """Test that the package structure is correct."""
    print("Testing package structure...")
    
    # Test that core modules can be imported
    from paper_graph.models import PaperNode, GraphTag, TagType
    from paper_graph.graph import PaperGraph
    
    # Test that the main package imports work
    import paper_graph
    assert hasattr(paper_graph, 'PaperNode')
    assert hasattr(paper_graph, 'GraphTag')
    assert hasattr(paper_graph, 'TagType')
    assert hasattr(paper_graph, 'PaperGraph')
    
    # Test version
    assert hasattr(paper_graph, '__version__')
    assert paper_graph.__version__ == "0.1.0"
    
    print("✅ Package structure test passed")


def run_all_tests():
    """Run all tests."""
    print("🔬 Running Paper-Graph Integration Tests")
    print("=" * 50)
    
    tests = [
        test_package_structure,
        test_models,
        test_graph,
        test_query_functionality,
        test_import_export,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            print(traceback.format_exc())
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"🏁 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Paper-Graph is working correctly.")
        return 0
    else:
        print("💥 Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)