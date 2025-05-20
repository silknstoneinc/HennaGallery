"""
Main window package for Henna Gallery Editor.

Contains:
- Core window implementation
- Menu system
- Specialized handlers for different operations

Submodules:
handlers/
  - BatchProcessing: Bulk operations
  - FolderHandling: Directory management
  - Sorting: Image organization
"""

from .base import MainWindow
from .menu import MainMenu
from .handlers.folder_manager import FolderManager
from .handlers.image_manager import ImageManager
from .handlers.batch_processor import BatchProcessor

__all__ = ['MainWindow', 'MainMenu', 'FolderManager', 'ImageManager', 'BatchProcessor']