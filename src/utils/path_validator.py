"""
Path Validator - Secure file path validation
Prevents path traversal, symlink attacks, and other file system vulnerabilities
"""

import os
from pathlib import Path
from typing import Optional, Set


class PathValidator:
    """
    Secure file path validator

    Validates file paths to prevent:
    - Path traversal attacks (../, ../../etc/passwd)
    - Symlink attacks
    - Directory traversal
    - Oversized files
    - Invalid file extensions
    """

    # Allowed file extensions for model files
    ALLOWED_EXTENSIONS: Set[str] = {
        '.h5', '.pb', '.keras', '.tflite',  # TensorFlow
        '.pth', '.pt', '.ckpt',              # PyTorch
        '.onnx'                               # ONNX
    }

    # Maximum file path length (DoS prevention)
    MAX_PATH_LENGTH: int = 4096

    # Maximum file size in bytes (500 MB)
    MAX_FILE_SIZE: int = 500 * 1024 * 1024

    @staticmethod
    def validate_input_path(path_str: str) -> Path:
        """
        Validate and secure input file path

        Args:
            path_str: User-provided file path

        Returns:
            Validated and resolved Path object

        Raises:
            ValueError: Invalid file path
            FileNotFoundError: File does not exist
        """
        # 1. Length check (DoS prevention)
        if len(path_str) > PathValidator.MAX_PATH_LENGTH:
            raise ValueError(
                f"Dosya yolu çok uzun (max {PathValidator.MAX_PATH_LENGTH} karakter)"
            )

        # 2. Convert to Path and resolve (eliminates ../, ./, etc.)
        try:
            path = Path(path_str).resolve(strict=False)
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Geçersiz dosya yolu: {path_str}") from e

        # 3. Check if file exists
        if not path.exists():
            raise FileNotFoundError(f"Dosya bulunamadı: {path_str}")

        # 4. Symlink check (symlink attack prevention)
        if path.is_symlink():
            raise ValueError(
                "Sembolik link dosyalarına güvenlik nedeniyle izin verilmiyor"
            )

        # 5. File vs directory check
        if not path.is_file():
            raise ValueError("Yalnızca dosyalara izin verilir, dizinlere değil")

        # 6. Extension validation
        if path.suffix.lower() not in PathValidator.ALLOWED_EXTENSIONS:
            allowed = ', '.join(sorted(PathValidator.ALLOWED_EXTENSIONS))
            raise ValueError(
                f"Desteklenmeyen dosya formatı: {path.suffix}\n"
                f"Desteklenen formatlar: {allowed}"
            )

        # 7. File size check
        file_size = path.stat().st_size
        if file_size > PathValidator.MAX_FILE_SIZE:
            max_mb = PathValidator.MAX_FILE_SIZE / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            raise ValueError(
                f"Dosya boyutu çok büyük ({actual_mb:.1f} MB). "
                f"Maksimum izin verilen: {max_mb:.0f} MB"
            )

        # 8. Readable check
        if not os.access(path, os.R_OK):
            raise PermissionError(f"Dosya okunamıyor: {path}")

        return path

    @staticmethod
    def validate_output_path(
        path_str: str,
        allowed_base_dir: Optional[Path] = None,
        create_dirs: bool = True
    ) -> Path:
        """
        Validate and secure output file path

        Args:
            path_str: User-provided output path
            allowed_base_dir: Allowed base directory (optional)
            create_dirs: Whether to create parent directories

        Returns:
            Validated Path object

        Raises:
            ValueError: Invalid output path
        """
        # 1. Length check
        if len(path_str) > PathValidator.MAX_PATH_LENGTH:
            raise ValueError(
                f"Çıkış yolu çok uzun (max {PathValidator.MAX_PATH_LENGTH} karakter)"
            )

        # 2. Resolve path
        try:
            path = Path(path_str).resolve()
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Geçersiz çıkış yolu: {path_str}") from e

        # 3. If allowed_base_dir specified, ensure path is within it
        if allowed_base_dir:
            allowed_base_dir = allowed_base_dir.resolve()
            try:
                path.relative_to(allowed_base_dir)
            except ValueError:
                raise ValueError(
                    f"Çıkış yolu izin verilen dizin dışında.\n"
                    f"İzin verilen: {allowed_base_dir}\n"
                    f"Denenen: {path}"
                )

        # 4. Parent directory creation with depth limit
        if create_dirs and not path.parent.exists():
            # Count how many new directories would be created
            current = path.parent
            new_dir_count = 0
            while not current.exists():
                new_dir_count += 1
                if new_dir_count > 3:
                    raise ValueError(
                        "Çok fazla yeni dizin oluşturma denemesi (max 3 seviye)"
                    )
                current = current.parent

            # Create parent directories
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise ValueError(f"Dizin oluşturulamadı: {path.parent}") from e

        # 5. Check write permission on parent directory
        if path.parent.exists() and not os.access(path.parent, os.W_OK):
            raise PermissionError(f"Dizin yazılabilir değil: {path.parent}")

        # 6. If file exists, check if we can overwrite
        if path.exists():
            if not os.access(path, os.W_OK):
                raise PermissionError(f"Dosya üzerine yazılamıyor: {path}")

        return path

    @staticmethod
    def get_safe_workspace(base_name: str = "modelblaze_output") -> Path:
        """
        Get a safe workspace directory for output files

        Args:
            base_name: Base directory name

        Returns:
            Safe workspace Path
        """
        workspace = Path.cwd() / base_name
        workspace.mkdir(exist_ok=True)
        return workspace

    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 255) -> str:
        """
        Sanitize filename by removing dangerous characters

        Args:
            filename: Original filename
            max_length: Maximum filename length

        Returns:
            Sanitized filename
        """
        # Remove path separators and null bytes
        dangerous_chars = ['/', '\\', '\0', '..']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')

        # Remove control characters
        filename = ''.join(char for char in filename if ord(char) >= 32)

        # Truncate if too long
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            name = name[:max_length - len(ext) - 3] + '...'
            filename = name + ext

        return filename
