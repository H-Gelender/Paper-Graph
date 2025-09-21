"""
MCP server implementation for the Paper-Graph system.
"""

from typing import List, Dict, Any, Optional
import asyncio
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from .agent import PaperGraphAgent
from .models import SearchRequest, TagExtractionRequest, GraphQueryRequest, TagType

# Initialize MCP server
mcp = FastMCP("paper_graph_server")

# Global agent instance
agent: Optional[PaperGraphAgent] = None


async def get_agent() -> PaperGraphAgent:
    """Get or create the global agent instance."""
    global agent
    if agent is None:
        agent = PaperGraphAgent()
    return agent


@mcp.tool()
async def search_papers(query: str, max_results: int = 10, 
                       sources: List[str] = None) -> Dict[str, Any]:
    """
    Search for academic papers and add them to the graph.
    
    Args:
        query: Search query string (e.g., 'machine learning transformers')
        max_results: Maximum number of papers to return (default: 10)
        sources: List of paper sources to search (default: ['arxiv', 'pubmed'])
    
    Returns:
        Dictionary with search results and processing summary
    """
    if sources is None:
        sources = ["arxiv", "pubmed"]
    
    agent_instance = await get_agent()
    result = await agent_instance.process_search_query(query, max_results, sources)
    return result


@mcp.tool()
async def extract_tags(paper_id: str = None, force_reextract: bool = False) -> Dict[str, Any]:
    """
    Extract tags from papers using Gemini 2.5 Flash Lite.
    
    Args:
        paper_id: Specific paper ID to extract tags for (optional - if not provided, processes all papers)
        force_reextract: Force re-extraction even if tags already exist
    
    Returns:
        Dictionary with extraction results
    """
    agent_instance = await get_agent()
    
    if paper_id:
        # Extract tags for specific paper
        success = await agent_instance.extract_tags_for_paper(paper_id, force_reextract)
        return {
            "paper_id": paper_id,
            "success": success,
            "message": "Tag extraction completed" if success else "Tag extraction failed"
        }
    else:
        # Extract tags for all papers
        results = await agent_instance.extract_tags_for_all_papers(force_reextract)
        successful = sum(results.values())
        total = len(results)
        
        return {
            "total_papers": total,
            "successful_extractions": successful,
            "failed_extractions": total - successful,
            "results": results,
            "message": f"Processed {total} papers, {successful} successful extractions"
        }


@mcp.tool()
async def query_graph(tag_filter: List[str] = None, 
                     tag_type_filter: List[str] = None,
                     source_filter: List[str] = None,
                     limit: int = 50) -> List[Dict[str, Any]]:
    """
    Query papers in the graph based on various filters.
    
    Args:
        tag_filter: Filter by specific tag names
        tag_type_filter: Filter by tag types (methodology, domain, technique, etc.)
        source_filter: Filter by paper sources (arxiv, pubmed, etc.)
        limit: Maximum number of papers to return
    
    Returns:
        List of paper dictionaries matching the filters
    """
    agent_instance = await get_agent()
    
    # Convert string tag types to TagType enums
    tag_types = None
    if tag_type_filter:
        tag_types = []
        for tag_type_str in tag_type_filter:
            try:
                tag_types.append(TagType(tag_type_str.lower()))
            except ValueError:
                pass  # Skip invalid tag types
    
    # Create query request
    query_request = GraphQueryRequest(
        tag_filter=tag_filter,
        tag_type_filter=tag_types,
        source_filter=source_filter
    )
    
    # Query papers
    papers = agent_instance.graph.query_papers(query_request)
    
    # Limit results and convert to dictionaries
    limited_papers = papers[:limit]
    return [paper.to_dict() for paper in limited_papers]


@mcp.tool()
async def get_paper_details(paper_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific paper.
    
    Args:
        paper_id: The unique identifier of the paper
    
    Returns:
        Dictionary with paper details including tags
    """
    agent_instance = await get_agent()
    paper = agent_instance.graph.get_paper(paper_id)
    
    if not paper:
        return {"error": f"Paper with ID '{paper_id}' not found"}
    
    paper_dict = paper.to_dict()
    
    # Add similar papers
    similar_papers = agent_instance.graph.get_similar_papers(paper_id, limit=5)
    paper_dict["similar_papers"] = [
        {
            "paper_id": sim_id,
            "shared_tags": shared_count,
            "title": agent_instance.graph.get_paper(sim_id).title if agent_instance.graph.get_paper(sim_id) else "Unknown"
        }
        for sim_id, shared_count in similar_papers
    ]
    
    return paper_dict


@mcp.tool()
async def get_graph_statistics() -> Dict[str, Any]:
    """
    Get comprehensive statistics about the current graph state.
    
    Returns:
        Dictionary with various graph statistics and metrics
    """
    agent_instance = await get_agent()
    return agent_instance.get_graph_summary()


@mcp.tool()
async def get_papers_by_tag(tag_name: str) -> List[Dict[str, Any]]:
    """
    Get all papers that have a specific tag.
    
    Args:
        tag_name: The name of the tag to search for
    
    Returns:
        List of paper dictionaries that have the specified tag
    """
    agent_instance = await get_agent()
    papers = agent_instance.graph.get_papers_by_tag(tag_name)
    return [paper.to_dict() for paper in papers]


@mcp.tool()
async def get_papers_by_tag_type(tag_type: str) -> List[Dict[str, Any]]:
    """
    Get all papers that have tags of a specific type.
    
    Args:
        tag_type: The type of tag to search for (methodology, domain, technique, etc.)
    
    Returns:
        List of paper dictionaries that have tags of the specified type
    """
    agent_instance = await get_agent()
    
    try:
        tag_type_enum = TagType(tag_type.lower())
        papers = agent_instance.graph.get_papers_by_type(tag_type_enum)
        return [paper.to_dict() for paper in papers]
    except ValueError:
        return {"error": f"Invalid tag type: {tag_type}. Valid types: {[t.value for t in TagType]}"}


@mcp.tool()
async def export_graph(filepath: str, format: str = "json") -> Dict[str, str]:
    """
    Export the current graph to a file.
    
    Args:
        filepath: Path where to save the graph file
        format: Export format ('json', 'gexf', 'graphml')
    
    Returns:
        Dictionary with export status
    """
    agent_instance = await get_agent()
    
    try:
        agent_instance.export_graph(filepath, format)
        return {
            "status": "success",
            "message": f"Graph exported to {filepath} in {format} format",
            "filepath": filepath
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to export graph: {str(e)}"
        }


@mcp.tool()
async def import_graph(filepath: str, format: str = "json") -> Dict[str, str]:
    """
    Import a graph from a file.
    
    Args:
        filepath: Path to the graph file to import
        format: Import format ('json', 'gexf', 'graphml')
    
    Returns:
        Dictionary with import status
    """
    agent_instance = await get_agent()
    
    try:
        if not Path(filepath).exists():
            return {
                "status": "error",
                "message": f"File {filepath} does not exist"
            }
        
        agent_instance.import_graph(filepath, format)
        stats = agent_instance.get_graph_summary()
        
        return {
            "status": "success",
            "message": f"Graph imported from {filepath}",
            "papers_imported": stats["total_papers"]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to import graph: {str(e)}"
        }


@mcp.tool()
async def build_relationships(min_shared_tags: int = 1) -> Dict[str, Any]:
    """
    Build or rebuild relationships between papers based on shared tags.
    
    Args:
        min_shared_tags: Minimum number of shared tags required to create an edge
    
    Returns:
        Dictionary with relationship building results
    """
    agent_instance = await get_agent()
    
    # Build relationships
    agent_instance.graph.build_tag_relationships(min_shared_tags)
    
    # Get graph metrics
    metrics = agent_instance.graph.get_graph_metrics()
    
    return {
        "message": "Relationships rebuilt successfully",
        "min_shared_tags": min_shared_tags,
        "graph_metrics": metrics
    }


@mcp.tool()
async def get_similar_papers(paper_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get papers similar to a given paper based on shared tags.
    
    Args:
        paper_id: The ID of the paper to find similar papers for
        limit: Maximum number of similar papers to return
    
    Returns:
        List of similar papers with similarity scores
    """
    agent_instance = await get_agent()
    
    if not agent_instance.graph.get_paper(paper_id):
        return {"error": f"Paper with ID '{paper_id}' not found"}
    
    similar_papers = agent_instance.graph.get_similar_papers(paper_id, limit)
    
    result = []
    for sim_id, shared_count in similar_papers:
        sim_paper = agent_instance.graph.get_paper(sim_id)
        if sim_paper:
            result.append({
                "paper_id": sim_id,
                "title": sim_paper.title,
                "shared_tags_count": shared_count,
                "authors": sim_paper.authors,
                "source": sim_paper.source,
                "url": sim_paper.url
            })
    
    return result


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()