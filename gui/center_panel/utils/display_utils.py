# gui/center_panel/display_utils.py
import tkinter as tk
from typing import Tuple
from PIL import Image

class DisplayUtils:
    """
    Shared display functionality for both single and grid views.
    Handles common operations like zoom calculations and panning.
    """
    
    @staticmethod
    def calculate_display_size(
        original_size: Tuple[int, int],
        canvas_size: Tuple[int, int],
        zoom_level: float,
        view_mode: str = "fit"
    ) -> Tuple[int, int]:
        """
        Calculate display dimensions based on view mode and zoom.
        
        Args:
            original_size: (width, height) of original image
            canvas_size: (width, height) of display canvas
            zoom_level: Current zoom multiplier
            view_mode: Either "fit" or "actual"
            
        Returns:
            Tuple of (width, height) for displayed image
        """
        img_width, img_height = original_size
        canvas_width, canvas_height = canvas_size
        
        if view_mode == "fit":
            ratio = min(
                canvas_width / img_width,
                canvas_height / img_height
            )
            return (
                int(img_width * ratio * zoom_level),
                int(img_height * ratio * zoom_level)
            )
        else:  # actual size
            return (
                int(img_width * zoom_level),
                int(img_height * zoom_level)
            )

    @staticmethod
    def center_image(
        canvas: tk.Canvas,
        canvas_item: int,
        img_width: int,
        img_height: int
    ):
        """
        Center an image on the canvas with bounds checking.
        
        Args:
            canvas: The canvas widget
            canvas_item: The canvas item ID
            img_width: Width of the image
            img_height: Height of the image
        """
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        x = max((canvas_width - img_width) // 2, 0)
        y = max((canvas_height - img_height) // 2, 0)
        
        canvas.coords(canvas_item, x, y)