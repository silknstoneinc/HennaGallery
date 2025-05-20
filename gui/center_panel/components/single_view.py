import tkinter as tk
from tkinter import ttk
from typing import Dict
from pathlib import Path
from PIL import Image, ImageTk

from config import get_color
from .draggable_info import DraggableInfo
from utils.image_utils import validate_image_file, create_image_preview
from gui.styles import COLORS, FONTS
#from tkintertooltip import Hovertip  # Requires package: pip install tkinter-tooltip

class SingleView(tk.Frame):
    """Handles single image view functionality."""
    
    def __init__(self, parent, controller):
        super().__init__(parent, bg=get_color("background", "#F9F7F4"))
        self.controller = controller
        self._init_ui()
        self._setup_bindings()
        
    def _init_ui(self):
        """Initialize UI components with original dimensions and layout"""
        # Main canvas with original dimensions
        self.canvas = tk.Canvas(
            self,
            bg=get_color("background_dark", "#EDEAE4"),
            highlightthickness=0,
            width=700,  # Original width
            height=700,  # Original height
            confine=True
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Image reference
        self.canvas_image = self.canvas.create_image(0, 0, anchor="nw", tags="image")
        
        # Navigation controls frame (matches original layout)
        self.nav_frame = tk.Frame(
        self,
        bg=get_color("background", "#F9F7F4")
        )
        self.nav_frame.pack(fill="x", pady=(0, 5))
        
        # Navigation buttons (centered in nav_frame)
        self.nav_buttons_frame = tk.Frame(
            self.nav_frame,
            bg=get_color("background", "#F9F7F4")
        )
        self.nav_buttons_frame.pack(expand=True)
        
        # Add navigation buttons (matches original)
        self.prev_btn = ttk.Button(
            self.nav_buttons_frame,
            text="◄ Previous",
            command=self.controller.show_previous_image,
            style="Nav.TButton"
        )
        self.prev_btn.pack(side="left", padx=5)
        
        self.image_count = tk.StringVar(value="Image 0 of 0")
        self.count_label = tk.Label(
            self.nav_buttons_frame,
            textvariable=self.image_count,
            font=("Georgia", 10),
            fg=get_color("dark", "#5A5A5A"),
            bg=get_color("background", "#F9F7F4")
        )
        self.count_label.pack(side="left", padx=10)
        
        self.next_btn = ttk.Button(
            self.nav_buttons_frame,
            text="Next ►",
            command=self.controller.show_next_image,
            style="Nav.TButton"
        )
        self.next_btn.pack(side="left", padx=5)
        
        # Info overlay
        self._setup_info_overlay()
    
    def _setup_info_overlay(self):
        """Set up draggable info panel with hover effects."""
        self.info_frame = DraggableInfo(
            self.canvas,
            bg=COLORS["dark"],
            padx=10,
            pady=5,
            relief="raised",
            borderwidth=1,
            highlightbackground=COLORS["accent_dark"]
        )
        
        # Main info text (truncated)
        self.info_text = tk.StringVar()
        self.info_label = tk.Label(
            self.info_frame,
            textvariable=self.info_text,
            font=FONTS["small"],
            fg="white",
            bg=COLORS["dark"],
            justify="left",
            cursor="hand2"
        )
        self.info_label.pack()
        
        # Create the canvas window for the info frame
        self.info_window = self.canvas.create_window(
            20, 20,  # x, y position
            anchor="nw",
            window=self.info_frame,
            tags="info_frame"
        )
        
        # Bring to front to ensure visibility
        self.canvas.tag_raise("info_frame")
        
        # Tooltip for full info
        self.full_info_tooltip = None
        self.info_label.bind("<Enter>", self._show_full_info)
        self.info_label.bind("<Leave>", self._hide_full_info)
        
        # Force update
        self.info_frame.update_idletasks()

    def _show_full_info(self, event):
        """Show full information on hover."""
        if hasattr(self, 'full_info_text') and self.full_info_text:
            x, y = self.info_frame.winfo_rootx(), self.info_frame.winfo_rooty()
            self.full_info_tooltip = tk.Toplevel()
            self.full_info_tooltip.wm_overrideredirect(True)
            self.full_info_tooltip.wm_geometry(f"+{x + self.info_frame.winfo_width() + 5}+{y}")
            
            label = tk.Label(
                self.full_info_tooltip,
                text=self.full_info_text,
                font=FONTS["small"],
                bg=COLORS["background_light"],
                fg=COLORS["dark"],
                justify="left",
                relief="solid",
                borderwidth=1,
                padx=10,
                pady=5,
                wraplength=300
            )
            label.pack()

    def _hide_full_info(self, event):
        """Hide the full info tooltip."""
        if self.full_info_tooltip:
            self.full_info_tooltip.destroy()
            self.full_info_tooltip = None


    def _setup_bindings(self):
        """Configure only pan/zoom bindings for single view"""
        # Zoom bindings
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", lambda e: self.controller.zoom_in())
        self.canvas.bind("<Button-5>", lambda e: self.controller.zoom_out())

        # Pan bindings
        self.canvas.bind("<ButtonPress-1>", self._start_pan)
        self.canvas.bind("<B1-Motion>", self._pan_image)
        self.canvas.bind("<ButtonRelease-1>", self._end_pan)
        self.canvas.bind("<Configure>", lambda e: self.display_image())

    def display_image(self):
        """Display the current image with proper zoom."""
        if not self.controller or not hasattr(self.controller, 'original_image') or not self.controller.original_image:
            self.canvas.itemconfig(self.canvas_image, image='')  # Clear canvas
            return
            
        try:
            # Get canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            img_width, img_height = self.controller.original_image.size
            
            ratio = min(
                canvas_width / img_width,
                canvas_height / img_height
            )
            display_size = (
                int(img_width * ratio * self.controller.zoom_level),
                int(img_height * ratio * self.controller.zoom_level)
            )
            
            # Create and display resized image
            resized_img = self.controller.original_image.resize(display_size, Image.Resampling.LANCZOS)
            self.controller.current_image = ImageTk.PhotoImage(resized_img)
            self.controller._image_references.append(self.controller.current_image)
            
            self.canvas.itemconfig(self.canvas_image, image=self.controller.current_image)
            self._center_image()
            
        except Exception as e:
            self.controller.status_cb(f"Display error: {str(e)}")
            self.canvas.itemconfig(self.canvas_image, image='')  # Clear canvas on error

    def _center_image(self):
        """Center the image on canvas."""
        if not self.controller.current_image:
            return
            
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_width = self.controller.current_image.width()
        img_height = self.controller.current_image.height()
        
        x = max((canvas_width - img_width) // 2, 0)
        y = max((canvas_height - img_height) // 2, 0)
        self.canvas.coords(self.canvas_image, x, y)

    def _on_mousewheel(self, event):
        """Handle mouse wheel zoom."""
        if event.delta > 0 or event.num == 4:
            self.controller.zoom_in()
        else:
            self.controller.zoom_out()

    def _start_pan(self, event):
        """Begin panning with proper initialization"""
        self.controller.pan_start_x = event.x
        self.controller.pan_start_y = event.y
        self.canvas.config(cursor="fleur")

    def _pan_image(self, event):
        """Handle panning with null checks"""
        if not hasattr(self.controller, 'pan_start_x') or self.controller.pan_start_x is None:
            return
            
        dx = event.x - self.controller.pan_start_x
        dy = event.y - self.controller.pan_start_y
        
        self.canvas.move("image", dx, dy)
        self.controller.pan_start_x = event.x
        self.controller.pan_start_y = event.y

    def _end_pan(self, event):
        """Clean up panning state"""
        if hasattr(self.controller, 'pan_start_x'):
            del self.controller.pan_start_x
            del self.controller.pan_start_y
        self.canvas.config(cursor="")