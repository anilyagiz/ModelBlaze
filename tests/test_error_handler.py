"""
Test Error Handler - Security tests for error handling
"""

import pytest
import logging
from src.utils.error_handler import ErrorHandler, ModelBlazeError, ModelLoadError


class TestErrorHandler:
    """Test ErrorHandler security features"""

    def test_handle_error_generic_message(self):
        """Test that detailed error info is not exposed to users"""
        # Sensitive error with path information
        error = FileNotFoundError("/secret/path/to/model.pth")

        # Handler should return generic message
        safe_message = ErrorHandler.handle_error(error)

        # Should not contain sensitive path
        assert "/secret/path" not in safe_message
        assert "Model dosyası bulunamadı" in safe_message

    def test_handle_error_with_logger(self, caplog):
        """Test that detailed errors are logged"""
        error = RuntimeError("Detailed internal error with sensitive info")

        logger = logging.getLogger("test")
        with caplog.at_level(logging.ERROR):
            ErrorHandler.handle_error(error, logger=logger)

        # Check that detailed error was logged
        assert "Detailed internal error" in caplog.text

    def test_handle_error_permission_error(self):
        """Test PermissionError handling"""
        error = PermissionError("Access denied")

        safe_message = ErrorHandler.handle_error(error)

        assert "izin" in safe_message.lower()

    def test_handle_error_memory_error(self):
        """Test MemoryError handling"""
        error = MemoryError()

        safe_message = ErrorHandler.handle_error(error)

        assert "bellek" in safe_message.lower()

    def test_wrap_import_error_tensorflow(self):
        """Test TensorFlow import error message"""
        error = ImportError("No module named 'tensorflow'")

        message = ErrorHandler.wrap_import_error(error)

        assert "TensorFlow" in message
        assert "pip install tensorflow" in message

    def test_wrap_import_error_pytorch(self):
        """Test PyTorch import error message"""
        error = ImportError("No module named 'torch'")

        message = ErrorHandler.wrap_import_error(error)

        assert "PyTorch" in message
        assert "pip install torch" in message

    def test_wrap_import_error_onnx(self):
        """Test ONNX import error message"""
        error = ImportError("No module named 'onnx'")

        message = ErrorHandler.wrap_import_error(error)

        assert "ONNX" in message
        assert "pip install onnx" in message

    def test_handle_framework_error(self):
        """Test framework-specific error handling"""
        error = RuntimeError("TensorFlow internal error")

        safe_message = ErrorHandler.handle_framework_error(
            error,
            framework="tensorflow"
        )

        assert "TensorFlow" in safe_message or "tensorflow" in safe_message.lower()

    def test_custom_exception_types(self):
        """Test custom ModelBlaze exception types"""
        # Test that custom exceptions can be raised and caught
        with pytest.raises(ModelBlazeError):
            raise ModelBlazeError("Test error")

        with pytest.raises(ModelLoadError):
            raise ModelLoadError("Model load failed")

        # ModelLoadError should be subclass of ModelBlazeError
        with pytest.raises(ModelBlazeError):
            raise ModelLoadError("This should also be caught as ModelBlazeError")

    def test_keyboard_interrupt_not_caught(self):
        """Test that KeyboardInterrupt is not suppressed"""
        error = KeyboardInterrupt()

        # Should return message for KeyboardInterrupt
        safe_message = ErrorHandler.handle_error(error)

        assert "iptal" in safe_message.lower()
