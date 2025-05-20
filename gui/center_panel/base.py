"""
gui/center_panel/base.py

Center Panel - Main display area for image viewing and management

Responsibilities:
- Displaying images in single or grid view
- Handling zoom/pan functionality
- Managing view switching between single/grid modes
- Coordinating with main window for navigation
- Maintaining image state and references

Dependencies:
- Components: single_view, grid_view, view_controls, zoom_controls
- Utils: image_utils
- Config: color management
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, Callable, List, Tuple
from pathlib import Path
from PIL import Image, ImageTk

from config import get_color
from .components.draggable_info import DraggableInfo
from .components.single_view import SingleView
from .components.grid_view import GridView
from .components.view_controls import ViewControls
from .components.zoom_controls import ZoomControls
from utils.image_utils import validate_image_file, create_image_preview
from gui.styles import COLORS, FONTS
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from gui.main_window.base import MainWindow

class CenterPanel(tk.Frame):
    """Main controller for center panel functionality."""
    
    def __init__(self, parent: tk.Widget, status_callback: Callable[[str], None], main_window: 'MainWindow'):
        super().__init__(parent, bg=get_color("background", "#F9F7F4"))
        self.status_cb = status_callback
        self.main_window = main_window  # Explicit reference
        
        # Initialize all components first
        self.view_container = None
        self.single_view = None
        self.grid_view = None
        self.controls_frame = None
        self.zoom_controls = None
        self.view_controls = None
        self.reorder_handler = None # This will be set by MainWindow

        # State management - Initialize with empty/default values    
        self._image_references = []
        self.current_image = None
        self.image_path = None
        self.original_image = None
        self.current_metadata = {} # Initialize as empty dict instead of None
        self.filtered_images = None
        self.current_folder_name = ""
        
        # Navigation callbacks
        self.show_next_callback = None
        self.show_prev_callback = None
        
        # Zoom/pan configuration
        self.zoom_level = 1.0
        self.max_zoom = 3.0
        self.min_zoom = 0.5
        self.zoom_step = 0.1
        self.pan_start_x = None
        self.pan_start_y = None
        
        # View mode
        self.current_view = "single"
        
        # Initialize UI
        self._init_ui()
        self.show_placeholder()

    def _init_ui(self):
        """Initialize all UI components including grid view setup."""
        self.configure(
            bg=get_color("background", "#F9F7F4"),
            padx=0,
            pady=0
        )
        
        # Main container
        self.view_container = tk.Frame(self, bg=COLORS["background"], padx=10, pady=10)
        self.view_container.pack(fill="both", expand=True)
        
        # Make responsive
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Folder name display
        self.folder_name_var = tk.StringVar(value="No folder selected")
        self.folder_label = tk.Label(
                self.view_container,
                textvariable=self.folder_name_var,
                font=("Georgia", 13, "bold"),
                fg=get_color("accent_dark", "#9585C2"),
                bg=get_color("background", "#F9F7F4")
            ).pack(pady=(0, 5))

        # Initialize sub-components
        self.single_view = SingleView(self.view_container, self)
        self.grid_view = GridView(self.view_container, self)  # self is the controller
        
        # Controls frame
        self.controls_frame = tk.Frame(self, bg=get_color("background", "#F9F7F4"))
        self.controls_frame.pack(fill="x", side="bottom", pady=(5, 0))
        
        # Add controls
        self.zoom_controls = ZoomControls(self.controls_frame, self)
        self.zoom_controls.pack(side="left")
        
        self.view_controls = ViewControls(self.controls_frame, self)
        self.view_controls.pack(side="right")

        # Show single view by default
        self.show_view("single")

    def setup_drag_handlers(self, drag_handler):
        """Configure drag handlers for this panel"""
        self.drag_handler = drag_handler
        if hasattr(self, 'grid_view'):
            self.grid_view.drag_handler = drag_handler  # Direct assignment
            self.grid_view.update_view()  # Force refresh to propagate handler
            
    def _setup_thumbnail_drag_handlers(self):
        """Setup drag handlers for all thumbnails in grid view."""
        if not hasattr(self.grid_view, 'grid_inner_frame'):
            return
            
        for child in self.grid_view.grid_inner_frame.winfo_children():
            if hasattr(child, '_setup_bindings'):
                child._setup_bindings()

    def start_pan(self, event):
        """Start panning the image."""
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def pan_image(self, event):
        """Pan the image based on mouse movement."""
        if self.pan_start_x is not None and self.pan_start_y is not None:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.single_view.canvas.move("image", dx, dy)
            self.pan_start_x = event.x
            self.pan_start_y = event.y

    def end_pan(self, event):
        """End panning operation."""
        self.pan_start_x = None
        self.pan_start_y = None

    def show_image(self, image_path: Path, metadata: Dict) -> None:
        """Display an image with metadata."""
        # UPDATE FOLDER NAME FIRST - this ensures it's always set
        self.folder_name_var.set(Path(image_path).parent.name)
        
        if not validate_image_file(image_path):
            self.status_cb(f"Invalid image file: {image_path}")
            self.show_placeholder()
            return
            
        try:
            self._clear_image_references()
            self.image_path = image_path
            self.current_metadata = metadata
            img = create_image_preview(image_path, (1200, 1200))

            if img is None:
                raise ValueError("Failed to create image preview")
                
            self.original_image = img
            self.update_nav_display(metadata)
            self.update_info_overlay(metadata)
            self.zoom_level = 1.0
            
            # Force display update immediately
            self.update_display()
            self.update_idletasks()  # Ensure UI updates

        except Exception as e:
            self.status_cb(f"Error loading image: {str(e)}")
            self.show_placeholder()

    def on_folder_changed(self):
        """Handle folder change while maintaining current view state."""
        if self.current_view == "grid":
            self.grid_view.update_view()
        else:
            if self.current_image:
                self.single_view.display_image()
            else:
                self.show_placeholder()

    def update_display(self):
        """Update the current view's display."""
        if self.current_view == "single":
            self.single_view.display_image()
        elif self.current_view == "grid":
            self.grid_view.update_view()

    def update_grid_view(self):
        """Update the grid view with current images"""
        if hasattr(self, 'grid_view'):
            self.grid_view.update_view()
            # Setup drag handlers for new thumbnails
            self._setup_thumbnail_drag_handlers()
        else:
            self.status_cb("Grid view not initialized")

    def show_view(self, view_name: str):
        """Switch between view modes."""
        self.current_view = view_name
        self.view_controls.view_mode.set(view_name)  # Update the button state

        # Force update of the current view
        if view_name == "single":
            self.grid_view.pack_forget()
            self.single_view.pack(fill="both", expand=True)

            # Only update nav buttons if we have metadata
            if hasattr(self, 'current_metadata') and self.current_metadata:
                self.update_nav_buttons(self.current_metadata)
                self.single_view.display_image()
        
            # Always try to display the image
            if hasattr(self, 'current_image') and self.current_image:
                self.single_view.display_image()
            else:
                self.show_placeholder()
        else:
            self.single_view.pack_forget()
            self.grid_view.pack(fill="both", expand=True)
            # Force immediate grid view update with current data
            self.grid_view.update_view()
        
        # Force UI update
        self.update_idletasks()

    def _clear_image_references(self) -> None:
        """Clean up existing image references."""
        self._image_references.clear()
        self.current_image = None
        self.original_image = None

    def show_placeholder(self) -> None:
        """Display a placeholder image."""
        try:
            placeholder = Image.new(
                "RGB",
                (600, 600),
                color=get_color("background_dark", "#EDEAE4")
            )
            self.current_image = ImageTk.PhotoImage(placeholder)
            self._image_references.append(self.current_image)
            self.single_view.canvas.itemconfig(
                self.single_view.canvas_image,
                image=self.current_image
            )
            # Keep existing folder name but update status text
            self.single_view.info_text.set("No image selected")
            
        except Exception as e:
            self.status_cb(f"Placeholder error: {str(e)}")
            self.single_view.canvas.delete("all")

    def set_navigation_callbacks(self, next_cb: Callable, prev_cb: Callable):
        """Set navigation callbacks."""
        self.show_next_callback = next_cb
        self.show_prev_callback = prev_cb

    def update_nav_display(self, metadata: Dict):
        """Update navigation controls."""
        total = metadata.get('total', 1)
        index = metadata.get('index', 0) + 1
        self.single_view.image_count.set(f"Image {index} of {total}")
        self.update_nav_buttons(metadata)

    def update_nav_buttons(self, metadata: Dict):
        """Update navigation button states."""
        total = metadata.get('total', 1)
        index = metadata.get('index', 0)
        
        self.single_view.prev_btn.config(state="normal" if index > 0 else "disabled")
        self.single_view.next_btn.config(state="normal" if index < total - 1 else "disabled")

    def update_info_overlay(self, metadata: Dict) -> None:
        """Enhanced information overlay with consistent field mapping"""
        if not metadata:
            return

        # Field mapping and fallbacks
        file_name = self.image_path.name if hasattr(self, 'image_path') else 'N/A'
        title = metadata.get('title', metadata.get('headline', 'Untitled'))
        caption = metadata.get('caption', 'No description')
        keywords = metadata.get('keywords', metadata.get('tags', []))
        alt_text = metadata.get('alt_text', 'No alt text')
        
        # Truncated version for main display
        info_lines = [
            f"File: {file_name}",
            f"Title: {title}",
            f"Caption: {caption[:60] + '...' if len(caption) > 60 else caption}",
            f"Keywords: {', '.join(keywords[:3])}{'...' if len(keywords) > 3 else ''}",
            f"Alt Text: {alt_text[:60] + '...' if len(alt_text) > 60 else alt_text}"
        ]

         # Full version for tooltip
        full_info_lines = [
            f"File: {file_name}",
            f"Title: {title}",
            f"Caption: {caption}",
            f"Keywords: {', '.join(keywords)}",
            f"Alt Text: {alt_text}",
            f"Dimensions: {self.original_image.width}×{self.original_image.height}",
            f"Position: {metadata.get('index', 0) + 1} of {metadata.get('total', 1)}"
        ]
        
        self.single_view.info_text.set("\n".join(info_lines))
        self.single_view.full_info_text = "\n".join(full_info_lines)
        # Determine image type based on keywords/content
       # image_type = self._classify_image_type(keywords)
        
        #info_lines = [
         #   f"File: {file_name}",
          #  f"Title: {title}",
           # f"Caption: {caption[:60] + '...' if len(caption) > 60 else caption}",
            #f"Type: {image_type}",
           # f"Size: {self.original_image.width}×{self.original_image.height}",
           # f"Keywords: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}",
           # f"Alt Text: {alt_text[:60] + '...' if len(alt_text) > 60 else alt_text}",
           # f"Image {metadata.get('index', 0) + 1} of {metadata.get('total', 1)}"
        #]
        
        #self.single_view.info_text.set("\n".join(info_lines))

    def _classify_image_type(self, keywords: List[str]) -> str:
        """Classify image based on keywords"""
        keyword_categories = {
            'portrait': ['face', 'portrait', 'headshot'],
            'henna': ['henna', 'mehndi', 'design'],
            'event': ['wedding', 'party', 'event', 'celebration'],
            'body': ['arm', 'hand', 'leg', 'foot', 'belly']
        }
        
        for type_name, terms in keyword_categories.items():
            if any(term in ' '.join(keywords).lower() for term in terms):
                return type_name.title()
        return 'General'

    def show_next_image(self):
        """Handle next image navigation."""
        if self.show_next_callback:
            self.show_next_callback()
        else:
            self.status_cb("Navigation callback not set")

    def show_previous_image(self):
        """Handle previous image navigation."""
        if self.show_prev_callback:
            self.show_prev_callback()
        else:
            self.status_cb("Navigation callback not set")

    def zoom_in(self, event=None):
        """Zoom in with bounds checking."""
        if self.zoom_level < self.max_zoom:
            self.zoom_level = round(min(
                self.zoom_level + self.zoom_step,
                self.max_zoom
            ), 2)
            self.update_display()
            self.status_cb(f"Zoom: {int(self.zoom_level * 100)}%")

    def zoom_out(self, event=None):
        """Zoom out with bounds checking."""
        if self.zoom_level > self.min_zoom:
            self.zoom_level = round(max(
                self.zoom_level - self.zoom_step,
                self.min_zoom
            ), 2)
            self.update_display()
            self.status_cb(f"Zoom: {int(self.zoom_level * 100)}%")

    def zoom_reset(self, event=None):
        """Reset zoom to 100%."""
        self.zoom_level = 1.0
        self.update_display()
        self.status_cb("Zoom reset to 100%")

    def _on_resize(self, event):
        """Handle panel resizing to update grid layout"""
        if hasattr(self, 'grid_view') and self.current_view == "grid":
            self.grid_view.update_view()

    def get_images(self):
        return getattr(self.main_window, 'images', [])