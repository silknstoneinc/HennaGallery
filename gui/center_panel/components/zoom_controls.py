import tkinter as tk
from tkinter import ttk
from config import get_color

class ZoomControls(tk.Frame):
    """Handles zoom functionality."""
    
    def __init__(self, parent, controller):
        super().__init__(parent, bg=get_color("background", "#F9F7F4"))
        self.controller = controller
        self._init_ui()
        
    def _init_ui(self):
        """Initialize zoom controls."""
        self.zoom_label = tk.Label(
            self,
            text="Zoom:",
            font=("Georgia", 10),
            bg=get_color("background", "#F9F7F4"),
            fg=get_color("dark", "#5A5A5A")
        )
        self.zoom_label.pack(side="left")
        
        self.zoom_out_btn = ttk.Button(
            self,
            text="-",
            width=3,
            command=self.zoom_out,
            style="Secondary.TButton"
        )
        self.zoom_out_btn.pack(side="left", padx=5)
        
        # Zoom reset button
        self.zoom_reset_btn = ttk.Button(
            self,
            text="100%",
            width=5,
            command=self.zoom_reset,
            style="Secondary.TButton"
        )
        self.zoom_reset_btn.pack(side="left")
        
        # Zoom in button
        self.zoom_in_btn = ttk.Button(
            self,
            text="+",
            width=3,
            command=self.zoom_in,
            style="Secondary.TButton"
        )
        self.zoom_in_btn.pack(side="left", padx=5)
        
        # Bind keyboard shortcuts
        self.controller.bind_all("<Control-plus>", lambda e: self.zoom_in())
        self.controller.bind_all("<Control-minus>", lambda e: self.zoom_out())
        self.controller.bind_all("<Control-0>", lambda e: self.zoom_reset())

    def zoom_in(self, event=None):
        """Zoom in with bounds checking."""
        if self.controller.zoom_level < self.controller.max_zoom:
            self.controller.zoom_level = round(min(
                self.controller.zoom_level + self.controller.zoom_step,
                self.controller.max_zoom
            ), 2)
            self._update_display()
            #self.controller.update_display()
            #self.controller.status_cb(f"Zoom: {int(self.controller.zoom_level * 100)}%")

    def zoom_out(self, event=None):
        """Zoom out with bounds checking."""
        if self.controller.zoom_level > self.controller.min_zoom:
            self.controller.zoom_level = round(max(
                self.controller.zoom_level - self.controller.zoom_step,
                self.controller.min_zoom
            ), 2)
            self._update_display()
            #self.controller.update_display()
            #self.controller.status_cb(f"Zoom: {int(self.controller.zoom_level * 100)}%")

    def zoom_reset(self, event=None):
        """Reset zoom to 100%."""
        self.controller.zoom_level = 1.0
        self._update_display()
        self.controller.status_cb("Zoom reset to 100%")
        #self.controller.update_display()
        #self.controller.status_cb("Zoom reset to 100%")

    def _update_display(self):
        """Update display through controller"""
        self.controller.status_cb(f"Zoom: {int(self.controller.zoom_level * 100)}%")
        if self.controller.current_view == "single":
            self.controller.single_view.display_image()