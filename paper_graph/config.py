"""
Configuration management for the Paper-Graph system.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Configuration settings for Paper-Graph."""
    
    # API Keys
    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API key for tag extraction")
    semantic_scholar_api_key: Optional[str] = Field(default=None, description="Semantic Scholar API key")
    
    # Default search settings
    default_sources: list[str] = Field(default=["arxiv", "pubmed"], description="Default paper sources")
    max_results_per_search: int = Field(default=20, description="Maximum results per search")
    
    # Tag extraction settings
    tag_extraction_temperature: float = Field(default=0.3, description="Temperature for tag extraction")
    max_tags_per_paper: int = Field(default=15, description="Maximum tags to extract per paper")
    min_tag_confidence: float = Field(default=0.5, description="Minimum confidence for tags")
    
    # Graph settings
    min_shared_tags_for_edge: int = Field(default=1, description="Minimum shared tags to create edge")
    auto_build_relationships: bool = Field(default=True, description="Automatically build relationships")
    
    # File paths
    default_export_path: str = Field(default="./exports", description="Default export directory")
    cache_directory: str = Field(default="./cache", description="Cache directory")
    
    # Rate limiting
    api_delay_seconds: float = Field(default=1.0, description="Delay between API calls")
    max_concurrent_requests: int = Field(default=5, description="Maximum concurrent API requests")

    @classmethod
    def load_from_env(cls, env_file: Optional[str] = None) -> "Config":
        """Load configuration from environment variables and .env file."""
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to load from common locations
            for env_path in [".env", ".env.local", Path.home() / ".paper-graph.env"]:
                if Path(env_path).exists():
                    load_dotenv(env_path)
                    break
        
        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            semantic_scholar_api_key=os.getenv("SEMANTIC_SCHOLAR_API_KEY"),
            default_sources=os.getenv("DEFAULT_SOURCES", "arxiv,pubmed").split(","),
            max_results_per_search=int(os.getenv("MAX_RESULTS_PER_SEARCH", "20")),
            tag_extraction_temperature=float(os.getenv("TAG_EXTRACTION_TEMPERATURE", "0.3")),
            max_tags_per_paper=int(os.getenv("MAX_TAGS_PER_PAPER", "15")),
            min_tag_confidence=float(os.getenv("MIN_TAG_CONFIDENCE", "0.5")),
            min_shared_tags_for_edge=int(os.getenv("MIN_SHARED_TAGS_FOR_EDGE", "1")),
            auto_build_relationships=os.getenv("AUTO_BUILD_RELATIONSHIPS", "true").lower() == "true",
            default_export_path=os.getenv("DEFAULT_EXPORT_PATH", "./exports"),
            cache_directory=os.getenv("CACHE_DIRECTORY", "./cache"),
            api_delay_seconds=float(os.getenv("API_DELAY_SECONDS", "1.0")),
            max_concurrent_requests=int(os.getenv("MAX_CONCURRENT_REQUESTS", "5")),
        )

    def save_to_file(self, filepath: str) -> None:
        """Save configuration to a file."""
        config_dict = self.model_dump()
        
        with open(filepath, 'w') as f:
            f.write("# Paper-Graph Configuration\n")
            f.write("# Copy this to .env and fill in your API keys\n\n")
            
            for key, value in config_dict.items():
                env_key = key.upper()
                if isinstance(value, list):
                    value = ",".join(value)
                elif isinstance(value, bool):
                    value = str(value).lower()
                
                f.write(f"{env_key}={value}\n")

    def create_directories(self) -> None:
        """Create necessary directories."""
        Path(self.default_export_path).mkdir(parents=True, exist_ok=True)
        Path(self.cache_directory).mkdir(parents=True, exist_ok=True)

    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate that required API keys are available."""
        return {
            "gemini_api_key": bool(self.gemini_api_key),
            "semantic_scholar_api_key": bool(self.semantic_scholar_api_key),
        }


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.load_from_env()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config