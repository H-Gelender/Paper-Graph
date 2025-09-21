"""
Graph structure management for the Paper-Graph system.
"""

import networkx as nx
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime
import json
from pathlib import Path

from .models import PaperNode, GraphTag, TagType, GraphQueryRequest


class PaperGraph:
    """
    Manages the graph structure of papers and their relationships.
    
    Papers are nodes, and edges represent relationships based on shared tags,
    citations, or other criteria.
    """

    def __init__(self):
        """Initialize an empty paper graph."""
        self.graph = nx.Graph()
        self._paper_nodes: Dict[str, PaperNode] = {}
        self._tag_index: Dict[str, Set[str]] = {}  # tag_name -> set of paper_ids
        self._type_index: Dict[TagType, Set[str]] = {}  # tag_type -> set of paper_ids

    def add_paper(self, paper: PaperNode) -> None:
        """Add a paper node to the graph."""
        self._paper_nodes[paper.paper_id] = paper
        self.graph.add_node(paper.paper_id, **paper.to_dict())
        self._update_indices(paper)

    def get_paper(self, paper_id: str) -> Optional[PaperNode]:
        """Get a paper node by ID."""
        return self._paper_nodes.get(paper_id)

    def remove_paper(self, paper_id: str) -> bool:
        """Remove a paper from the graph."""
        if paper_id not in self._paper_nodes:
            return False
        
        paper = self._paper_nodes[paper_id]
        self._remove_from_indices(paper)
        del self._paper_nodes[paper_id]
        self.graph.remove_node(paper_id)
        return True

    def update_paper_tags(self, paper_id: str, new_tags: List[GraphTag]) -> bool:
        """Update tags for a paper and rebuild relationships."""
        if paper_id not in self._paper_nodes:
            return False
        
        paper = self._paper_nodes[paper_id]
        old_tags = paper.tags.copy()
        
        # Remove old tags from indices
        self._remove_from_indices(paper)
        
        # Update paper with new tags
        paper.tags = new_tags
        paper.updated_at = datetime.now()
        
        # Update indices with new tags
        self._update_indices(paper)
        
        # Update graph node attributes
        self.graph.nodes[paper_id].update(paper.to_dict())
        
        # Rebuild edges for this paper
        self._rebuild_edges_for_paper(paper_id)
        
        return True

    def _update_indices(self, paper: PaperNode) -> None:
        """Update tag and type indices for a paper."""
        for tag in paper.tags:
            # Update tag index
            if tag.name not in self._tag_index:
                self._tag_index[tag.name] = set()
            self._tag_index[tag.name].add(paper.paper_id)
            
            # Update type index
            if tag.tag_type not in self._type_index:
                self._type_index[tag.tag_type] = set()
            self._type_index[tag.tag_type].add(paper.paper_id)

    def _remove_from_indices(self, paper: PaperNode) -> None:
        """Remove a paper from tag and type indices."""
        for tag in paper.tags:
            if tag.name in self._tag_index:
                self._tag_index[tag.name].discard(paper.paper_id)
                if not self._tag_index[tag.name]:
                    del self._tag_index[tag.name]
            
            if tag.tag_type in self._type_index:
                self._type_index[tag.tag_type].discard(paper.paper_id)
                if not self._type_index[tag.tag_type]:
                    del self._type_index[tag.tag_type]

    def build_tag_relationships(self, min_shared_tags: int = 1) -> None:
        """Build edges between papers that share tags."""
        # Clear existing edges
        self.graph.clear_edges()
        
        paper_ids = list(self._paper_nodes.keys())
        
        for i, paper_id1 in enumerate(paper_ids):
            for paper_id2 in paper_ids[i+1:]:
                shared_tags = self._get_shared_tags(paper_id1, paper_id2)
                if len(shared_tags) >= min_shared_tags:
                    self.graph.add_edge(
                        paper_id1, 
                        paper_id2, 
                        shared_tags=list(shared_tags),
                        weight=len(shared_tags)
                    )

    def _get_shared_tags(self, paper_id1: str, paper_id2: str) -> Set[str]:
        """Get shared tag names between two papers."""
        paper1 = self._paper_nodes.get(paper_id1)
        paper2 = self._paper_nodes.get(paper_id2)
        
        if not paper1 or not paper2:
            return set()
        
        tags1 = set(paper1.get_tag_names())
        tags2 = set(paper2.get_tag_names())
        
        return tags1.intersection(tags2)

    def _rebuild_edges_for_paper(self, paper_id: str) -> None:
        """Rebuild edges for a specific paper after tag updates."""
        # Remove existing edges for this paper
        edges_to_remove = list(self.graph.edges(paper_id))
        self.graph.remove_edges_from(edges_to_remove)
        
        # Add new edges based on updated tags
        for other_paper_id in self._paper_nodes:
            if other_paper_id != paper_id:
                shared_tags = self._get_shared_tags(paper_id, other_paper_id)
                if shared_tags:
                    self.graph.add_edge(
                        paper_id,
                        other_paper_id,
                        shared_tags=list(shared_tags),
                        weight=len(shared_tags)
                    )

    def query_papers(self, request: GraphQueryRequest) -> List[PaperNode]:
        """Query papers based on various filters."""
        candidate_paper_ids = set(self._paper_nodes.keys())
        
        # Filter by tags
        if request.tag_filter:
            tag_matches = set()
            for tag_name in request.tag_filter:
                if tag_name in self._tag_index:
                    tag_matches.update(self._tag_index[tag_name])
            candidate_paper_ids &= tag_matches
        
        # Filter by tag types
        if request.tag_type_filter:
            type_matches = set()
            for tag_type in request.tag_type_filter:
                if tag_type in self._type_index:
                    type_matches.update(self._type_index[tag_type])
            candidate_paper_ids &= type_matches
        
        # Filter by source
        if request.source_filter:
            source_matches = {
                pid for pid, paper in self._paper_nodes.items()
                if paper.source in request.source_filter
            }
            candidate_paper_ids &= source_matches
        
        # Filter by date range
        if request.date_from or request.date_to:
            date_matches = set()
            for pid, paper in self._paper_nodes.items():
                if paper.published_date:
                    if request.date_from and paper.published_date < request.date_from:
                        continue
                    if request.date_to and paper.published_date > request.date_to:
                        continue
                    date_matches.add(pid)
            candidate_paper_ids &= date_matches
        
        return [self._paper_nodes[pid] for pid in candidate_paper_ids]

    def get_papers_by_tag(self, tag_name: str) -> List[PaperNode]:
        """Get all papers that have a specific tag."""
        if tag_name not in self._tag_index:
            return []
        return [self._paper_nodes[pid] for pid in self._tag_index[tag_name]]

    def get_papers_by_type(self, tag_type: TagType) -> List[PaperNode]:
        """Get all papers that have tags of a specific type."""
        if tag_type not in self._type_index:
            return []
        return [self._paper_nodes[pid] for pid in self._type_index[tag_type]]

    def get_similar_papers(self, paper_id: str, limit: int = 10) -> List[Tuple[str, int]]:
        """Get papers similar to the given paper based on shared tags."""
        if paper_id not in self.graph:
            return []
        
        # Get neighbors sorted by edge weight (number of shared tags)
        neighbors = []
        for neighbor in self.graph.neighbors(paper_id):
            weight = self.graph[paper_id][neighbor].get('weight', 0)
            neighbors.append((neighbor, weight))
        
        # Sort by weight (descending) and limit results
        neighbors.sort(key=lambda x: x[1], reverse=True)
        return neighbors[:limit]

    def get_tag_statistics(self) -> Dict[str, Any]:
        """Get statistics about tags in the graph."""
        total_papers = len(self._paper_nodes)
        total_tags = sum(len(paper.tags) for paper in self._paper_nodes.values())
        unique_tags = len(self._tag_index)
        
        # Tag frequency distribution
        tag_counts = {tag: len(papers) for tag, papers in self._tag_index.items()}
        
        # Tag type distribution
        type_counts = {}
        for tag_type, papers in self._type_index.items():
            type_counts[tag_type.value] = len(papers)
        
        return {
            "total_papers": total_papers,
            "total_tags": total_tags,
            "unique_tags": unique_tags,
            "avg_tags_per_paper": total_tags / total_papers if total_papers > 0 else 0,
            "tag_frequency": tag_counts,
            "tag_type_distribution": type_counts,
            "most_common_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        }

    def export_graph(self, filepath: Path, format: str = "json") -> None:
        """Export the graph to a file."""
        if format == "json":
            data = {
                "papers": {pid: paper.to_dict() for pid, paper in self._paper_nodes.items()},
                "edges": [
                    {
                        "source": u,
                        "target": v,
                        "shared_tags": data.get("shared_tags", []),
                        "weight": data.get("weight", 0)
                    }
                    for u, v, data in self.graph.edges(data=True)
                ]
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        
        elif format == "gexf":
            nx.write_gexf(self.graph, filepath)
        
        elif format == "graphml":
            nx.write_graphml(self.graph, filepath)
        
        else:
            raise ValueError(f"Unsupported format: {format}")

    def import_graph(self, filepath: Path, format: str = "json") -> None:
        """Import a graph from a file."""
        if format == "json":
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Clear existing graph
            self.graph.clear()
            self._paper_nodes.clear()
            self._tag_index.clear()
            self._type_index.clear()
            
            # Import papers
            for paper_data in data["papers"].values():
                # Convert datetime strings back to datetime objects
                if paper_data.get("published_date"):
                    paper_data["published_date"] = datetime.fromisoformat(paper_data["published_date"])
                if paper_data.get("created_at"):
                    paper_data["created_at"] = datetime.fromisoformat(paper_data["created_at"])
                if paper_data.get("updated_at"):
                    paper_data["updated_at"] = datetime.fromisoformat(paper_data["updated_at"])
                
                # Convert tags back to GraphTag objects
                tags = []
                for tag_data in paper_data.get("tags", []):
                    tags.append(GraphTag(**tag_data))
                paper_data["tags"] = tags
                
                paper = PaperNode(**paper_data)
                self.add_paper(paper)
            
            # Import edges
            for edge_data in data["edges"]:
                self.graph.add_edge(
                    edge_data["source"],
                    edge_data["target"],
                    shared_tags=edge_data["shared_tags"],
                    weight=edge_data["weight"]
                )
        
        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_connected_components(self) -> List[List[str]]:
        """Get connected components in the graph."""
        return [list(component) for component in nx.connected_components(self.graph)]

    def get_graph_metrics(self) -> Dict[str, Any]:
        """Get various graph metrics."""
        if not self.graph.nodes():
            return {}
        
        return {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "num_connected_components": nx.number_connected_components(self.graph),
            "average_clustering": nx.average_clustering(self.graph),
            "diameter": nx.diameter(self.graph) if nx.is_connected(self.graph) else None,
        }