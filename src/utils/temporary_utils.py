"""
Temporary Utils - Safe temporary directory and file management
Automatic cleanup with context managers to prevent resource leaks
"""

import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Optional
import logging


logger = logging.getLogger(__name__)


@contextmanager
def temporary_directory(prefix: str = "modelblaze_") -> Generator[Path, None, None]:
    """
    Context manager for safe temporary directory management

    Automatically cleans up temporary directory on exit, even if exceptions occur.
    This prevents disk space leaks and /tmp partition filling up.

    Args:
        prefix: Prefix for temporary directory name

    Yields:
        Path to temporary directory

    Example:
        >>> with temporary_directory() as tmpdir:
        ...     output_path = tmpdir / "model.tflite"
        ...     # Use tmpdir...
        ... # tmpdir automatically deleted here

    """
    tmpdir: Optional[Path] = None
    try:
        tmpdir = Path(tempfile.mkdtemp(prefix=prefix))
        logger.debug(f"Created temporary directory: {tmpdir}")
        yield tmpdir
    finally:
        # Cleanup: Always runs, even if exception occurred
        if tmpdir and tmpdir.exists():
            try:
                shutil.rmtree(tmpdir)
                logger.debug(f"Cleaned up temporary directory: {tmpdir}")
            except Exception as e:
                # Log error but don't raise (cleanup failure shouldn't break main flow)
                logger.warning(f"Failed to cleanup temporary directory {tmpdir}: {e}")


@contextmanager
def temporary_file(
    suffix: str = "",
    prefix: str = "modelblaze_",
    delete: bool = True
) -> Generator[Path, None, None]:
    """
    Context manager for safe temporary file management

    Args:
        suffix: File suffix (e.g., '.tflite')
        prefix: File prefix
        delete: Whether to delete file on exit

    Yields:
        Path to temporary file

    Example:
        >>> with temporary_file(suffix='.tflite') as tmpfile:
        ...     # Write to tmpfile
        ...     tmpfile.write_bytes(data)
        ... # tmpfile automatically deleted here
    """
    tmpfile: Optional[Path] = None
    try:
        fd, tmppath = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        tmpfile = Path(tmppath)
        # Close file descriptor
        import os
        os.close(fd)
        logger.debug(f"Created temporary file: {tmpfile}")
        yield tmpfile
    finally:
        if delete and tmpfile and tmpfile.exists():
            try:
                tmpfile.unlink()
                logger.debug(f"Deleted temporary file: {tmpfile}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {tmpfile}: {e}")


def cleanup_old_temp_files(max_age_hours: int = 24):
    """
    Clean up old ModelBlaze temporary files

    Args:
        max_age_hours: Maximum age of temp files in hours

    Note:
        This is a utility function to clean up leaked temporary files
        that weren't properly cleaned up due to crashes or interruptions.
    """
    import time

    temp_dir = Path(tempfile.gettempdir())
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600

    cleaned_count = 0
    for item in temp_dir.glob("modelblaze_*"):
        try:
            # Check file age
            file_age = current_time - item.stat().st_mtime
            if file_age > max_age_seconds:
                if item.is_file():
                    item.unlink()
                    cleaned_count += 1
                elif item.is_dir():
                    shutil.rmtree(item)
                    cleaned_count += 1
                logger.debug(f"Cleaned up old temp item: {item}")
        except Exception as e:
            logger.warning(f"Failed to clean up {item}: {e}")

    if cleaned_count > 0:
        logger.info(f"Cleaned up {cleaned_count} old temporary items")

    return cleaned_count
