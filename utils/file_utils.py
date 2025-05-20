"""
File utility functions for Henna Gallery Editor.
Handles file operations, JSON management, path utilities, and asset loading.
"""

from __future__ import annotations
import os
import json
import shutil
import re
import hashlib
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, BinaryIO
from datetime import datetime
from PIL import Image, UnidentifiedImageError

# --------------------------
# Configuration Handling
# --------------------------

def load_config(
    config_path: Union[str, Path],
    default_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Load configuration from JSON file with defaults, including Google Cloud credentials.
    
    Args:
        config_path: Path to configuration file
        default_config: Default values if file doesn't exist or is invalid
        
    Returns:
        Dictionary with loaded configuration
        
    Example:
        >>> config = load_config('config.json', {
        ...     'google_credentials': 'path/to/credentials.json',
        ...     'vision_settings': {'max_results': 10}
        ... })
    """
    default = default_config or {}
    config_path = Path(config_path)
    
    if not config_path.exists():
        return default.copy()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            if not isinstance(config, dict):
                return default.copy()
            
            # Set Google credentials environment variable if specified
            if 'google_credentials' in config:
                creds_path = Path(config['google_credentials'])
                if creds_path.exists():
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(creds_path)
            
            # Only keep keys that exist in default config (if provided)
            if default:
                return {
                    **default,
                    **{k: v for k, v in config.items() if k in default}
                }
            return config
    except (json.JSONDecodeError, IOError, OSError) as e:
        print(f"Error loading config: {str(e)}")
        return default.copy()

# --------------------------
# Text and Path Utilities
# --------------------------

def slugify(text: str) -> str:
    """
    Convert text to a URL/filesystem-safe slug.
    
    Args:
        text: Input text to convert
        
    Returns:
        str: URL-safe version of the text
    """
    text = re.sub(r'[^\w\s-]', '', text.lower())
    return re.sub(r'[-\s]+', '-', text).strip('-_')

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to remove problematic characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    return filename.replace("\n", "").replace("\r", "").strip()

def ensure_directory_exists(path: Union[str, Path]) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        bool: True if directory exists or was created
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except (OSError, PermissionError):
        return False

# --------------------------
# File Operations
# --------------------------

def safe_rename(
    source: Union[str, Path],
    target: Union[str, Path],
    overwrite: bool = False
) -> bool:
    """
    Safely rename/move a file with error handling.
    
    Args:
        source: Source file path
        target: Target file path
        overwrite: Whether to overwrite existing
        
    Returns:
        bool: True if rename succeeded
    """
    source, target = Path(source), Path(target)
    if not source.exists():
        return False
    if target.exists() and not overwrite:
        return False
        
    try:
        if overwrite and target.exists():
            target.unlink()
        source.rename(target)
        return True
    except (OSError, PermissionError):
        return False

def copy_file_with_backup(
    source: Union[str, Path],
    target: Union[str, Path],
    backup: bool = True
) -> bool:
    """
    Copy a file with optional backup of existing target.
    
    Args:
        source: Source file path
        target: Target file path
        backup: Whether to create backup of existing
        
    Returns:
        bool: True if copy succeeded
    """
    source, target = Path(source), Path(target)
    if not source.exists():
        return False
        
    try:
        if backup and target.exists():
            backup_path = target.with_suffix(f"{target.suffix}.bak")
            backup_path.unlink(missing_ok=True)
            target.rename(backup_path)
            
        shutil.copy2(source, target)
        return True
    except (OSError, shutil.Error):
        return False

def get_files_by_extensions(
    directory: Union[str, Path],
    extensions: List[str],
    recursive: bool = False
) -> List[Path]:
    """
    Get files in directory with specified extensions.
    
    Args:
        directory: Directory to search
        extensions: List of file extensions (e.g. ['.jpg', '.png'])
        recursive: Whether to search subdirectories
        
    Returns:
        List of Path objects matching extensions
    """
    directory = Path(directory)
    if not directory.is_dir():
        return []
    
    if recursive:
        return [
            p for p in directory.rglob('*')
            if p.suffix.lower() in extensions and p.is_file()
        ]
    else:
        return [
            p for p in directory.glob('*')
            if p.suffix.lower() in extensions and p.is_file()
        ]

def create_unique_filename(
    directory: Union[str, Path],
    basename: str,
    extension: str
) -> Path:
    """
    Generate a unique filename in the specified directory.
    
    Args:
        directory: Target directory
        basename: Desired base filename
        extension: File extension with dot (e.g. '.jpg')
        
    Returns:
        Path: Unique file path
    """
    directory = Path(directory)
    counter = 1
    stem = slugify(basename)
    
    while True:
        candidate = directory / f"{stem}{extension}"
        if not candidate.exists():
            return candidate
            
        candidate = directory / f"{stem}-{counter}{extension}"
        if not candidate.exists():
            return candidate
            
        counter += 1

# --------------------------
# File Information
# --------------------------

def get_file_modified_time(filepath: Union[str, Path]) -> Optional[datetime]:
    """
    Get a file's last modified time as datetime.
    
    Args:
        filepath: Path to file
        
    Returns:
        datetime or None if failed
    """
    try:
        return datetime.fromtimestamp(os.path.getmtime(filepath))
    except (OSError, AttributeError):
        return None

def get_directory_size(directory: Union[str, Path]) -> int:
    """
    Calculate total size of all files in a directory (bytes).
    
    Args:
        directory: Path to directory
        
    Returns:
        int: Total size in bytes
    """
    total = 0
    try:
        for entry in os.scandir(directory):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_directory_size(entry.path)
        return total
    except (OSError, PermissionError):
        return 0

# --------------------------
# JSON Handling
# --------------------------

def load_json_data(filepath: Union[str, Path]) -> Any:
    """
    Safely load data from a JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Parsed JSON data or empty dict if failed
        
    Raises:
        json.JSONDecodeError: If file contains invalid JSON
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in {filepath}: {str(e)}",
            e.doc, e.pos
        )

def save_json_data(
    filepath: Union[str, Path],
    data: Any,
    indent: int = 2,
    ensure_ascii: bool = False
) -> bool:
    """
    Save data to a JSON file with error handling.
    
    Args:
        filepath: Path to save JSON file
        data: Data to serialize to JSON
        indent: Indentation level
        ensure_ascii: Force ASCII output
        
    Returns:
        bool: True if save succeeded
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        return True
    except (IOError, TypeError):
        return False

def load_config(
    config_path: Union[str, Path],
    default_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Load configuration from JSON file with defaults.
    
    Args:
        config_path: Path to configuration file
        default_config: Default values if file doesn't exist or is invalid
        
    Returns:
        Dictionary with loaded configuration
        
    Example:
        >>> config = load_config('config.json', {'api_key': '', 'quality': 90})
    """
    default = default_config or {}
    config_path = Path(config_path)
    
    if not config_path.exists():
        return default.copy()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            if not isinstance(config, dict):
                return default.copy()
            
            # Only keep keys that exist in default config (if provided)
            if default:
                return {
                    **default,
                    **{k: v for k, v in config.items() if k in default}
                }
            return config
    except (json.JSONDecodeError, IOError, OSError):
        return default.copy()

# --------------------------
# Image Utilities
# --------------------------

def validate_image_file(filepath: Union[str, Path]) -> bool:
    """
    Validate that a file is a readable image file.
    
    Args:
        filepath: Path to the image file
        
    Returns:
        bool: True if valid image, False otherwise
    """
    try:
        with Image.open(filepath) as img:
            img.verify()
        return True
    except (IOError, UnidentifiedImageError, Image.DecompressionBombError):
        return False

def compute_image_hash(filepath: Union[str, Path]) -> str:
    """
    Compute SHA-256 hash of an image file.
    
    Args:
        filepath: Path to the image file
        
    Returns:
        str: Hexadecimal string of the file's hash
        
    Raises:
        IOError: If file cannot be read
    """
    BLOCK_SIZE = 65536
    hasher = hashlib.sha256()
    
    try:
        with open(filepath, 'rb') as f:
            buf = f.read(BLOCK_SIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(BLOCK_SIZE)
        return hasher.hexdigest()
    except IOError as e:
        raise IOError(f"Could not read file {filepath}: {str(e)}")

def is_supported_image_format(filepath: Union[str, Path]) -> bool:
    """
    Check if a file is in a supported image format.
    
    Args:
        filepath: Path to file to check
        
    Returns:
        bool: True if file is a supported image format
    """
    try:
        with Image.open(filepath) as img:
            return True
    except (UnidentifiedImageError, IOError):
        return False

# --------------------------
# Asset Loading
# --------------------------

def load_image_asset(
    filepath: Union[str, Path],
    max_size: Optional[Tuple[int, int]] = None,
    convert_mode: Optional[str] = None
) -> Optional[Image.Image]:
    """
    Load an image asset with optional resizing and format conversion.
    
    Args:
        filepath: Path to image file
        max_size: Optional maximum (width, height) to resize to
        convert_mode: Optional mode to convert to (e.g., 'RGB', 'RGBA')
        
    Returns:
        PIL.Image or None if failed
    """
    try:
        img = Image.open(filepath)
        if max_size:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        if convert_mode and img.mode != convert_mode:
            img = img.convert(convert_mode)
        return img
    except (UnidentifiedImageError, IOError, OSError):
        return None

def save_image_asset(
    image: Image.Image,
    filepath: Union[str, Path],
    quality: int = 85,
    optimize: bool = True,
    **kwargs
) -> bool:
    """
    Save an image asset with quality and optimization options.
    
    Args:
        image: PIL Image object to save
        filepath: Destination path
        quality: Quality setting (1-100)
        optimize: Whether to optimize the image
        **kwargs: Additional format-specific options
        
    Returns:
        bool: True if save succeeded
    """
    try:
        image.save(filepath, quality=quality, optimize=optimize, **kwargs)
        return True
    except (IOError, OSError, ValueError):
        return False

def load_binary_asset(filepath: Union[str, Path]) -> Optional[bytes]:
    """
    Load a binary file completely into memory.
    
    Args:
        filepath: Path to binary file
        
    Returns:
        bytes content or None if failed
    """
    try:
        with open(filepath, 'rb') as f:
            return f.read()
    except IOError:
        return None

def stream_binary_asset(
    filepath: Union[str, Path],
    chunk_size: int = 4096
) -> Optional[BinaryIO]:
    """
    Open a binary file for streaming reading.
    
    Args:
        filepath: Path to binary file
        chunk_size: Suggested chunk size for reading
        
    Returns:
        Binary file object or None if failed
    """
    try:
        return open(filepath, 'rb')
    except IOError:
        return None

def get_asset_metadata(filepath: Union[str, Path]) -> Dict[str, Any]:
    """
    Get basic metadata about an asset file.
    
    Args:
        filepath: Path to asset file
        
    Returns:
        Dictionary with metadata including:
        - size: File size in bytes
        - modified: Last modified timestamp
        - mime_type: Detected MIME type
        - is_image: Whether file is an image
    """
    path = Path(filepath)
    metadata = {
        'size': 0,
        'modified': None,
        'mime_type': 'application/octet-stream',
        'is_image': False
    }
    
    if not path.exists() or not path.is_file():
        return metadata
    
    try:
        stat = path.stat()
        metadata['size'] = stat.st_size
        metadata['modified'] = datetime.fromtimestamp(stat.st_mtime)
        
        mime_type, _ = mimetypes.guess_type(path)
        if mime_type:
            metadata['mime_type'] = mime_type
            metadata['is_image'] = mime_type.startswith('image/')
            
    except OSError:
        pass
    
    return metadata