"""
Left panel module for Henna Gallery Editor.
Handles folder navigation and selection functionality with robust thumbnail management.
Maintains all existing functionality while enhancing visual style.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Callable, Optional, Any
from pathlib import Path
from PIL import Image, ImageTk
import weakref
from PIL import ImageDraw
from PIL import ImageOps

from config import get_color
from utils.image_utils import validate_image_file
from gui.styles import COLORS, FONTS


class ThumbnailCache:
    """Final polished thumbnail cache implementation"""
    def __init__(self, max_size: int = 100):
        self._cache = {}
        self._order = []
        self.max_size = max_size
        self.thumbnail_size = (150, 180)  # Width x Height
        self.caption_area = 30  # Slightly increased for better visibility

    def get(self, image_path: Optional[str]) -> ImageTk.PhotoImage:
        """Get thumbnail with all fixes applied"""
        if not image_path:
            return self._default_thumbnail()
            
        if image_path in self._cache:
            self._order.remove(image_path)
            self._order.insert(0, image_path)
            return self._cache[image_path]
            
        try:
            if validate_image_file(image_path):
                img = Image.open(image_path).convert('RGB')
                img = self._process_thumbnail(img)
                photo = ImageTk.PhotoImage(img)
                self._add_to_cache(image_path, photo)
                return photo
        except Exception as e:
            print(f"Error loading thumbnail: {str(e)}")
            
        return self._default_thumbnail()

    def _process_thumbnail(self, img: Image.Image) -> Image.Image:
        """Process image without any text overlay"""
        base = Image.new('RGB', self.thumbnail_size, (255,255,255))
        img_width, img_height = self.thumbnail_size[0], self.thumbnail_size[1]-self.caption_area
        
        img.thumbnail((img_width, img_height), Image.Resampling.LANCZOS)
        x = (img_width - img.width) // 2
        y = (img_height - img.height) // 2
        
        base.paste(img, (x, y))
        
        # Add caption area (blank - text will be added via Tkinter)
        draw = ImageDraw.Draw(base)
        draw.rectangle(
            [0, img_height, self.thumbnail_size[0], self.thumbnail_size[1]],
            fill=(40,40,40)  # Dark gray background for caption
        )
        
        return base

    def _default_thumbnail(self) -> ImageTk.PhotoImage:
        """Default thumbnail without any text"""
        img = Image.new('RGB', self.thumbnail_size, (168, 213, 186))  # Sea green
        draw = ImageDraw.Draw(img)
        
        # Add embossed effect
        for i in range(1, 4):
            draw.rectangle(
                [i, i, self.thumbnail_size[0]-i, self.thumbnail_size[1]-i],
                outline=(220,220,220) if i == 1 else (100,100,100),
                width=1
            )
        
        # Add blank caption area
        draw.rectangle(
            [0, self.thumbnail_size[1]-self.caption_area, 
             self.thumbnail_size[0], self.thumbnail_size[1]],
            fill=(40,40,40)
        )
        
        return ImageTk.PhotoImage(img)

    def _add_to_cache(self, path: str, photo: ImageTk.PhotoImage) -> None:
        """Cache management"""
        if len(self._order) >= self.max_size:
            oldest = self._order.pop()
            del self._cache[oldest]
        self._cache[path] = photo
        self._order.insert(0, path)


class LeftPanel(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        folder_select_callback: Callable[[Dict[str, Any]], None],
        status_callback: Callable[[str], None],
        *args, **kwargs
    ):
        super().__init__(parent, *args, **kwargs)

        self.configure(
            bg=COLORS["secondary"],
            width=340,  # Fixed width
            padx=12,
            pady=12
        )
        
        self.folder_select_cb = folder_select_callback
        self.status_cb = status_callback
        self.folder_buttons: Dict[str, tk.Button] = {}
        self.thumbnail_cache = ThumbnailCache(max_size=50)
        self._image_references = []  # Maintain strong references to all images
        self.search_active = False

        self.pack_propagate(False)  # Prevent auto-resizing
        self._setup_ui()
        self._bind_events()

    def _setup_ui(self):
        """Initialize all UI components with enhanced styling"""
        
        # Header with folder count - Enhanced styling
        self.header_frame = tk.Frame(
            self, 
            bg=get_color("secondary_dark", "#C5B3A0"),
            padx=10,
            pady=8,
            highlightthickness=0,
            highlightbackground=get_color("border", "#D1C0AD")
        )
        self.header_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            self.header_frame,
            text="Select Folder",
            bg=get_color("secondary_dark", "#C5B3A0"),
            fg=get_color("text_dark", "#4A4A4A"),
            font=("Georgia", 14, "bold"),
            padx=5
        ).pack(side="left")
        
        self.folder_count = tk.Label(
            self.header_frame,
            text="0 folders",
            bg=get_color("secondary_dark", "#C5B3A0"),
            fg=get_color("text_light", "#6A6A6A"),
            font=("Georgia", 10, "italic"),
            padx=5
        )
        self.folder_count.pack(side="right")
        
        # Search frame with enhanced styling
        search_frame = tk.Frame(
            self, 
            bg=get_color("secondary_light", "#E5D9CC"),
            padx=5,
            pady=8,
            highlightthickness=1,
            highlightbackground=get_color("border", "#D1C0AD")
        )
        search_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            search_frame,
            text="Search Folders:",
            bg=get_color("secondary_light", "#E5D9CC"),
            fg=get_color("text", "#333333"),
            font=("Georgia", 12),
            padx=5
        ).pack(anchor="w")
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Georgia", 12),
            bg="white",
            fg=get_color("text_dark", "#333333"),
            relief="flat",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=get_color("border", "#D1C0AD"),
            highlightcolor=get_color("accent", "#B4A7D6")
        )
        self.search_entry.pack(fill="x", padx=5, pady=5)
        
        # Clear search button with enhanced styling
        self.clear_search_btn = ttk.Button(
            search_frame,
            text="Clear",
            command=self.clear_search,
            style="Secondary.TButton",
            width=6
        )
        self.clear_search_btn.pack(side="right", padx=(5,0))
        self.clear_search_btn.pack_forget()  # Hidden initially
        
        # Filter frame with enhanced styling
        filter_frame = tk.Frame(
            self, 
            bg=get_color("secondary_light", "#E5D9CC"),
            padx=5,
            pady=8,
            highlightthickness=1,
            highlightbackground=get_color("border", "#D1C0AD")
        )
        filter_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            filter_frame,
            text="Filter by Tag:",
            bg=get_color("secondary_light", "#E5D9CC"),
            fg=get_color("text", "#333333"),
            font=("Georgia", 12),
            padx=5
        ).pack(anchor="w")
        
        self.filter_var = tk.StringVar()
        self.filter_entry = tk.Entry(
            filter_frame,
            textvariable=self.filter_var,
            font=("Georgia", 12),
            bg="white",
            fg=get_color("text_dark", "#333333"),
            relief="flat",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=get_color("border", "#D1C0AD"),
            highlightcolor=get_color("accent", "#B4A7D6")
        )
        self.filter_entry.pack(fill="x", padx=5, pady=5)
        
        # Drop zone indicator (for drag-and-drop) - Enhanced styling
        self.drop_zone = tk.Frame(
            self,
            height=2,
            bg=get_color("accent_dark", "#9585C2"),
            highlightthickness=0
        )
        self.drop_zone.pack(fill="x", pady=5)
        self.drop_zone.pack_forget()
        
        # No results label - Enhanced styling
        self.no_results_label = tk.Label(
            self,
            text="No folders match your search",
            font=("Georgia", 12, "italic"),
            fg=get_color("text_light", "#7A7A7A"),
            bg=get_color("secondary", "#D8C6B8"),
            padx=10,
            pady=10
        )
        self.no_results_label.pack_forget()
        
        # Main container for scrollable area
        self.container = tk.Frame(
            self, 
            bg=COLORS["secondary"],
            highlightthickness=0
        )
        self.container.pack(fill="both", expand=True)
        
        # Create canvas and scrollbar with enhanced styling
        self.canvas = tk.Canvas(
            self.container,
            bg=COLORS["secondary"],
            highlightthickness=0
        )
        
        self.scrollbar = ttk.Scrollbar(
            self.container,
            orient="vertical",
            command=self.canvas.yview,
            style="Vertical.TScrollbar"
        )
        
        # Create frame inside canvas
        self.folders_frame = tk.Frame(
            self.canvas,
            bg=COLORS["secondary"],
            padx=5
        )
        
        # Configure canvas scrolling
        self.canvas.create_window((0, 0), window=self.folders_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Layout with proper expansion
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind configuration events
        self.folders_frame.bind(
            "<Configure>",
            lambda e: self._update_scrollregion()
        )

    def _bind_events(self):
        """Bind mouse wheel events for scrolling and search functionality"""
        self.search_entry.bind("<KeyRelease>", self._on_search)
        self.filter_entry.bind("<KeyRelease>", self._on_filter)
        
        # Prepare for drag-and-drop
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        self.canvas.bind("<Configure>", self._check_scroll_needed)

        # Add drag-and-drop bindings
        self.folders_frame.bind("<Enter>", lambda e: self.show_drop_zone(True))
        self.folders_frame.bind("<Leave>", lambda e: self.show_drop_zone(False))

    def _bind_mousewheel(self, event=None):
        """Bind mousewheel events when entering canvas"""
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", lambda e: self._on_mousewheel_scroll(-1))
        self.canvas.bind_all("<Button-5>", lambda e: self._on_mousewheel_scroll(1))

    def _unbind_mousewheel(self, event=None):
        """Unbind mousewheel events when leaving canvas"""
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _check_scroll_needed(self, event=None):
        """Check if scrolling is needed based on content height"""
        self.update_idletasks()
        if self.folders_frame.winfo_reqheight() > self.canvas.winfo_height():
            self.scrollbar.pack(side="right", fill="y")
            self._bind_mousewheel()
        else:
            self.scrollbar.pack_forget()
            self._unbind_mousewheel()

    def _update_scrollregion(self):
        """Update the scrollable region"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._check_scroll_needed()

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling for Windows/Mac"""
        if event.delta:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        return "break"  # Prevent event propagation

    def _on_mousewheel_scroll(self, units):
        """Handle mouse wheel scrolling for Linux"""
        self.canvas.yview_scroll(units, "units")
        return "break"

    def load_folders(self, folders: List[Dict[str, Any]]) -> None:
        """Load folders into the navigation panel"""
        self._clear_folders()
        
        if not folders:
            self.status_cb("No folders found")
            self.folder_count.config(text="0 folders")
            self.no_results_label.pack(fill="x", pady=20)
            return
            
        self.status_cb(f"Loading {len(folders)} folders...")
        self.folder_count.config(text=f"{len(folders)} folders")
        
        # Configure grid columns
        self.folders_frame.grid_columnconfigure(0, weight=1, minsize=150)
        self.folders_frame.grid_columnconfigure(1, weight=1, minsize=150)
        
        for i, folder in enumerate(folders):
            self._add_folder_button(folder, i)
        
        # Update the layout and check if scrolling is needed
        self.update_idletasks()
        self._update_scrollregion()
        
        self.status_cb(f"Loaded {len(folders)} folders")
        self._update_search_results()

    def update_folder_display(self, folder_path: str, image_count: int) -> None:
        """Update the display for a single folder with new image count"""
        if folder_path in self.folder_buttons:
            btn = self.folder_buttons[folder_path]
            folder_name = Path(folder_path).name
            btn.config(text=f"{folder_name}\n({image_count} images)")
            
            # Update tooltip if it exists
            if hasattr(btn, 'tooltip'):
                btn.tooltip.text = f"{folder_name} ({image_count} images)"

    def _add_folder_button(self, folder: Dict[str, Any], index: int) -> None:
        """Preserves original folder selection functionality with visual improvements"""
        row = index // 2
        col = index % 2
        
        # Original thumbnail loading
        thumb_path = folder.get('thumbnail_path')
        thumbnail = self.thumbnail_cache.get(thumb_path)
        self._image_references.append(thumbnail)
        
        # Create button with visual improvements
        btn = tk.Button(
            self.folders_frame,
            text=f"{folder['name']}\n({folder.get('image_count', 0)} images)",
            image=thumbnail,
            compound="top",
            command=lambda f=folder: self._trigger_folder_select(f),
            bg=get_color("background", "#F9F7F4"),
            fg="#5E4D8B",
            activebackground=get_color("primary", "#A8D5BA"),
            activeforeground="white",
            width=148,
            height=170,
            wraplength=140,
            justify="center",
            font=("Georgia", 10),
            relief="flat",
            borderwidth=0,
            highlightthickness=0
        )
        
        btn.grid(
            row=row,
            column=col,
            sticky="nsew",
            padx=5,
            pady=5
        )
        
        # Critical original attributes
        btn.folder_path = folder['path']
        
        # Original hover effects
        btn.bind("<Enter>", self._on_folder_hover)
        btn.bind("<Leave>", self._on_folder_leave)
        
        self.folder_buttons[folder['path']] = btn

    def _trigger_folder_select(self, folder: Dict[str, Any]) -> None:
        """EXACT original implementation that properly refreshes grid view"""
        try:
            self.folder_select_cb(folder)  # This triggers the grid view refresh
        except Exception as e:
            self.status_cb(f"Error selecting folder: {str(e)}")

    def _clear_folders(self) -> None:
        """Clear all folder buttons while preserving references"""
        for widget in self.folders_frame.winfo_children():
            widget.destroy()
            
        self.folder_buttons.clear()
        self._image_references.clear()  # Clear old references
        self.thumbnail_cache = ThumbnailCache(max_size=50)

    def _on_search(self, event=None) -> None:
        """Enhanced search functionality with visual feedback"""
        self._update_search_results()

    def _on_filter(self, event=None) -> None:
        """Filter functionality with combined search"""
        self._update_search_results()

    def _update_search_results(self):
        """Update visible folders based on search and filter terms"""
        search_term = self.search_var.get().strip().lower()
        filter_term = self.filter_var.get().strip().lower()
        
        visible_count = 0
        
        for btn in self.folder_buttons.values():
            text = btn.cget("text").lower()
            matches_search = not search_term or search_term in text
            matches_filter = not filter_term or filter_term in text
            
            if matches_search and matches_filter:
                btn.grid()
                visible_count += 1
            else:
                btn.grid_remove()
        
        # Show/hide no results message
        if visible_count == 0 and (search_term or filter_term):
            self.no_results_label.pack(fill="x", pady=20)
        else:
            self.no_results_label.pack_forget()
        
        # Show/hide clear button
        if search_term or filter_term:
            self.clear_search_btn.pack(side="right", padx=(5,0))
        else:
            self.clear_search_btn.pack_forget()

    def clear_search(self) -> None:
        """Clear search and filter fields"""
        self.search_var.set("")
        self.filter_var.set("")
        self._update_search_results()
        self.search_entry.focus()
        self.status_cb("Search cleared")

    def show_drop_zone(self, show: bool) -> None:
        """Show or hide the drop zone indicator"""
        if show:
            self.drop_zone.pack(fill="x", pady=5)
        else:
            self.drop_zone.pack_forget()

    def _on_folder_hover(self, event):
        """Enhanced highlight folder on hover during drag"""
        widget = event.widget
        if hasattr(self.master, 'drag_controller') and hasattr(self.master.drag_controller, 'drag_data'):
            widget.configure(
                highlightbackground=get_color("accent", "#B4A7D6"),
                highlightthickness=2,
                relief="solid"
            )

            # Show drop zone more prominently
            self.drop_zone.configure(
                height=4,
                bg=get_color("accent_dark", "#9585C2")
            )
            self.drop_zone.pack(fill='x', pady=2)

    def _on_folder_leave(self, event):
        """Remove highlight when leaving folder"""
        widget = event.widget
        widget.configure(
            highlightthickness=0,
            relief="flat"
        )

        # Reset drop zone
        self.drop_zone.configure(
            height=2,
            bg=get_color("accent", "#B4A7D6")
        )