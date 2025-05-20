"""
gui/main_window/handlers/image_manager.py

Image Manager - Central controller for all image-related operations

Responsibilities:
- Image loading, caching and display
- Metadata management
- Validation and error handling
- Coordination between UI panels

Dependencies:
- MainWindow (for panel access)
- CenterPanel (image display) 
- RightPanel (metadata editing)
- StatusBar (status updates)
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from tkinter import messagebox
from PIL import Image, UnidentifiedImageError

class ImageManager:  # Changed from ImageHandler
    """Main controller for image operations."""
    
    def __init__(self, main_window, cache_size: int = 50):
        """
        Initialize image handler.
        
        Args:
            main_window: Reference to main application window
            cache_size: Maximum images to cache (default: 50)
        """
        self.main = main_window
        self._image_cache = {}
        self._max_cache_size = cache_size
        self._valid_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')

    def show_current_image(self) -> None:
        """
        Display the currently selected image with validation and caching.
        
        Handles:
        - Index validation
        - Path resolution
        - File validation
        - Caching
        - UI updates
        """
        if not self._validate_image_state():
            return
            
        img_data = self._prepare_image_metadata()
        img_path = self._resolve_image_path(img_data)
        
        if not self._validate_image_path(img_path):
            return
            
        self._display_validated_image(img_path, img_data)

    def save_current_image(self) -> None:
        """
        Save metadata for current image with validation.
        
        Handles:
        - Data collection from UI
        - Metadata updating
        - Error handling
        - User feedback
        """
        if not self._validate_image_state():
            return
            
        try:
            new_metadata = self.main.right_panel.get_image_data()
            self._update_image_metadata(new_metadata)
            self.main.save_folder_data()
            messagebox.showinfo("Saved", "Image data updated successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image data: {str(e)}")

    # -------------------- Configuration -------------------- #
    
    def set_cache_size(self, size: int) -> None:
        """Set maximum number of images to cache."""
        self._max_cache_size = max(1, size)
        self._trim_cache()

    def set_valid_extensions(self, extensions: tuple) -> None:
        """Set valid image file extensions."""
        self._valid_extensions = extensions

    # -------------------- Core Operations -------------------- #

    def _validate_image_state(self) -> bool:
        """Check if current image state is valid."""
        return (
            0 <= self.main.current_image_index < len(self.main.images)
            and hasattr(self.main, 'current_folder')
            and self.main.current_folder
        )

    def _prepare_image_metadata(self) -> Dict[str, Any]:
        """Prepare image metadata with navigation context."""
        img_data = self.main.images[self.main.current_image_index].copy()
        img_data.update({
            'index': self.main.current_image_index,
            'total': len(self.main.images)
        })
        return img_data

    def _resolve_image_path(self, img_data: Dict[str, Any]) -> Path:
        """Get absolute path from image metadata."""
        return Path(self.main.current_folder) / img_data['url']

    def _validate_image_path(self, img_path: Path) -> bool:
        """Validate image path exists and has valid extension."""
        return (
            img_path.exists()
            and img_path.suffix.lower() in self._valid_extensions
        )

    def _display_validated_image(self, img_path: Path, img_data: Dict[str, Any]) -> None:
        """Display validated image with caching."""
        try:
            image = self._get_cached_or_load_image(img_path)
            self._update_interface(image, img_path, img_data)
        except (IOError, UnidentifiedImageError) as e:
            self.main.status_bar.update_status(f"Error loading image: {str(e)}")

    def _update_image_metadata(self, new_data: Dict[str, Any]) -> None:
        """Update metadata for current image."""
        self.main.images[self.main.current_image_index].update(new_data)

    # -------------------- Cache Management -------------------- #

    def _get_cached_or_load_image(self, img_path: Path) -> Image.Image:
        """Get image from cache or load new."""
        path_str = str(img_path)
        if path_str in self._image_cache:
            return self._image_cache[path_str]
            
        image = Image.open(img_path)
        self._cache_image(path_str, image)
        return image

    def _cache_image(self, path: str, image: Image.Image) -> None:
        """Cache image with LRU strategy."""
        if len(self._image_cache) >= self._max_cache_size:
            self._image_cache.pop(next(iter(self._image_cache)))
        self._image_cache[path] = image

    def _trim_cache(self) -> None:
        """Reduce cache size if needed."""
        while len(self._image_cache) > self._max_cache_size:
            self._image_cache.pop(next(iter(self._image_cache)))

    # -------------------- UI Coordination -------------------- #

    def _update_interface(self, image: Image.Image, path: Path, data: Dict[str, Any]) -> None:
        """Update all UI elements with new image."""
        self.main.center_panel.show_image(path, data)
        self.main.right_panel.load_image_data(data)
        self.main.update_navigation_buttons()
        self.main.status_bar.update_status(
            f"Image {self.main.current_image_index + 1} of {len(self.main.images)}"
        )