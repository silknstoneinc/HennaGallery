# gui/center_panel/draggable_info.py
import tkinter as tk
from config import get_color

class DraggableInfo(tk.Frame):
    """Enhanced movable info panel with drag handle"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(
            bg=get_color("dark", "#5A5A5A"),
            padx=10,
            pady=5,
            relief="flat"
        )
        self._drag_data = {"x": 0, "y": 0}
        
        # Add drag handle
        self.handle = tk.Frame(self, height=5, bg=get_color("accent", "#B4A7D6"))
        self.handle.pack(fill="x")
        self.handle.bind("<ButtonPress-1>", self.start_move)
        self.handle.bind("<B1-Motion>", self.on_move)
        
        # Info content
        self.info_text = tk.StringVar()
        self.info_label = tk.Label(
            self,
            textvariable=self.info_text,
            font=("Georgia", 10),
            fg="white",
            bg=get_color("dark", "#5A5A5A"),
            justify="left"
        )
        self.info_label.pack()

    def start_move(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self.lift()

    def on_move(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.winfo_x() + dx
        y = self.winfo_y() + dy
        self.place(x=x, y=y)
        self.info_text = tk.StringVar()
        self.info_label = tk.Label(
            self,
            textvariable=self.info_text,
            font=("Georgia", 10),
            fg="white",
            bg=get_color("dark", "#5A5A5A"),
            justify="left"
        )
        self.info_label.pack()

    def start_move(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self.lift()

    def on_move(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.winfo_x() + dx
        y = self.winfo_y() + dy
        self.place(x=x, y=y)