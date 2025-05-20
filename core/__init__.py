"""
Core package initialization for Henna Gallery application.

Exports:
- Main application components
- Exception classes
- Manager classes
- Processor classes

Usage:
>>> from henna_gallery import GalleryManager, VisionProcessor
"""

from .exceptions import (
    ImageProcessingError,
    GalleryConfigError,
    GalleryManagerError,
    VisionAPIError,
    DragOperationError,
    GalleryExportError  # New export
)

from .vision_processor import VisionProcessor
from .gallery_manager import GalleryManager
from .export_manager import ExportManager
from .schema_validator import SchemaValidator

__all__ = [
    'ImageProcessingError',
    'GalleryConfigError',
    'GalleryManagerError',
    'VisionAPIError',
    'DragOperationError',
    'GalleryExportError',  # New export 
    'VisionProcessor',
    'GalleryManager',
    'ExportManager',
    'SchemaValidator'
]