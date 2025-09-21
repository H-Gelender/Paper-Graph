"""
Paper-Graph: A MCP LLM agent for creating graph structures from scientific papers.

This package provides functionality to:
1. Search for scientific papers using the paper-search-mcp
2. Extract tags from papers using Gemini 2.5 Flash Lite
3. Create graph structures with papers as nodes and tags as attributes
"""

__version__ = "0.1.0"
__author__ = "H-Gelender"

# Import core models and graph first
from .models import PaperNode, GraphTag, TagType
from .graph import PaperGraph

# Import agent with graceful error handling
try:
    from .agent import PaperGraphAgent
    _has_agent = True
except ImportError as e:
    # Agent requires optional dependencies
    PaperGraphAgent = None
    _has_agent = False
    import warnings
    warnings.warn(f"PaperGraphAgent not available due to missing dependencies: {e}")

# Import configuration with graceful error handling
try:
    from .config import Config
    _has_config = True
except ImportError as e:
    Config = None
    _has_config = False
    import warnings
    warnings.warn(f"Config not available due to missing dependencies: {e}")

# Define what's available
__all__ = ["PaperNode", "GraphTag", "TagType", "PaperGraph"]
if _has_agent:
    __all__.append("PaperGraphAgent")
if _has_config:
    __all__.append("Config")