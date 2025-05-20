"""
gui/drag_handlers/drag_handler.py

Consolidated Drag Handler - Handles both reordering and folder moves
"""

import tkinter as tk
from typing import Optional, Callable, Dict, Any, Tuple
from pathlib import Path

class DragHandler:
    def __init__(self, main_window, config=None):
        self.main_window = main_window
        self.config = config or {
            'ghost_opacity': 0.8,
            'valid_drop_color': "#B4A7D6",
            'invalid_drop_color': "#FF9999",
            #'scroll_speed': 10,
            'drag_threshold': 5
        }
        
        # Drag state
        self.drag_data = {}
        self.current_target = None
        self.drag_ghost = None
        self.drop_indicator = None
        self.drop_position = None
        self.last_position = 0
        
        # UI references (set later via configure)
        self.source_view = None
        self.folders_panel = None
    
    def configure(self, source_view, folders_panel):
        """Set up UI component references"""
        self.source_view = source_view
        self.folders_panel = folders_panel
    
    def handle_drag_start(self, widget, event):
        print(f"Drag starting on thumbnail {getattr(widget, 'image_index', '?')}")

        # Verify critical attributes exist
        if not hasattr(widget, 'image_index'):
            print("❌ Missing image_index - cannot drag")
            return False
            
        if not hasattr(widget, 'image'):
            print("❌ Missing image attribute - check load_image()")
            return False
            
        self.drag_data = {
            'widget': widget,
            'index': widget.image_index,
            'start_x': event.x_root,
            'start_y': event.y_root,
            'threshold_passed': False  # Start with False for threshold checking
        }
        
        # Create ghost immediately but keep it hidden until threshold passed
        self._create_ghost_image(widget, event)
        #if hasattr(self, 'drag_ghost') and self.drag_ghost:
        #    self.drag_ghost.withdraw()  # Hide initially    
        return True

    def handle_drag(self, event):
        """Handle drag motion with threshold checking"""
        if not self.drag_data:
            return
            
        # Check if we've passed the threshold
        if not self.drag_data['threshold_passed']:
            dx = abs(event.x_root - self.drag_data['start_x'])
            dy = abs(event.y_root - self.drag_data['start_y'])
            
            if dx < self.config['drag_threshold'] and dy < self.config['drag_threshold']:
                return
                
            self.drag_data['threshold_passed'] = True
            if hasattr(self, 'drag_ghost') and self.drag_ghost:
                self.drag_ghost.deiconify()  # Show when threshold passed
        
        # Only proceed with visual feedback if threshold passed
        if self.drag_data['threshold_passed']:
            self._update_ghost_position(event)
            target = self._find_drop_target(event)
            self._update_target_highlight(target, event)
    
    def handle_drop(self, event):
        """Finalize drop operation"""
        if not self.drag_data:
            return False
            
        try:
            if self.current_target:
                if hasattr(self.current_target, 'folder_path'):
                    return self._handle_folder_move()
                elif hasattr(self.current_target, 'image_index'):
                    return self._handle_reorder()
            return False
        finally:
            self.cleanup_drag()

    def _handle_reorder(self):
        """Handle reordering of images"""
        from_idx = self.drag_data['index']
        to_idx = self.current_target.image_index
        
        # Calculate final position considering drop position
        if self.drop_position == "after":
            to_idx = min(to_idx + 1, len(self.main_window.images) - 1)
        elif self.drop_position == "before":
            to_idx = max(0, to_idx)
        
        # Don't reorder if position didn't change
        if from_idx == to_idx:
            return False
            
        # Call main window's reorder method
        self.main_window.reorder_images(from_idx, to_idx)
        return True
    
    def _handle_folder_move(self):
        """Handle moving to different folder"""
        folder_path = getattr(self.current_target, 'folder_path', None)
        current_folder = getattr(self.main_window, 'current_folder', None)
        
        if folder_path and folder_path != current_folder:
            # Get image index from drag data
            img_index = self.drag_data['index']
            
            # Call main window's move method
            self.main_window.move_image_to_folder(img_index, folder_path)
            return True
        return False
    
    def _create_ghost_image(self, widget, event):
        """Optimized ghost creation - NO DUPLICATION"""
        if not hasattr(widget, 'image') or not widget.image:
            return
            
        self._destroy_ghost()  # Clean up any existing ghost
        
        # Create minimal ghost window
        self.drag_ghost = tk.Toplevel(widget.winfo_toplevel())
        self.drag_ghost.wm_overrideredirect(True)
        self.drag_ghost.wm_attributes("-alpha", 0.7) # Set opacity self.config['ghost_opacity']
        self.drag_ghost.wm_attributes("-topmost", True)
        
        # Add drop shadow effect
        shadow = tk.Frame(
            self.drag_ghost,
            bg="#888888",
            bd=0
        )
        shadow.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)

        # Main ghost frame
        ghost_frame = tk.Frame(
            self.drag_ghost,
            bg="white",
            bd=0
        )
        ghost_frame.pack(fill="both", expand=True, padx=2, pady=2)
        

        # Keep reference to the image
        self._ghost_image_ref = widget.image
         
        # Create label with image
        tk.Label(
            ghost_frame,
            #self.drag_ghost,
            image=self._ghost_image_ref,
            border=0,
            highlightthickness=2,
            highlightbackground="#7E57C2"
        ).pack()
        
        self._position_ghost(event)
        
        # Use a label for better performance than canvas
        #ghost_label = tk.Label(self.drag_ghost, image=widget.image, bd=0)
        #ghost_label.pack()
        
        # Add border directly to label
        #ghost_label.config(
        #    highlightbackground="#7E57C2",
        #    highlightthickness=2,
        #    relief='solid'
        #)
        #self._position_ghost(event)

    def _position_ghost(self, event):
        """Position the ghost image relative to cursor"""
        if not hasattr(self, 'drag_ghost') or not self.drag_ghost:
            return
            
        # Calculate position with offset
        x_pos = event.x_root + 15
        y_pos = event.y_root + 15
        
        # Keep ghost on screen
        screen_width = self.drag_ghost.winfo_screenwidth()
        screen_height = self.drag_ghost.winfo_screenheight()
        ghost_width = self.drag_ghost.winfo_reqwidth()
        ghost_height = self.drag_ghost.winfo_reqheight()
        
        x_pos = min(x_pos, screen_width - ghost_width - 5)
        y_pos = min(y_pos, screen_height - ghost_height - 5) 
        
        self.drag_ghost.geometry(f"+{int(x_pos)}+{int(y_pos)}")
        self.drag_ghost.update_idletasks()  # Ensure position is updated immediately
        self.drag_ghost.lift()  # Bring ghost to front

    def _update_ghost_position(self, event):
        """Update ghost image position during drag"""
        if self.drag_ghost:
            self._position_ghost(event)

    def _handle_auto_scroll(self, event):
        """Auto-scroll when near edges"""
        if not hasattr(self, 'source_view') or not self.source_view:
            return
            
        canvas = self.source_view.grid_canvas
        scroll_region = canvas.bbox("all")
        if not scroll_region:
            return
            
        # Calculate scroll margins (10% of canvas height)
        scroll_margin = canvas.winfo_height() * 0.1
        y = event.y_root - canvas.winfo_rooty()
        
        if y < scroll_margin:
            canvas.yview_scroll(-1, "units")
        elif y > canvas.winfo_height() - scroll_margin:
            canvas.yview_scroll(1, "units")

    def _find_drop_target(self, event):
        """Find valid drop target under cursor"""
        # Get the actual widget under cursor using the root window
        root = self.main_window.root  # Assuming main_window has a root attribute
        widget = root.winfo_containing(event.x_root, event.y_root)
        
        # Check for folder target first
        while widget and not hasattr(widget, 'folder_path'):
            widget = widget.master
        
        if widget and hasattr(widget, 'folder_path'):
            return widget
            
        # Check for grid reorder target
        widget = root.winfo_containing(event.x_root, event.y_root)
        while widget and not hasattr(widget, 'image_index'):
            widget = widget.master
        
        return widget if (widget and hasattr(widget, 'image_index')) else None

    def _update_target_highlight(self, target, event=None):
        """Update visual feedback based on target"""
        self.current_target = target
        
        if not target:
            self._clear_all_highlights()
            return
            
        if hasattr(target, 'folder_path'):
            # Folder target - check if valid
            is_valid = target.folder_path != getattr(self.main_window, 'current_folder', None)
            self._highlight_folder_target(target, is_valid)
        elif hasattr(target, 'image_index') and event:
            # Grid reorder target - more precise position calculation
            widget_height = target.winfo_height()
            rel_y = (event.y_root - target.winfo_rooty()) / widget_height
            
            # Use 40% threshold for more intuitive dropping
            if rel_y < 0.4:
                self.drop_position = "before"
            elif rel_y > 0.6:
                self.drop_position = "after"
            else:
                self.drop_position = "on"
                
            self._highlight_reorder_target(target)

    def cleanup_drag(self):
        """Clean up all drag resources"""
        # Remove duplicate method calls
        if hasattr(self, 'drag_ghost') and self.drag_ghost:
            try:
                self.drag_ghost.destroy()
            except:
                pass
            self.drag_ghost = None
        
        # Clear drop indicator if it exists
        if hasattr(self, 'drop_indicator') and self.drop_indicator:
            try:
                self.drop_indicator.place_forget()
                self.drop_indicator.destroy()
            except:
                pass
            self.drop_indicator = None
        
        # Clear target highlights
        if hasattr(self, 'current_target') and self.current_target and self.current_target.winfo_exists():
            if hasattr(self.current_target, '_on_leave'):
                self.current_target._on_leave(None)
            else:
                self.current_target.config(
                    highlightbackground=self.current_target.cget('bg'),
                    highlightthickness=0,
                    relief="flat"
                )
        
        # Reset state variables
        self.current_target = None
        self.drop_position = None
        
        # Clean up drag data
        if hasattr(self, 'drag_data'):
            # Reset the dragged widget's appearance
            if (hasattr(self.drag_data['widget'], 'winfo_exists') and 
                self.drag_data['widget'].winfo_exists()):
                self.drag_data['widget']._on_leave(None)
            self.drag_data = {}

    def _clear_all_highlights(self):
        """Clear all highlighting without recursion"""
        # Clear drop indicator if it exists
        if self.drop_indicator:
            try:
                self.drop_indicator.place_forget()
                self.drop_indicator.destroy()
            except:
                pass
            self.drop_indicator = None
        
        # Clear target highlights
        if self.current_target and hasattr(self.current_target, 'winfo_exists') and self.current_target.winfo_exists():
            if hasattr(self.current_target, '_on_leave'):
                self.current_target._on_leave(None)
            else:
                self.current_target.config(
                    highlightbackground=self.current_target.cget('bg'),
                    highlightthickness=0,
                    relief="flat"
                )
        self.current_target = None
        self.drop_position = None
    
    def _update_ghost_position(self, event):
        """Update ghost image position during drag"""
        if self.drag_ghost:
            self._position_ghost(event)
    
    def _highlight_folder_target(self, target, is_valid):
        """Visual feedback for folder targets"""
        color = self.config['valid_drop_color'] if is_valid else self.config['invalid_drop_color']
        target.configure(
            highlightbackground=color,
            highlightthickness=2,
            relief="solid"
        )
    
    def _highlight_reorder_target(self, target):
        """Visual feedback for reorder targets"""
        self._clear_drop_indicator()
        
        y_pos = target.winfo_y()
        if self.drop_position == "after":
            y_pos += target.winfo_height()
        
        self.drop_indicator = tk.Frame(
            target.master,
            height=4,
            bg=self.config['valid_drop_color'],
            highlightthickness=0
        )
        self.drop_indicator.place(
            x=target.winfo_x(),
            y=y_pos-2,
            width=target.winfo_width()
        )

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

    def _destroy_ghost(self):
        """Clean up ghost image"""
        if hasattr(self, 'drag_ghost') and self.drag_ghost:
            try:
                self.drag_ghost.destroy()
            except:
                pass
            self.drag_ghost = None

    def _clear_drop_indicator(self):
        """Remove drop indicator"""
        if hasattr(self, 'drop_indicator') and self.drop_indicator:
            try:
                self.drop_indicator.place_forget()
                self.drop_indicator.destroy()
            except:
                pass
            self.drop_indicator = None