"""
gui/drag_handlers/shared_utils.py

Shared Utilities - Common helper functions for drag operations

Responsibilities:
- Finding draggable widgets in hierarchy
- Coordinate transformations
- Common validation checks

Used across all drag handlers.
"""

import tkinter as tk
from typing import Optional

def find_draggable_widget(widget: tk.Widget) -> Optional[tk.Widget]:
    """
    Find the nearest draggable parent widget.
    
    Args:
        widget: Starting widget
        
    Returns:
        First parent with image_index attribute or None
    """
    while widget and not hasattr(widget, "image_index"):
        widget = widget.master
    return widget

def widget_contains(widget: tk.Widget, x: int, y: int) -> bool:
    """
    Check if coordinates are within widget bounds.
    
    Args:
        widget: Target widget
        x,y: Root coordinates
        
    Returns:
        True if coordinates are inside widget
    """
    return (widget.winfo_rootx() <= x <= widget.winfo_rootx() + widget.winfo_width() and
            widget.winfo_rooty() <= y <= widget.winfo_rooty() + widget.winfo_height())