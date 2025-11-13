"""
Tests for ModelLoader
"""

import pytest
from src.model_loader import ModelLoader


def test_model_loader_init():
    """Test ModelLoader initialization"""
    loader = ModelLoader()
    assert loader is not None
    assert len(loader.supported_formats) > 0


def test_supported_formats():
    """Test that supported formats are defined"""
    loader = ModelLoader()
    formats = loader.list_supported_formats()

    assert "tensorflow" in formats
    assert "pytorch" in formats
    assert "onnx" in formats

    assert ".h5" in formats["tensorflow"]
    assert ".pth" in formats["pytorch"]
    assert ".onnx" in formats["onnx"]


def test_load_invalid_path():
    """Test loading from invalid path"""
    loader = ModelLoader()

    with pytest.raises(FileNotFoundError):
        loader.load("nonexistent_model.onnx")


def test_load_unsupported_format():
    """Test loading unsupported format"""
    loader = ModelLoader()

    # Create a dummy file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        f.write(b"dummy")
        temp_path = f.name

    with pytest.raises(ValueError):
        loader.load(temp_path)

    # Clean up
    import os
    os.unlink(temp_path)
