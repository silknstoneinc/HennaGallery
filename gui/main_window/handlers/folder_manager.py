"""
gui/main_window/handlers/folder_manager.py

Folder Manager - Handles all folder-related business logic and operations

Responsibilities:
- Managing root folder selection and validation
- Scanning and listing gallery folders
- Finding thumbnail images for folder previews
- Handling all filesystem operations related to folders

Dependencies:
- MainWindow (for status updates and gallery access)
- GalleryManager (for root folder storage)
- LeftPanel (for folder list display)

Note: This is purely for business logic - UI interactions are handled elsewhere
"""

import os
import json
from typing import List, Dict, Optional, Any
from pathlib import Path
from tkinter import filedialog
from PIL import Image, UnidentifiedImageError

class FolderManager:
    """Central handler for all folder management operations."""
    
    def __init__(self, main_window):
        """
        Initialize with reference to main application window.
        
        Args:
            main_window: Reference to MainWindow instance for callbacks and access
                        to other components like GalleryManager and StatusBar
        """
        self.main = main_window
        
    def select_root_folder(self) -> None:
        """
        Handle root folder selection dialog and initialization.
        
        Triggers:
        - Folder selection dialog
        - Gallery structure scan
        - UI updates through main window
        
        Side Effects:
        - Updates gallery_manager.root_folder
        - Triggers left panel refresh
        - Updates status bar
        """
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.main.gallery_manager.root_folder = folder_path
            self.main.status_bar.update_status(f"Root folder set to: {folder_path}")
            folders = self.scan_gallery_structure()
            self.main.left_panel.load_folders(folders)

    def scan_gallery_structure(self) -> List[Dict[str, Any]]:
        """
        Scan root folder for valid gallery folders with error handling.
        
        Returns:
            List of folder dictionaries with:
            - name: Folder name
            - path: Full path
            - thumbnail_path: Path to first valid image or None
            
        Handles:
        - Permission errors
        - Empty folders
        - Invalid directories
        """
        folders = []
        if not hasattr(self.main.gallery_manager, 'root_folder'):
            return folders
            
        try:
            for item in sorted(os.listdir(self.main.gallery_manager.root_folder)):
                full_path = os.path.join(self.main.gallery_manager.root_folder, item)
                
                if not os.path.isdir(full_path):
                    continue
                    
                folder_data = self._process_gallery_folder(item, full_path)
                if folder_data:
                    folders.append(folder_data)
                    
        except Exception as e:
            self.main.status_bar.update_status(f"Error scanning folders: {str(e)}")
            
        return folders

    def _process_gallery_folder(self, folder_name: str, folder_path: str) -> Optional[Dict[str, Any]]:
        """
        Process individual gallery folder with validation.
        
        Args:
            folder_name: Name of the folder
            folder_path: Full path to folder
            
        Returns:
            Folder data dict if valid, None otherwise
        """
        try:
            if not os.listdir(folder_path):
                self.main.status_bar.update_status(
                    f"Skipped empty folder: {folder_name}", 
                    temporary=True
                )
                return None
                
            return {
                'name': folder_name,
                'path': folder_path,
                'thumbnail_path': self.find_first_image(full_path)
            }
            
        except PermissionError:
            self.main.status_bar.update_status(
                f"Permission denied: {folder_name}", 
                temporary=True
            )
            return None

    def find_first_image(self, folder_path: str) -> Optional[str]:
        """
        Find first valid image in folder for thumbnail preview.
        
        Args:
            folder_path: Path to search for images
            
        Returns:
            Path to first valid image file or None
            
        Handles:
        - Image verification
        - Permission errors
        - Corrupt image files
        """
        VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')
        
        try:
            for f in sorted(os.listdir(folder_path)):
                if f.lower().endswith(VALID_EXTENSIONS):
                    full_path = os.path.join(folder_path, f)
                    if self._validate_image_file(full_path):
                        return full_path
        except PermissionError:
            self.main.status_bar.update_status(
                f"Permission denied accessing images in {folder_path}", 
                temporary=True
            )
        return None

    def _validate_image_file(self, file_path: str) -> bool:
        """
        Validate that a file is a loadable image.
        
        Args:
            file_path: Path to image file
            
        Returns:
            True if valid image, False otherwise
        """
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except (IOError, SyntaxError, UnidentifiedImageError):
            return False