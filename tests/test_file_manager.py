import pytest
import tempfile
import os
from src.file_manager import FileManager

def test_file_manager_initialization():
    """Test that FileManager can be initialized"""
    manager = FileManager()
    assert manager is not None
    assert manager.current_file is None
    assert manager.file_content is None

def test_file_completer_initialization():
    """Test that FileCompleter can be initialized"""
    from src.file_manager import FileCompleter
    completer = FileCompleter()
    assert completer is not None