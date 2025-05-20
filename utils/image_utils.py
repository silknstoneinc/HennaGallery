"""
Enhanced Image Utilities for Henna Gallery Editor
===============================================

This module provides comprehensive image processing capabilities including:
- Image validation and verification
- Thumbnail generation
- Color analysis and extraction
- Format conversion
- Metadata handling

Key Features:
1. Complete preservation of existing functionality
2. Added color extraction using ColorThief
3. Robust error handling
4. Type hints for better IDE support
5. Detailed docstrings
"""

import os
import hashlib
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from PIL import Image, ImageOps, UnidentifiedImageError

# Optional import for color extraction
try:
    from colorthief import ColorThief
    COLOR_EXTRACTION_AVAILABLE = True
except ImportError:
    COLOR_EXTRACTION_AVAILABLE = False
    print("⚠️ ColorThief not installed - color extraction will be disabled")
    print("Install with: pip install colorthief")

def validate_image_file(filepath: Path) -> bool:
    """
    Validate that a file is a readable image file with comprehensive checks.
    
    Args:
        filepath: Path to the image file
        
    Returns:
        bool: True if valid image, False otherwise
        
    Example:
        >>> validate_image_file(Path("image.jpg"))
        True
    """
    try:
        with Image.open(filepath) as img:
            img.verify()
        return True
    except (IOError, UnidentifiedImageError, Image.DecompressionBombError) as e:
        print(f"Image validation failed for {filepath}: {str(e)}")
        return False

def compute_image_hash(filepath: Path) -> str:
    """
    Compute SHA-256 hash of an image file for duplicate detection.
    
    Args:
        filepath: Path to the image file
        
    Returns:
        str: Hexadecimal string of the file's hash
        
    Raises:
        IOError: If file cannot be read
        
    Example:
        >>> compute_image_hash(Path("image.jpg"))
        'a1b2c3...'
    """
    BLOCK_SIZE = 65536  # Read in 64kb chunks
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

def extract_dominant_colors(image_path: Path, num_colors: int = 3) -> List[str]:
    """
    Extract dominant colors from an image using ColorThief.
    
    Args:
        image_path: Path to the image file
        num_colors: Number of colors to extract (1-10)
        
    Returns:
        List of hex color strings (e.g., ["#A8D5BA", "#D8C6B8"])
        
    Example:
        >>> extract_dominant_colors(Path("design.jpg"), 3)
        ["#A8D5BA", "#D8C6B8", "#4A6FA5"]
    """
    if not COLOR_EXTRACTION_AVAILABLE:
        print("Color extraction disabled - ColorThief not installed")
        return []
    
    if not validate_image_file(image_path):
        print(f"Invalid image file: {image_path}")
        return []
    
    try:
        color_thief = ColorThief(str(image_path))
        palette = color_thief.get_palette(color_count=num_colors)
        return [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in palette]
    except Exception as e:
        print(f"Color extraction failed for {image_path}: {str(e)}")
        return []

def generate_thumbnail(
    image_path: Path,
    size: Tuple[int, int] = (150, 150),
    crop_to_fit: bool = False
) -> Optional[Image.Image]:
    """
    Generate high-quality thumbnails with optional cropping.
    
    Args:
        image_path: Path to source image
        size: Tuple of (width, height) for thumbnail
        crop_to_fit: Whether to crop to maintain aspect ratio
        
    Returns:
        PIL.Image or None if generation fails
        
    Example:
        >>> thumb = generate_thumbnail(Path("image.jpg"), (200, 200))
    """
    if not validate_image_file(image_path):
        return None
        
    try:
        with Image.open(image_path) as img:
            img = normalize_image_orientation(img)
            if crop_to_fit:
                thumb = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
            else:
                thumb = ImageOps.contain(img, size, Image.Resampling.LANCZOS)
            return thumb
    except Exception as e:
        print(f"Thumbnail generation failed for {image_path}: {str(e)}")
        return None

# [Rest of the existing functions remain exactly the same]
# [Keep all current implementations of:]
# - resize_image()
# - convert_to_webp() 
# - get_image_metadata()
# - normalize_image_orientation()
# - create_image_preview()
# - create_thumbnail()

# Only add the new extract_dominant_colors() function
# and the COLOR_EXTRACTION_AVAILABLE check at the top

def resize_image(
    image: Image.Image,
    max_size: Tuple[int, int],
    keep_aspect: bool = True
) -> Image.Image:
    """
    Resize an image while optionally maintaining aspect ratio.
    
    Args:
        image: PIL Image object
        max_size: Tuple of (max_width, max_height)
        keep_aspect: Whether to maintain aspect ratio
        
    Returns:
        Resized PIL Image
    """
    if not keep_aspect:
        return image.resize(max_size, Image.Resampling.LANCZOS)
    
    original_width, original_height = image.size
    max_width, max_height = max_size
    
    ratio = min(max_width / original_width, max_height / original_height)
    new_size = (int(original_width * ratio), int(original_height * ratio))
    
    return image.resize(new_size, Image.Resampling.LANCZOS)

def convert_to_webp(
    source_path: Path,
    destination_path: Path,
    quality: int = 80
) -> bool:
    """
    Convert an image to WebP format.
    
    Args:
        source_path: Path to source image
        destination_path: Path to save WebP image
        quality: Quality setting (1-100)
        
    Returns:
        bool: True if conversion succeeded
    """
    if not validate_image_file(source_path):
        return False
        
    try:
        with Image.open(source_path) as img:
            img.save(
                destination_path,
                'webp',
                quality=quality,
                method=6  # Best quality/slowest
            )
        return True
    except Exception:
        return False

def get_image_metadata(image_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract basic metadata from an image file.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dict with metadata or None if failed
    """
    if not validate_image_file(image_path):
        return None
        
    try:
        with Image.open(image_path) as img:
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'size_bytes': os.path.getsize(image_path)
            }
    except Exception:
        return None

def normalize_image_orientation(image: Image.Image) -> Image.Image:
    """
    Correct image orientation based on EXIF data.
    
    Args:
        image: PIL Image object
        
    Returns:
        Image with corrected orientation
    """
    try:
        exif = image.getexif()
        if exif:
            orientation = exif.get(0x0112)
            if orientation:
                # Rotate/flip according to EXIF orientation
                if orientation == 2:
                    image = ImageOps.mirror(image)
                elif orientation == 3:
                    image = image.rotate(180)
                elif orientation == 4:
                    image = ImageOps.flip(image)
                elif orientation == 5:
                    image = ImageOps.flip(image).rotate(-90, expand=True)
                elif orientation == 6:
                    image = image.rotate(-90, expand=True)
                elif orientation == 7:
                    image = ImageOps.mirror(image).rotate(-90, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
    except Exception:
        pass
        
    return image

def create_image_preview(
    image_path: Path,
    preview_size: Tuple[int, int] = (600, 600)
) -> Optional[Image.Image]:
    """
    Create a preview version of an image with proper orientation.
    
    Args:
        image_path: Path to source image
        preview_size: Maximum dimensions for preview
        
    Returns:
        PIL Image or None if failed
    """
    if not validate_image_file(image_path):
        return None
        
    try:
        with Image.open(image_path) as img:
            img = normalize_image_orientation(img)
            return resize_image(img, preview_size)
    except Exception:
        return None
    
    # utils/image_utils.py (add this function)
def create_thumbnail(image_path: Path, size: Tuple[int, int]) -> Optional[Image.Image]:
    """
    Create a thumbnail from an image file.
    
    Args:
        image_path: Path to the image file
        size: Tuple of (width, height) for the thumbnail
        
    Returns:
        PIL Image object or None if creation fails
    """
    if not validate_image_file(image_path):
        return None
    try:
        with Image.open(image_path) as img:
            # Create a copy of the original image to work with
            img_copy = img.copy()
            # Apply orientation correction if needed
            img_copy = normalize_image_orientation(img_copy)
            # Create thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)
            return img.copy()  # Return a copy to avoid file handle issues
    except Exception as e:
        print(f"Error creating thumbnail from {image_path}: {e}")
        return None