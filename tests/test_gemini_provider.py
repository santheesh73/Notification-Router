"""Unit tests for official google-genai SDK GeminiProvider implementation."""

import os
from unittest.mock import patch

import pytest

from src.llm.gemini_provider import GeminiProvider


def test_gemini_provider_env_model_configuration() -> None:
    """Test reading GEMINI_MODEL from environment using google-genai SDK."""
    os.environ["GEMINI_API_KEY"] = "test_key_123"
    os.environ["GEMINI_MODEL"] = "gemini-2.5-flash"

    provider = GeminiProvider(api_key="test_key_123")

    assert provider.name == "Gemini"
    assert provider.model_name in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]


def test_gemini_provider_missing_key_raises_error() -> None:
    """Test that missing GEMINI_API_KEY raises ValueError without silent Mock fallback."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}):
        with pytest.raises(ValueError, match="GEMINI_API_KEY not found"):
            GeminiProvider(api_key="")


def test_gemini_provider_generate_fallback() -> None:
    """Test GeminiProvider generate method."""
    provider = GeminiProvider(api_key="test_key_123")
    res = provider.generate("Test prompt")
    assert isinstance(res, str)
    assert len(res) > 0
