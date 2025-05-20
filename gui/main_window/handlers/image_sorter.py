"""
gui/main_window/handlers/image_sorter.py

Image Sorter - Handles PROGRAMMATIC sorting of entire image collections

Responsibilities:
- Sorting entire image lists by various criteria
- Resetting view to first image after sort
- Providing user feedback
- Persisting sorted state

Dependencies:
- MainWindow (for image list access)
- ImageManager (for display updates)
"""

from tkinter import messagebox
from typing import List, Dict

class ImageSorter:
    """Handles bulk sorting operations for image collections."""
    
    def __init__(self, main_window):
        """
        Initialize with main window reference.
        
        Args:
            main_window: Reference to main application window
        """
        self.main = main_window
    
    def sort_by_filename(self, reverse: bool = False) -> None:
        """
        Sort entire collection by filename.
        
        Args:
            reverse: False for A-Z, True for Z-A
        """
        if not self.main.images:
            return
            
        self.main.images.sort(
            key=lambda x: x['url'].lower(), 
            reverse=reverse
        )
        self._finalize_operation(f"Images sorted {'Z-A' if reverse else 'A-Z'} by filename")

    def sort_by_featured(self) -> None:
        """Sort with featured images first."""
        if not self.main.images:
            return
            
        self.main.images.sort(
            key=lambda x: not x.get('featured', False)
        )
        self._finalize_operation("Featured images moved to top")

    def sort_by_metadata(self, key: str, reverse: bool = False) -> None:
        """
        Sort by any metadata field.
        
        Args:
            key: Metadata key to sort by
            reverse: False for ascending, True for descending
        """
        if not self.main.images:
            return
            
        self.main.images.sort(
            key=lambda x: str(x.get(key, '')).lower(),
            reverse=reverse
        )
        self._finalize_operation(f"Sorted by {key} ({'Z-A' if reverse else 'A-Z'})")

    def _finalize_operation(self, message: str) -> None:
        """
        Common post-sort operations.
        
        Args:
            message: Status message to display
        """
        # Reset to first image
        self.main.current_image_index = 0
        
        # Persist changes
        self.main.save_folder_data()
        
        # Update all views
        self.main.image_manager.show_current_image()
        self.main.center_panel.update_grid_view()
        
        # User feedback
        messagebox.showinfo("Sorted", message)
        self.main.status_bar.update_status(message)