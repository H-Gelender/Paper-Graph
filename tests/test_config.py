"""Test configuration for Paper-Graph."""

import pytest

try:
    from paper_graph.config import Config
    has_config = True
except ImportError:
    has_config = False


@pytest.mark.skipif(not has_config, reason="Config not available due to missing dependencies")
def test_config_load_from_env():
    """Test loading configuration from environment variables."""
    config = Config.load_from_env()
    assert config is not None
    assert isinstance(config.default_sources, list)
    assert config.max_results_per_search > 0


@pytest.mark.skipif(not has_config, reason="Config not available due to missing dependencies")
def test_config_validation():
    """Test configuration validation."""
    config = Config()
    api_keys_status = config.validate_api_keys()
    assert isinstance(api_keys_status, dict)
    assert "gemini_api_key" in api_keys_status
    assert "semantic_scholar_api_key" in api_keys_status


@pytest.mark.skipif(not has_config, reason="Config not available due to missing dependencies")
def test_config_directories():
    """Test directory creation."""
    config = Config()
    # This should not raise an exception
    config.create_directories()