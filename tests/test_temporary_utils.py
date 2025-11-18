"""
Test Temporary Utils - Tests for temporary file/directory management
"""

import pytest
from pathlib import Path
import time

from src.utils.temporary_utils import temporary_directory, temporary_file


class TestTemporaryUtils:
    """Test temporary file and directory utilities"""

    def test_temporary_directory_created_and_cleaned(self):
        """Test that temporary directory is created and cleaned up"""
        tmpdir_path = None

        with temporary_directory() as tmpdir:
            tmpdir_path = tmpdir
            # Directory should exist
            assert tmpdir.exists()
            assert tmpdir.is_dir()

            # Create a file inside
            test_file = tmpdir / "test.txt"
            test_file.write_text("test content")
            assert test_file.exists()

        # After context exit, directory should be cleaned up
        assert not tmpdir_path.exists()

    def test_temporary_directory_cleanup_on_exception(self):
        """Test that temporary directory is cleaned up even if exception occurs"""
        tmpdir_path = None

        try:
            with temporary_directory() as tmpdir:
                tmpdir_path = tmpdir
                assert tmpdir.exists()

                # Raise exception
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Directory should still be cleaned up
        assert not tmpdir_path.exists()

    def test_temporary_file_created_and_deleted(self):
        """Test that temporary file is created and deleted"""
        tmpfile_path = None

        with temporary_file(suffix=".txt") as tmpfile:
            tmpfile_path = tmpfile
            # File should exist
            assert tmpfile.exists()
            assert tmpfile.suffix == ".txt"

            # Write content
            tmpfile.write_text("test content")
            assert tmpfile.read_text() == "test content"

        # After context exit, file should be deleted
        assert not tmpfile_path.exists()

    def test_temporary_file_not_deleted_if_requested(self):
        """Test that temporary file can be kept if delete=False"""
        tmpfile_path = None

        with temporary_file(suffix=".txt", delete=False) as tmpfile:
            tmpfile_path = tmpfile
            tmpfile.write_text("test content")

        # File should still exist
        assert tmpfile_path.exists()

        # Manual cleanup
        tmpfile_path.unlink()

    def test_temporary_directory_with_prefix(self):
        """Test temporary directory with custom prefix"""
        with temporary_directory(prefix="modelblaze_test_") as tmpdir:
            assert "modelblaze_test_" in tmpdir.name

    def test_temporary_file_cleanup_on_exception(self):
        """Test that temporary file is deleted even if exception occurs"""
        tmpfile_path = None

        try:
            with temporary_file(suffix=".txt") as tmpfile:
                tmpfile_path = tmpfile
                tmpfile.write_text("test")

                # Raise exception
                raise ValueError("Test exception")
        except ValueError:
            pass

        # File should still be deleted
        assert not tmpfile_path.exists()

    def test_nested_temporary_directories(self):
        """Test nested temporary directories"""
        outer_path = None
        inner_path = None

        with temporary_directory() as outer:
            outer_path = outer
            assert outer.exists()

            with temporary_directory() as inner:
                inner_path = inner
                assert inner.exists()

                # Create file in inner
                (inner / "test.txt").write_text("inner")

            # Inner should be cleaned up
            assert not inner_path.exists()

            # Outer should still exist
            assert outer_path.exists()

        # Outer should now be cleaned up
        assert not outer_path.exists()
