"""
Example usage of Paper-Graph core functionality.
This example demonstrates the basic graph operations without requiring API keys.
"""

from paper_graph.models import PaperNode, GraphTag, TagType
from paper_graph.graph import PaperGraph
from datetime import datetime


def create_sample_papers():
    """Create some sample papers for demonstration."""
    
    # Paper 1: Deep Learning paper
    paper1 = PaperNode(
        paper_id="sample-001",
        title="Deep Learning for Natural Language Processing",
        authors=["John Smith", "Jane Doe"],
        abstract="This paper presents a comprehensive overview of deep learning techniques applied to natural language processing tasks.",
        source="example",
        published_date=datetime(2023, 1, 15)
    )
    
    # Add tags to paper 1
    paper1.add_tag(GraphTag(name="deep learning", tag_type=TagType.METHODOLOGY, confidence=0.95))
    paper1.add_tag(GraphTag(name="natural language processing", tag_type=TagType.DOMAIN, confidence=0.9))
    paper1.add_tag(GraphTag(name="neural networks", tag_type=TagType.TECHNIQUE, confidence=0.85))
    paper1.add_tag(GraphTag(name="transformer", tag_type=TagType.TECHNIQUE, confidence=0.8))
    
    # Paper 2: Computer Vision paper
    paper2 = PaperNode(
        paper_id="sample-002",
        title="Convolutional Neural Networks for Image Classification",
        authors=["Alice Johnson", "Bob Wilson"],
        abstract="An investigation of convolutional neural network architectures for image classification tasks.",
        source="example",
        published_date=datetime(2023, 2, 20)
    )
    
    # Add tags to paper 2
    paper2.add_tag(GraphTag(name="deep learning", tag_type=TagType.METHODOLOGY, confidence=0.9))
    paper2.add_tag(GraphTag(name="computer vision", tag_type=TagType.DOMAIN, confidence=0.95))
    paper2.add_tag(GraphTag(name="convolutional neural networks", tag_type=TagType.TECHNIQUE, confidence=0.9))
    paper2.add_tag(GraphTag(name="image classification", tag_type=TagType.RESEARCH_AREA, confidence=0.85))
    
    # Paper 3: Transformer paper
    paper3 = PaperNode(
        paper_id="sample-003",
        title="Attention Is All You Need: A Survey of Transformer Architectures",
        authors=["Carol Brown", "David Lee"],
        abstract="This survey examines various transformer architectures and their applications across different domains.",
        source="example",
        published_date=datetime(2023, 3, 10)
    )
    
    # Add tags to paper 3
    paper3.add_tag(GraphTag(name="transformer", tag_type=TagType.TECHNIQUE, confidence=0.95))
    paper3.add_tag(GraphTag(name="attention mechanism", tag_type=TagType.TECHNIQUE, confidence=0.9))
    paper3.add_tag(GraphTag(name="deep learning", tag_type=TagType.METHODOLOGY, confidence=0.85))
    paper3.add_tag(GraphTag(name="natural language processing", tag_type=TagType.DOMAIN, confidence=0.8))
    
    return [paper1, paper2, paper3]


def main():
    """Demonstrate Paper-Graph functionality."""
    
    print("🔬 Paper-Graph Example")
    print("=" * 40)
    
    # Create graph
    graph = PaperGraph()
    
    # Add sample papers
    papers = create_sample_papers()
    for paper in papers:
        graph.add_paper(paper)
    
    print(f"📄 Added {len(papers)} papers to the graph")
    
    # Build relationships based on shared tags
    graph.build_tag_relationships(min_shared_tags=1)
    
    # Show statistics
    stats = graph.get_tag_statistics()
    print(f"\n📊 Graph Statistics:")
    print(f"   Total papers: {stats['total_papers']}")
    print(f"   Total tags: {stats['total_tags']}")
    print(f"   Unique tags: {stats['unique_tags']}")
    print(f"   Avg tags per paper: {stats['avg_tags_per_paper']:.1f}")
    
    # Show most common tags
    print(f"\n🏷️  Most Common Tags:")
    for tag, count in stats['most_common_tags'][:5]:
        print(f"   {tag}: {count} papers")
    
    # Show papers with "deep learning" tag
    print(f"\n🔍 Papers with 'deep learning' tag:")
    dl_papers = graph.get_papers_by_tag("deep learning")
    for paper in dl_papers:
        print(f"   • {paper.title}")
    
    # Show papers by methodology tag type
    print(f"\n🔬 Papers with methodology tags:")
    method_papers = graph.get_papers_by_type(TagType.METHODOLOGY)
    for paper in method_papers:
        method_tags = [tag.name for tag in paper.get_tags_by_type(TagType.METHODOLOGY)]
        print(f"   • {paper.title}")
        print(f"     Methodologies: {', '.join(method_tags)}")
    
    # Show similar papers
    print(f"\n🔗 Papers similar to '{papers[0].title}':")
    similar = graph.get_similar_papers(papers[0].paper_id, limit=3)
    for paper_id, shared_count in similar:
        similar_paper = graph.get_paper(paper_id)
        print(f"   • {similar_paper.title} (shared tags: {shared_count})")
    
    # Show graph metrics
    metrics = graph.get_graph_metrics()
    print(f"\n📈 Graph Metrics:")
    for metric, value in metrics.items():
        if value is not None:
            if isinstance(value, float):
                print(f"   {metric.replace('_', ' ').title()}: {value:.3f}")
            else:
                print(f"   {metric.replace('_', ' ').title()}: {value}")
    
    print(f"\n✅ Example completed successfully!")


if __name__ == "__main__":
    main()