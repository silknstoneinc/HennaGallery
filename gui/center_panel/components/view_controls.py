import tkinter as tk
from tkinter import ttk
from config import get_color

class ViewControls(tk.Frame):
    """Handles view mode switching."""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._init_ui()
        
    def _init_ui(self):
        """Initialize view controls."""
        self.view_mode = tk.StringVar(value="single")
        
        ttk.Label(self, text="", width=5).pack(side="right")
        
        self.single_view_btn = ttk.Radiobutton(
            self,
            text="Single View",
            variable=self.view_mode,
            value="single",
            command=lambda: self.controller.show_view("single"),
            style="Toolbutton"
        )
        self.single_view_btn.pack(side="right", padx=5)
        
        self.grid_view_btn = ttk.Radiobutton(
            self,
            text="Grid View",
            variable=self.view_mode,
            value="grid",
            command=lambda: self.controller.show_view("grid"),
            style="Toolbutton"
        )
        self.grid_view_btn.pack(side="right", padx=5)