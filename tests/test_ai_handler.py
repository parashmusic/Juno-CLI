import pytest
from src.ai_handler import AIHandler

def test_ai_handler_initialization():
    """Test that AIHandler can be initialized"""
    handler = AIHandler()
    assert handler is not None

def test_ai_handler_attributes():
    """Test that AIHandler has required attributes"""
    handler = AIHandler()
    assert hasattr(handler, 'llm')