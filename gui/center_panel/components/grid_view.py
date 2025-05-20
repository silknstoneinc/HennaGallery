import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Optional, Set
from pathlib import Path

from config import get_color
from gui.styles import COLORS, FONTS
from .thumbnail_widget import ThumbnailWidget
from ...drag_handlers.shared_utils import find_draggable_widget

class GridView(tk.Frame):
    """Enhanced grid view with dynamic columns, multi-select and grouping."""
    
    def __init__(self, parent, controller):
        super().__init__(parent, bg=get_color("background", "#F9F7F4"))
        self.controller = controller
        self.on_thumbnails_loaded = None
        self.selected_indices: Set[int] = set()  # Track selected thumbnails
        self.group_mode: Optional[str] = None    # Current grouping mode
        self._init_ui()
        self._setup_bindings()

    def _init_ui(self):
        """Initialize grid view layout with enhanced styling."""
        self.configure(
            bg=COLORS["background"],
            padx=0,
            pady=0,
            highlightthickness=0
        )
        
        # Main container with shadow effect
        self.grid_container = tk.Frame(
            self,
            bg=COLORS["background"],
            padx=10,
            pady=10
        )
        self.grid_container.pack(fill="both", expand=True)
        
        # Control bar at top
        self.control_bar = tk.Frame(
            self.grid_container,
            bg=COLORS["background"],
            padx=5,
            pady=5
        )
        self.control_bar.pack(fill="x", pady=(0, 10))
        
        # Grouping controls
        ttk.Label(
            self.control_bar,
            text="Group by:",
            style="Bold.TLabel"
        ).pack(side="left", padx=(0, 5))
        
        self.group_var = tk.StringVar()
        self.group_menu = ttk.OptionMenu(
            self.control_bar,
            self.group_var,
            "None",
            "None",
            "Date",
            "Tags",
            "Featured",
            command=self._on_group_change
        )
        self.group_menu.pack(side="left")
        
        # Multi-select controls
        ttk.Button(
            self.control_bar,
            text="Clear Selection",
            style="Secondary.TButton",
            command=self._clear_selection
        ).pack(side="right", padx=(5, 0))
        
        # Scrollable canvas area
        self._setup_scrollable_area()
        
        # Configure grid columns for dynamic sizing
        self.grid_columnconfigure(0, weight=1)
        
    def _setup_scrollable_area(self):
        """Setup canvas and scrollbars with improved styling."""
        self.canvas_frame = tk.Frame(
            self.grid_container,
            bg=COLORS["background"]
        )
        self.canvas_frame.pack(fill="both", expand=True)
        
        self.grid_canvas = tk.Canvas(
            self.canvas_frame,
            bg=COLORS["background"],
            highlightthickness=0
        )
        
        self.scrollbar = ttk.Scrollbar(
            self.canvas_frame,
            orient="vertical",
            command=self.grid_canvas.yview
        )
        
        self.grid_inner_frame = tk.Frame(
            self.grid_canvas,
            bg=COLORS["background"]
        )
        
        # Configure canvas scrolling
        self.grid_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.grid_canvas.create_window((0, 0), window=self.grid_inner_frame, anchor="nw")
        
        # Layout with proper expansion
        self.grid_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind configuration events
        self.grid_inner_frame.bind(
            "<Configure>",
            lambda e: self._update_scrollregion()
        )
        
    def _setup_bindings(self):
        """Configure mouse wheel events and keyboard shortcuts."""
        self.grid_canvas.bind("<Enter>", self._bind_mousewheel)
        self.grid_canvas.bind("<Leave>", self._unbind_mousewheel)
        
        # Multi-select bindings
        self.bind("<Control-a>", self._select_all)
        self.bind("<Escape>", self._clear_selection)
        
    def _bind_mousewheel(self, event):
        """Bind mousewheel events when entering canvas."""
        self.grid_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
    def _unbind_mousewheel(self, event):
        """Unbind mousewheel events when leaving canvas."""
        self.grid_canvas.unbind_all("<MouseWheel>")
        
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.grid_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def _update_scrollregion(self):
        """Update the scrollable region."""
        self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all"))
        
    def update_view(self):
        """Update grid view with dynamic columns and enhanced thumbnails."""
        # Clear existing widgets
        for widget in self.grid_inner_frame.winfo_children():
            widget.destroy()
            
        self.selected_indices.clear()
        
        # Get current state
        images = getattr(self.controller.main_window, 'images', [])
        current_folder = getattr(self.controller.main_window, 'current_folder', '')
        
        if not images or not current_folder:
            self._show_placeholder("No images available")
            return
            
        # Calculate dynamic layout
        canvas_width = self.grid_canvas.winfo_width()
        thumb_width = self._calculate_thumbnail_size(canvas_width)
        
        # Group images if needed
        grouped_images = self._group_images(images)
        
        # Create thumbnails with enhanced styling
        row = 0
        for group_name, group_images in grouped_images.items():
            if self.group_mode:
                # Add group header
                header = ttk.Label(
                    self.grid_inner_frame,
                    text=group_name,
                    style="Heading.TLabel",
                    background=COLORS["secondary_light"],
                    padding=(10, 5)
                )
                header.grid(
                    row=row, column=0, columnspan=2, 
                    sticky="ew", pady=(10, 5), padx=5
                )
                row += 1
                
            # Create thumbnails for this group
            for i, img_data in enumerate(group_images):
                col = i % self.columns
                if col == 0 and i != 0:
                    row += 1
                    
                self._create_thumbnail_widget(
                    img_data, 
                    current_folder, 
                    row, 
                    col,
                    thumb_width
                )
                
            row += 1
            
        # Configure grid columns
        for col in range(self.columns):
            self.grid_inner_frame.grid_columnconfigure(
                col, 
                weight=1,
                uniform="cols"
            )
            
        self._update_scrollregion()
        
    def _calculate_thumbnail_size(self, canvas_width: int) -> int:
        """Calculate optimal thumbnail size based on available width."""
        min_thumb = 180  # Minimum thumbnail width
        max_thumb = 280  # Maximum thumbnail width
        padding = 15     # Padding between thumbnails
        
        # Calculate columns and thumbnail size
        self.columns = max(2, canvas_width // (min_thumb + padding))
        thumb_width = min(
            max_thumb, 
            (canvas_width - (padding * (self.columns + 1))) // self.columns
        )
        
        return thumb_width
        
    def _group_images(self, images: List[Dict]) -> Dict[str, List[Dict]]:
        """Group images by current grouping mode."""
        if not self.group_mode or self.group_mode == "None":
            return {"All Images": images}
            
        grouped = {}
        
        for img in images:
            if self.group_mode == "Date":
                key = img.get('date', 'Unknown Date')
            elif self.group_mode == "Tags":
                tags = img.get('keywords', [])
                key = tags[0] if tags else 'Untagged'
            elif self.group_mode == "Featured":
                key = "Featured" if img.get('featured', False) else "Standard"
            else:
                key = "Other"
                
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(img)
            
        return grouped
        
    def _create_thumbnail_widget(self, img_data: Dict, folder: str, 
                               row: int, col: int, width: int):
        """Create a thumbnail widget with enhanced styling."""
        container = tk.Frame(
            self.grid_inner_frame,
            bg=COLORS["background"],
            padx=5,
            pady=5
        )
        
        img_path = Path(folder) / img_data.get('url', '')
        thumb = ThumbnailWidget(
            parent=container,
            image_data=img_data,
            folder_name=getattr(self.controller.main_window, 'current_folder_name', ''),
            select_callback=self._select_image,
            image_path=img_path if img_path.exists() else None,
            width=width,
            height=int(width * 1.25)  # Maintain 4:5 aspect ratio
        )
        
        # Apply enhanced styling
        thumb.configure(
            relief="flat",
            borderwidth=0,
            highlightthickness=0
        )
        
        # Add shadow effect
        self._add_shadow_effect(container)
        
        # Set drag handler if available
        if hasattr(self, 'drag_handler'):
            thumb.drag_handler = self.drag_handler
            
        thumb.image_index = self._get_image_index(img_data)
        thumb.pack(fill="both", expand=True)
        
        container.grid(
            row=row,
            column=col,
            sticky="nsew",
            padx=5,
            pady=5
        )
        
        # Bind multi-select events
        thumb.bind("<Button-1>", lambda e, idx=thumb.image_index: self._handle_thumbnail_click(e, idx))
        
    def _add_shadow_effect(self, widget):
        """Add subtle shadow effect to thumbnail containers."""
        shadow = tk.Frame(
            self.grid_inner_frame,
            bg=COLORS["section_shadow"],
            relief="flat"
        )
        shadow.place(
            in_=widget,
            x=2,
            y=2,
            relwidth=1,
            relheight=1
        )
        shadow.lower(widget)
        
    def _handle_thumbnail_click(self, event, index):
        """Handle thumbnail selection with modifier keys."""
        if event.state & 0x0004:  # Ctrl key
            # Toggle selection
            if index in self.selected_indices:
                self.selected_indices.remove(index)
            else:
                self.selected_indices.add(index)
        elif event.state & 0x0001:  # Shift key
            # Range selection
            if self.selected_indices:
                last = max(self.selected_indices)
                start = min(last, index)
                end = max(last, index)
                self.selected_indices.update(range(start, end + 1))
            else:
                self.selected_indices.add(index)
        else:
            # Single selection
            self.selected_indices = {index}
            
        self._update_selection_visuals()
        self._trigger_selection_callback()
        
    def _update_selection_visuals(self):
        """Update visual state of selected thumbnails."""
        for child in self.grid_inner_frame.winfo_children():
            if hasattr(child, 'thumbnail_widget'):
                thumb = child.thumbnail_widget
                if thumb.image_index in self.selected_indices:
                    child.configure(highlightbackground=COLORS["accent"], highlightthickness=2)
                else:
                    child.configure(highlightthickness=0)
                    
    def _trigger_selection_callback(self):
        """Notify controller about selection changes."""
        if hasattr(self.controller, 'on_thumbnail_selection'):
            selected_data = [
                img for i, img in enumerate(self.controller.main_window.images)
                if i in self.selected_indices
            ]
            self.controller.on_thumbnail_selection(selected_data)
            
    def _select_image(self, index: int):
        """Handle thumbnail selection (original functionality)."""
        if hasattr(self.controller.main_window, 'images'):
            images = self.controller.main_window.images
            if images and 0 <= index < len(images):
                self.controller.main_window.current_image_index = index
                self.controller.main_window.show_current_image()
                self.controller.show_view("single")
                
    def _on_group_change(self, *args):
        """Handle group mode change."""
        self.group_mode = self.group_var.get()
        self.update_view()
        
    def _clear_selection(self, event=None):
        """Clear current selection."""
        self.selected_indices.clear()
        self._update_selection_visuals()
        self._trigger_selection_callback()
        
    def _select_all(self, event=None):
        """Select all thumbnails."""
        if hasattr(self.controller.main_window, 'images'):
            self.selected_indices = set(range(len(self.controller.main_window.images)))
            self._update_selection_visuals()
            self._trigger_selection_callback()
            
    def _get_image_index(self, img_data: Dict) -> int:
        """Get index of image in main images list."""
        for i, img in enumerate(self.controller.main_window.images):
            if img.get('url') == img_data.get('url'):
                return i
        return -1
        
    def _show_placeholder(self, message="No images available"):
        """Display placeholder message."""
        label = tk.Label(
            self.grid_inner_frame,
            text=message,
            font=FONTS["heading"],
            fg=COLORS["dark"],
            bg=COLORS["background"]
        )
        label.pack(pady=50)