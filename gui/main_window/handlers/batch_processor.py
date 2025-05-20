"""
gui/main_window/handlers/batch_processor.py

Batch Processor - Handles bulk operations on multiple folders

Responsibilities:
- Processing multiple folders in batch
- Thread management for background processing
- Progress reporting
- Coordinating with GalleryManager for actual processing

Dependencies:
- MainWindow (for access to other components)
- GalleryManager (for folder processing)
- ThreadUtils (for background operations)
"""

from typing import Callable
from tkinter import messagebox
from utils.thread_utils import run_in_thread

class BatchProcessor:
    """Handles batch processing operations with thread safety."""
    
    def __init__(self, main_window):
        """
        Initialize with reference to main application window.
        
        Args:
            main_window: Reference to MainWindow instance
        """
        self.main = main_window
        
    def process_all_folders(self) -> None:
        """Execute batch processing of all folders with validation."""
        if not self._validate_root_folder():
            return
            
        run_in_thread(
            self._process_folders_task,
            self._handle_completion
        )

    def _validate_root_folder(self) -> bool:
        """Check if root folder is set."""
        if not hasattr(self.main.gallery_manager, 'root_folder'):
            messagebox.showerror("Error", "Please select root folder first")
            return False
        return True

    def _process_folders_task(self) -> int:
        """Background task to process folders."""
        total = 0
        folders = self.main.folder_manager.scan_gallery_structure()
        
        for i, folder in enumerate(folders):
            count = self.main.gallery_manager.process_folder(folder['path'])
            total += count
            self._update_progress(i, len(folders), count, folder['name'])
            
        return total

    def _update_progress(self, current: int, total: int, count: int, name: str) -> None:
        """Update progress status."""
        progress = (current + 1) / total * 100
        self.main.status_bar.update_status(
            f"Processed {name} ({count} new images)", 
            progress
        )

    def _handle_completion(self, total: int) -> None:
        """Handle batch completion."""
        messagebox.showinfo(
            "Complete", 
            f"Batch processing completed\n{total} new images processed"
        )
        self.main.left_panel.load_folders(
            self.main.folder_manager.scan_gallery_structure()
        )