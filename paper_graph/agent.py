"""
Core Paper-Graph agent that integrates paper search with Gemini tag extraction.
"""

import os
import asyncio
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
import google.generativeai as genai

from .models import PaperNode, GraphTag, TagType, SearchRequest, TagExtractionRequest
from .graph import PaperGraph


class GeminiTagExtractor:
    """Handles tag extraction using Gemini 2.5 Flash Lite."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Gemini tag extractor."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        
        # Use Gemini 2.5 Flash (Lite variant is included in this model)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        self.extraction_prompt = """
You are an expert academic researcher tasked with extracting structured tags from scientific papers.

Given the following paper information, extract relevant tags categorized by type. 
Focus on the most important and specific concepts, methodologies, domains, techniques, datasets, metrics, and research areas.

Paper Title: {title}
Abstract: {abstract}
Authors: {authors}
Categories: {categories}

Extract tags in the following categories:
- METHODOLOGY: Research methods, approaches, frameworks
- DOMAIN: Field of study, application domain
- TECHNIQUE: Specific algorithms, models, techniques used
- DATASET: Named datasets, data sources mentioned
- METRIC: Evaluation metrics, performance measures
- RESEARCH_AREA: Broad research areas and subfields
- KEYWORD: Important keywords and concepts
- CONCEPT: Theoretical concepts and ideas

Return the result as a JSON object with the following structure:
{
  "tags": [
    {
      "name": "tag_name",
      "tag_type": "METHODOLOGY|DOMAIN|TECHNIQUE|DATASET|METRIC|RESEARCH_AREA|KEYWORD|CONCEPT",
      "confidence": 0.0-1.0,
      "context": "brief context where this tag was identified"
    }
  ]
}

Rules:
1. Extract 5-15 most relevant tags
2. Avoid generic terms like "machine learning" unless very specific
3. Prioritize specific techniques, methods, and domain-specific terms
4. Confidence should reflect how certain you are about the tag relevance
5. Context should be a brief phrase indicating where the tag was found
6. Tag names should be concise (1-4 words)

Respond only with the JSON object, no additional text.
"""

    async def extract_tags(self, paper: PaperNode) -> List[GraphTag]:
        """Extract tags from a paper using Gemini."""
        try:
            # Prepare the prompt with paper information
            prompt = self.extraction_prompt.format(
                title=paper.title,
                abstract=paper.abstract[:2000],  # Limit abstract length
                authors="; ".join(paper.authors[:5]),  # Limit authors
                categories="; ".join(paper.categories)
            )
            
            # Generate content using Gemini
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=1000,
                )
            )
            
            # Parse the response
            response_text = response.text.strip()
            
            # Handle potential markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
            
            # Parse JSON response
            result = json.loads(response_text)
            
            # Convert to GraphTag objects
            tags = []
            for tag_data in result.get("tags", []):
                try:
                    tag = GraphTag(
                        name=tag_data["name"],
                        tag_type=TagType(tag_data["tag_type"].lower()),
                        confidence=tag_data.get("confidence", 1.0),
                        context=tag_data.get("context", "")
                    )
                    tags.append(tag)
                except (KeyError, ValueError) as e:
                    print(f"Warning: Skipping invalid tag {tag_data}: {e}")
                    continue
            
            return tags
            
        except Exception as e:
            print(f"Error extracting tags for paper {paper.paper_id}: {e}")
            return []


class PaperSearchInterface:
    """Interface to the paper-search-mcp functionality."""
    
    def __init__(self):
        """Initialize the paper search interface."""
        # Import the paper search MCP components
        try:
            from paper_search_mcp.academic_platforms.arxiv import ArxivSearcher
            from paper_search_mcp.academic_platforms.pubmed import PubMedSearcher
            from paper_search_mcp.academic_platforms.biorxiv import BioRxivSearcher
            from paper_search_mcp.academic_platforms.semantic import SemanticSearcher
            from paper_search_mcp.paper import Paper
            
            self.searchers = {
                "arxiv": ArxivSearcher(),
                "pubmed": PubMedSearcher(),
                "biorxiv": BioRxivSearcher(),
                "semantic": SemanticSearcher(),
            }
            self.Paper = Paper
        except ImportError as e:
            raise ImportError(f"paper-search-mcp is required but not installed: {e}")

    def search_papers(self, request: SearchRequest) -> List[Dict]:
        """Search for papers using the specified sources."""
        all_papers = []
        
        for source in request.sources:
            if source not in self.searchers:
                print(f"Warning: Unknown paper source '{source}', skipping...")
                continue
            
            try:
                searcher = self.searchers[source]
                papers = searcher.search(request.query, max_results=request.max_results)
                
                # Convert Paper objects to dictionaries
                for paper in papers:
                    paper_dict = paper.to_dict()
                    paper_dict['source'] = source
                    all_papers.append(paper_dict)
                    
            except Exception as e:
                print(f"Error searching {source}: {e}")
                continue
        
        return all_papers

    def convert_to_paper_node(self, paper_dict: Dict) -> PaperNode:
        """Convert a paper dictionary to a PaperNode."""
        # Parse the published date if it's a string
        published_date = None
        if paper_dict.get('published_date'):
            try:
                if isinstance(paper_dict['published_date'], str):
                    published_date = datetime.fromisoformat(paper_dict['published_date'].replace('Z', '+00:00'))
                else:
                    published_date = paper_dict['published_date']
            except ValueError:
                pass
        
        # Parse authors if they're in string format
        authors = paper_dict.get('authors', [])
        if isinstance(authors, str):
            authors = [author.strip() for author in authors.split(';') if author.strip()]
        
        # Parse categories if they're in string format
        categories = paper_dict.get('categories', [])
        if isinstance(categories, str):
            categories = [cat.strip() for cat in categories.split(';') if cat.strip()]
        
        return PaperNode(
            paper_id=paper_dict.get('paper_id', ''),
            title=paper_dict.get('title', ''),
            authors=authors,
            abstract=paper_dict.get('abstract', ''),
            doi=paper_dict.get('doi', ''),
            published_date=published_date,
            pdf_url=paper_dict.get('pdf_url', ''),
            url=paper_dict.get('url', ''),
            source=paper_dict.get('source', 'unknown'),
            categories=categories,
            keywords=paper_dict.get('keywords', []) if isinstance(paper_dict.get('keywords'), list) else [],
            citations=paper_dict.get('citations', 0),
            extra=paper_dict.get('extra', {})
        )


class PaperGraphAgent:
    """
    Main agent that coordinates paper search, tag extraction, and graph management.
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """Initialize the Paper-Graph agent."""
        self.tag_extractor = GeminiTagExtractor(gemini_api_key)
        self.paper_search = PaperSearchInterface()
        self.graph = PaperGraph()
        
    async def search_and_add_papers(self, request: SearchRequest) -> List[PaperNode]:
        """Search for papers and add them to the graph."""
        # Search for papers
        paper_dicts = self.paper_search.search_papers(request)
        
        added_papers = []
        for paper_dict in paper_dicts:
            try:
                # Convert to PaperNode
                paper_node = self.paper_search.convert_to_paper_node(paper_dict)
                
                # Check if paper already exists
                if self.graph.get_paper(paper_node.paper_id):
                    print(f"Paper {paper_node.paper_id} already exists, skipping...")
                    continue
                
                # Add to graph
                self.graph.add_paper(paper_node)
                added_papers.append(paper_node)
                print(f"Added paper: {paper_node.title}")
                
            except Exception as e:
                print(f"Error adding paper: {e}")
                continue
        
        return added_papers

    async def extract_tags_for_paper(self, paper_id: str, force_reextract: bool = False) -> bool:
        """Extract tags for a specific paper."""
        paper = self.graph.get_paper(paper_id)
        if not paper:
            return False
        
        # Check if tags already exist and force re-extraction is not requested
        if paper.tags and not force_reextract:
            print(f"Paper {paper_id} already has tags, skipping extraction...")
            return True
        
        print(f"Extracting tags for: {paper.title}")
        
        # Extract tags using Gemini
        tags = await self.tag_extractor.extract_tags(paper)
        
        if tags:
            # Update paper with extracted tags
            self.graph.update_paper_tags(paper_id, tags)
            paper.processing_status = "completed"
            print(f"Extracted {len(tags)} tags for paper {paper_id}")
            return True
        else:
            paper.processing_status = "failed"
            print(f"Failed to extract tags for paper {paper_id}")
            return False

    async def extract_tags_for_all_papers(self, force_reextract: bool = False) -> Dict[str, bool]:
        """Extract tags for all papers in the graph."""
        results = {}
        
        papers_to_process = []
        for paper_id, paper in self.graph._paper_nodes.items():
            if not paper.tags or force_reextract:
                papers_to_process.append(paper_id)
        
        print(f"Processing {len(papers_to_process)} papers for tag extraction...")
        
        for paper_id in papers_to_process:
            success = await self.extract_tags_for_paper(paper_id, force_reextract)
            results[paper_id] = success
            
            # Add a small delay to respect API rate limits
            await asyncio.sleep(1)
        
        # Rebuild graph relationships after all tags are extracted
        self.graph.build_tag_relationships()
        
        return results

    async def process_search_query(self, query: str, max_results: int = 10, 
                                 sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """Complete workflow: search papers, extract tags, and build graph."""
        if sources is None:
            sources = ["arxiv", "pubmed"]
        
        print(f"Processing search query: '{query}'")
        
        # Step 1: Search for papers
        search_request = SearchRequest(
            query=query,
            max_results=max_results,
            sources=sources
        )
        
        added_papers = await self.search_and_add_papers(search_request)
        print(f"Added {len(added_papers)} new papers")
        
        # Step 2: Extract tags for new papers
        extraction_results = {}
        for paper in added_papers:
            success = await self.extract_tags_for_paper(paper.paper_id)
            extraction_results[paper.paper_id] = success
            await asyncio.sleep(1)  # Rate limiting
        
        # Step 3: Build graph relationships
        self.graph.build_tag_relationships()
        
        # Step 4: Generate summary
        stats = self.graph.get_tag_statistics()
        
        return {
            "query": query,
            "papers_found": len(added_papers),
            "papers_processed": len(extraction_results),
            "successful_extractions": sum(extraction_results.values()),
            "graph_stats": stats,
            "paper_ids": [p.paper_id for p in added_papers]
        }

    def get_graph_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of the current graph state."""
        stats = self.graph.get_tag_statistics()
        metrics = self.graph.get_graph_metrics()
        
        return {
            "tag_statistics": stats,
            "graph_metrics": metrics,
            "total_papers": len(self.graph._paper_nodes),
            "processing_status": {
                status: len([p for p in self.graph._paper_nodes.values() if p.processing_status == status])
                for status in ["pending", "completed", "failed"]
            }
        }

    def export_graph(self, filepath: str, format: str = "json") -> None:
        """Export the graph to a file."""
        from pathlib import Path
        self.graph.export_graph(Path(filepath), format)

    def import_graph(self, filepath: str, format: str = "json") -> None:
        """Import a graph from a file."""
        from pathlib import Path
        self.graph.import_graph(Path(filepath), format)