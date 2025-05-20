import tkinter as tk
from tkinter import ttk
from pathlib import Path
from PIL import Image, ImageTk, ImageOps

class ThumbnailWidget(tk.Frame):
    def __init__(self, parent, image_data, folder_name, select_callback, image_path=None, width=220, height=165, *args, **kwargs):
        # Validate and set dimensions
        self.width = max(width, 150)
        self.height = max(height, 120)
        kwargs['width'] = self.width
        kwargs['height'] = self.height
        
        super().__init__(parent, *args, **kwargs)
        self.image_data = image_data
        self.folder_name = folder_name
        self.select_callback = select_callback
        self.image_path = image_path
        self.image_index = 0
        self._image_ref = None  # Prevents garbage collection
        self.original_image = None
        self.hover_state = False
        self.zoom_level = 1.0
        self.drag_handler = None  # Will be set by parent
        
        # Configure base styling
        self.configure(
            bg="#FFFFFF",
            highlightthickness=0,
            bd=0,
            padx=0,
            pady=0
        )
        
        # Create shadow effect (hidden by default)
        self.shadow = tk.Frame(
            parent,
            bg="#E0E0E0",
            relief='flat'
        )
        self.shadow.place(
            in_=self,
            x=2,
            y=2,
            relwidth=1,
            relheight=1
        )
        self.shadow.lower(self)
        
        # Main content container
        self.content_frame = tk.Frame(self, bg="#FFFFFF")
        self.content_frame.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Image display area with 2px padding
        self.img_frame = tk.Frame(
            self.content_frame,
            bg="#FFFFFF",
            highlightthickness=0,
            padx=2,
            pady=2
        )
        self.img_frame.pack(fill='both', expand=True)
        
        # Image label - will contain the actual image
        self.thumbnail_label = tk.Label(
            self.img_frame,
            bg="#FFFFFF",
            bd=0
        )
        self.thumbnail_label.pack(fill='both', expand=True)
        
        # Caption area
        self.caption_var = tk.StringVar()
        self.caption_label = tk.Label(
            self.content_frame,
            textvariable=self.caption_var,
            font=("Segoe UI", 9),
            fg="#333333",
            bg="#FFFFFF",
            wraplength=self.width-20,
            justify="center",
            pady=3
        )
        self.caption_label.pack(fill='x')
        
        # Set up interactions
        self._setup_bindings()
        
        # Load image immediately if path provided
        if self.image_path:
            self.load_image(Path(self.image_path))
        else:
            self._show_placeholder()

    def _show_placeholder(self):
        """Display placeholder when no image available"""
        self.thumbnail_label.config(
            text="No Image",
            fg="#CCCCCC",
            font=("Segoe UI", 10)
        )
        self._update_caption()

    def _setup_bindings(self):
        """More robust binding setup"""
        # Clear existing bindings for all relevant widgets
        widgets = [self, self.content_frame, self.img_frame, self.thumbnail_label]
        
        for widget in widgets:
            widget.unbind("<Enter>")
            widget.unbind("<Leave>")
            widget.unbind("<ButtonPress-1>")
            widget.unbind("<B1-Motion>")
            widget.unbind("<ButtonRelease-1>")
            
            # Add new bindings
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.bind("<ButtonPress-1>", self._on_press)
            widget.bind("<B1-Motion>", self._on_drag)
            widget.bind("<ButtonRelease-1>", self._on_release)
        
        print(f"♻️ Bindings set for thumbnail {self.image_index}")

    def load_image(self, image_path: Path):
        """Load and display image with perfect sizing"""
        try:
            # Open and validate image
            self.original_image = Image.open(image_path)
            
            # Calculate display dimensions (90% of container width)
            display_width = int(self.width * 0.90)  # Changed from 0.95 to 0.90
            display_height = int((self.height - 30) * 0.90)  # Changed from 0.95 to 0.90
            
            # Create thumbnail that fills width while maintaining aspect ratio
            thumbnail = ImageOps.contain(
                self.original_image,
                (display_width, display_height),
                method=Image.Resampling.LANCZOS
            )
            
            # Create white background and center image
            bg = Image.new('RGB', (display_width, display_height), (255, 255, 255))
            bg.paste(
                thumbnail,
                (
                    (display_width - thumbnail.size[0]) // 2,
                    (display_height - thumbnail.size[1]) // 2
                )
            )
            
            # Critical addition - ensure the image attribute exists
            self._image_ref = ImageTk.PhotoImage(bg)
            self.image = self._image_ref  # This enables drag functionality
            self.thumbnail_label.config(
                image=self._image_ref,
                text=""
            )
            self._update_caption()
            
        except Exception as e:
            print(f"Error loading image {image_path}: {str(e)}")
            self._show_placeholder()

    def _apply_zoom(self, factor):
        """Apply proportional zoom effect to the image"""
        try:
            if not self.original_image:
                return
                
            # Calculate zoomed dimensions (but maintain same container size)
            img_width = int(self.width * 0.90 * factor)  # Changed from 0.95 to 0.90
            img_height = int((self.height - 30) * 0.90 * factor)  # Changed from 0.95 to 0.90
            
            # Create zoomed image (maintain aspect ratio)
            zoomed = self.original_image.resize(
                (img_width, img_height),
                Image.Resampling.LANCZOS
            )
            
            # Create display image (same container size as original)
            display_width = int(self.width * 0.90)  # Changed from 0.95 to 0.90
            display_height = int((self.height - 30) * 0.90)  # Changed from 0.95 to 0.90
            bg = Image.new('RGB', (display_width, display_height), (255, 255, 255))
            bg.paste(
                zoomed,
                (
                    (display_width - zoomed.size[0]) // 2,
                    (display_height - zoomed.size[1]) // 2
                )
            )
            
            self._image_ref = ImageTk.PhotoImage(bg)
            self.thumbnail_label.config(image=self._image_ref)
            
        except Exception as e:
            print(f"Zoom error: {str(e)}")

    def _update_caption(self):
        """Update caption with formatted metadata"""
        parts = []
        if 'url' in self.image_data:
            filename = Path(self.image_data['url']).stem[:15]
            parts.append(f"📄 {filename}{'...' if len(filename) >= 15 else ''}")
        if 'headline' in self.image_data:
            headline = self.image_data['headline'][:15]
            parts.append(f"🏷️ {headline}{'...' if len(headline) >= 15 else ''}")
        self.caption_var.set("\n".join(parts) or "No metadata")

    def _on_enter(self, event):
        """Handle mouse enter with hover effects"""
        self.hover_state = True
        self.config(highlightbackground="#7E57C2", highlightthickness=1)
        self.content_frame.config(bg="#F5F5F5")
        self.img_frame.config(bg="#F5F5F5")
        self.thumbnail_label.config(bg="#F5F5F5")
        self.caption_label.config(bg="#F5F5F5", fg="#7E57C2")
        self.shadow.config(bg="#B0B0B0")
        
        # Apply subtle zoom effect
        if hasattr(self, '_image_ref') and self._image_ref:
            self._apply_zoom(1.05)  # 5% zoom
        return "break"  # Important to prevent event propagation issues

    def _on_leave(self, event):
        """Handle mouse leave - PRECISE FIX"""
        # Handle None event case
        if event is None:
            self.hover_state = False
            # Reset all visual properties
            self.config(highlightbackground="#E0E0E0", highlightthickness=0)
            self.content_frame.config(bg="#FFFFFF")
            self.img_frame.config(bg="#FFFFFF")
            self.thumbnail_label.config(bg="#FFFFFF")
            self.caption_label.config(bg="#FFFFFF", fg="#333333")
            self.shadow.config(bg="#E0E0E0")
            return "break"
        # Get mouse coordinates relative to this widget
        x = event.x - self.winfo_x()
        y = event.y - self.winfo_y()
        
        # Check if mouse is actually outside the widget bounds
        if (x < 0 or y < 0 or 
            x > self.winfo_width() or 
            y > self.winfo_height()):
            
            self.hover_state = False
            # Reset all visual properties
            self.config(highlightbackground="#E0E0E0", highlightthickness=0)
            self.content_frame.config(bg="#FFFFFF")
            self.img_frame.config(bg="#FFFFFF")
            self.thumbnail_label.config(bg="#FFFFFF")
            self.caption_label.config(bg="#FFFFFF", fg="#333333")
            self.shadow.config(bg="#E0E0E0")
            
            # Reset zoom if image exists
            if hasattr(self, '_image_ref') and self._image_ref:
                self._apply_zoom(1.0)
        return "break"
    
    def _on_press(self, event):
        """Handle mouse press - start drag"""
        print(f"🖱️ Press event on thumbnail {self.image_index}")
        self._drag_start = (event.x_root, event.y_root)
        
        if hasattr(self, 'drag_handler') and self.drag_handler:
            print("✓ Drag handler accessible")
            # Create a simple event object with just the needed attributes
            class SimpleEvent:
                def __init__(self, x_root, y_root, widget):
                    self.x_root = x_root
                    self.y_root = y_root
                    self.widget = widget
            
            start_event = SimpleEvent(event.x_root, event.y_root, self)
            self.drag_handler.handle_drag_start(self, start_event)
        else:
            print("❌ No drag handler found")
        
        return "break"

    def _on_drag(self, event):
        """Handle drag motion"""
        if not hasattr(self, '_drag_start') or not hasattr(self, 'drag_handler'):
            return
            
        if hasattr(self, 'drag_handler') and self.drag_handler:
            # Create minimal event object
            class DragEvent:
                def __init__(self, x_root, y_root):
                    self.x_root = x_root
                    self.y_root = y_root
            
            drag_event = DragEvent(event.x_root, event.y_root)
            self.drag_handler.handle_drag(drag_event)
        return "break"

    def _on_release(self, event):
        """Handle drag completion"""
        if hasattr(self, '_drag_start'):
            del self._drag_start
            
        if hasattr(self, 'drag_handler') and self.drag_handler:
            self.drag_handler.handle_drop(event)
        return "break"

    def _on_double_click(self, event):
        if callable(self.select_callback):
            self.select_callback(self.image_index)
        return "break"
    
    def handle_drop(self, event):
        """Finalize drop operation with proper cleanup"""
        try:
            result = False
            if self.drag_data and self.current_target:
                if hasattr(self.current_target, 'folder_path'):
                    result = self._handle_folder_move()
                elif hasattr(self.current_target, 'image_index'):
                    result = self._handle_reorder()
                
                # Visual feedback
                if result:
                    self._show_drop_success()
                else:
                    self._show_drop_failure()
                    
            return result
        finally:
            self.cleanup_drag()

    def _show_drop_success(self):
        """Visual feedback for successful drop"""
        if self.current_target and self.current_target.winfo_exists():
            self.current_target.config(bg='#E8F5E9')  # Light green
            self.current_target.after(300, lambda: 
                self.current_target.config(bg='#FFFFFF' if hasattr(self.current_target, 'image_index') 
                                        else self.current_target.cget('bg')))

    def _show_drop_failure(self):
        """Visual feedback for failed drop"""
        if self.current_target and self.current_target.winfo_exists():
            self.current_target.config(bg='#FFEBEE')  # Light red
            self.current_target.after(300, lambda: 
                self.current_target.config(bg='#FFFFFF' if hasattr(self.current_target, 'image_index') 
                                        else self.current_target.cget('bg')))

    def cleanup_drag(self):
        """Clean up all drag resources"""
        self._destroy_ghost()
        self._clear_highlight()
        if hasattr(self, 'drag_data'):
            # Reset the dragged widget's appearance
            if hasattr(self.drag_data['widget'], 'winfo_exists') and self.drag_data['widget'].winfo_exists():
                self.drag_data['widget']._on_leave(None)  # Force reset appearance
            self.drag_data = {}