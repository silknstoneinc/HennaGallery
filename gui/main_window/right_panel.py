"""
Enhanced right panel module for Henna Gallery Editor.
Handles metadata editing with thread-safe undo/redo support and advanced tag management.
Complete implementation with improved button layout for better visibility.

Changes made:
1. Fixed initialization order to prevent AttributeError
2. Enhanced featured checkbox visibility
3. Added debug prints for troubleshooting
"""

import tkinter as tk
import threading
from tkinter import ttk, messagebox
from typing import Dict, Callable, Optional, List, Any
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageTk

from gui.styles import COLORS, FONTS
from utils.file_utils import slugify

class HistoryManager:
    """Track changes for undo/redo functionality with thread safety."""
    def __init__(self, max_steps: int = 50):
        self.undo_stack: List[Dict] = []
        self.redo_stack: List[Dict] = []
        self.max_steps = max_steps
        self._lock = threading.Lock()

    def record_change(self, field: str, old_value: Any, new_value: Any) -> None:
        """Record a change to the history with thread safety."""
        with self._lock:
            self.undo_stack.append({
                'field': field,
                'old_value': old_value,
                'new_value': new_value,
                'timestamp': datetime.now()
            })
            if len(self.undo_stack) > self.max_steps:
                self.undo_stack.pop(0)
            self.redo_stack.clear()

    def get_undo_change(self) -> Optional[Dict]:
        """Get the next undo change if available with thread safety."""
        with self._lock:
            return self.undo_stack.pop() if self.undo_stack else None

    def get_redo_change(self) -> Optional[Dict]:
        """Get the next redo change if available with thread safety."""
        with self._lock:
            return self.redo_stack.pop() if self.redo_stack else None

class RightPanel(tk.Frame):
    """
    Enhanced right panel with:
    - Full metadata editing
    - Thread-safe undo/redo support
    - Advanced tag management
    - Export functionality
    - Improved button layout
    - Fixed featured checkbox visibility
    """
    DEFAULT_EXPORT_SETTINGS = {
        "format": "webp",
        "quality": 85,
        "resize_enabled": True,
        "max_width": 1200,
        "max_height": 1200
    }

    def __init__(
        self,
        parent: tk.Widget,
        status_callback: Callable[[str], None],
        config: Dict,
        *args, **kwargs
    ):
        super().__init__(parent, *args, **kwargs)
        self.configure(
            bg=COLORS["background"],
            width=350,
            padx=15,
            pady=15
        )
        self.pack_propagate(False)
        
        self.status_cb = status_callback
        self.config = config
        self.current_data: Optional[Dict] = None
        self.history = HistoryManager()
        self.tag_suggestions: List[str] = []
        
        # Initialize export settings
        self.export_settings = {
            **self.DEFAULT_EXPORT_SETTINGS,
            **self.config.get("export_settings", {})
        }
        
        # Create all widgets first
        self.create_widgets()
        
        # Then load suggestions (safe now that widgets exist)
        self.load_tag_suggestions()
        
        # Finally set up bindings
        self.setup_bindings()

        print("RightPanel initialized successfully")  # Debug confirmation

    def create_widgets(self) -> None:
        """Initialize all UI components with improved button layout."""
        # Header
        self.header = tk.Frame(self, bg=COLORS["accent"])
        self.header.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            self.header,
            text="Edit Image Details",
            font=FONTS["heading"],
            bg=COLORS["accent"],
            fg="white",
            padx=10,
            pady=5
        ).pack()

        # Main form with scrollbar
        self.form_container = tk.Frame(self, bg=COLORS["background"])
        self.form_container.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(
            self.form_container,
            bg=COLORS["background"],
            highlightthickness=0
        )
        self.scrollbar = ttk.Scrollbar(
            self.form_container,
            orient="vertical",
            command=self.canvas.yview
        )
        self.form_frame = tk.Frame(self.canvas, bg=COLORS["background"])
        
        self.form_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.form_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Form elements
        self.create_form_fields()
        
        # Pack scrollable area
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Navigation controls
        self.create_navigation_controls()
        
        # Export section
        self.create_export_section()

    def create_form_fields(self) -> None:
        """Create metadata editing form fields with enhanced featured checkbox."""
        # Filename field
        tk.Label(
            self.form_frame,
            text="Filename:",
            font=FONTS["body"],
            bg=COLORS["background"],
            fg=COLORS["dark"]
        ).pack(anchor="w", pady=(5, 0))
        
        self.filename_entry = tk.Entry(
            self.form_frame,
            font=FONTS["body"],
            width=30
        )
        self.filename_entry.pack(fill="x", pady=(0, 10))
        self.filename_entry.bind("<KeyRelease>", self.on_filename_change)

        # Title field
        tk.Label(
            self.form_frame,
            text="Title:",
            font=FONTS["body"],
            bg=COLORS["background"],
            fg=COLORS["dark"]
        ).pack(anchor="w", pady=(5, 0))
        
        self.title_entry = tk.Entry(
            self.form_frame,
            font=FONTS["body"],
            width=30
        )
        self.title_entry.pack(fill="x", pady=(0, 10))
        self.title_entry.bind("<KeyRelease>", self.on_title_change)

        # Caption
        tk.Label(
            self.form_frame,
            text="Caption:",
            font=FONTS["body"],
            bg=COLORS["background"],
            fg=COLORS["dark"]
        ).pack(anchor="w", pady=(5, 0))
        
        self.caption_entry = tk.Text(
            self.form_frame,
            height=3,
            width=30,
            font=FONTS["body"],
            wrap=tk.WORD,
            padx=5,
            pady=5
        )
        self.caption_entry.pack(fill="x", pady=(0, 10))
        self.caption_entry.bind("<KeyRelease>", self.on_caption_change)

        # Keywords with tag suggestions
        self.tag_frame = tk.Frame(self.form_frame, bg=COLORS["background"])
        self.tag_frame.pack(fill="x", pady=(5, 0))
        
        tk.Label(
            self.tag_frame,
            text="Keywords:",
            font=FONTS["body"],
            bg=COLORS["background"],
            fg=COLORS["dark"]
        ).pack(anchor="w")
        
        self.keywords_entry = ttk.Combobox(
            self.tag_frame,
            font=FONTS["body"],
            values=self.tag_suggestions
        )
        self.keywords_entry.pack(fill="x", pady=(0, 5))
        self.keywords_entry.bind("<KeyRelease>", self.on_tags_change)
        self.keywords_entry.bind("<<ComboboxSelected>>", self.on_tag_selected)
        
        self.tag_list_frame = tk.Frame(self.form_frame, bg=COLORS["background"])
        self.tag_list_frame.pack(fill="x")

        # Alt Text
        tk.Label(
            self.form_frame,
            text="Alt Text:",
            font=FONTS["body"],
            bg=COLORS["background"],
            fg=COLORS["dark"]
        ).pack(anchor="w", pady=(5, 0))
        
        self.alt_text_entry = tk.Text(
            self.form_frame,
            height=3,
            width=30,
            font=FONTS["body"],
            wrap=tk.WORD,
            padx=5,
            pady=5
        )
        self.alt_text_entry.pack(fill="x", pady=(0, 10))
        self.alt_text_entry.bind("<KeyRelease>", self.on_alt_text_change)

        # Headline
        tk.Label(
            self.form_frame,
            text="Headline:",
            font=FONTS["body"],
            bg=COLORS["background"],
            fg=COLORS["dark"]
        ).pack(anchor="w", pady=(5, 0))
        
        self.headline_entry = tk.Entry(
            self.form_frame,
            font=FONTS["body"],
            width=30
        )
        self.headline_entry.pack(fill="x", pady=(0, 10))
        self.headline_entry.bind("<KeyRelease>", self.on_headline_change)

        # Enhanced Featured checkbox
        self.featured_var = tk.BooleanVar()
        self.featured_cb = tk.Checkbutton(
            self.form_frame,
            text="★ Featured Image",  # Added visual indicator
            variable=self.featured_var,
            font=("Georgia", 12, "bold"),  # More prominent
            bg=COLORS["background"],
            fg="#FFD700",  # Gold color
            selectcolor=COLORS["primary"],
            command=self.on_featured_change,
            padx=5,
            pady=3
        )
        self.featured_cb.pack(anchor="w", pady=(15, 20), ipadx=5, ipady=3)
        print("Featured checkbox created and packed")  # Debug confirmation

    def create_navigation_controls(self) -> None:
        """Create navigation and action buttons with improved layout."""
        # Main container for all buttons
        nav_container = tk.Frame(self, bg=COLORS["background"])
        nav_container.pack(fill="x", pady=(15, 0))
        
        # Row 1: Undo/Redo buttons
        undo_frame = tk.Frame(nav_container, bg=COLORS["background"])
        undo_frame.pack(fill="x", pady=(0, 5))
        
        self.undo_btn = ttk.Button(
            undo_frame,
            text="Undo",
            command=self.undo_change,
            style="Secondary.TButton",
            width=12
        )
        self.undo_btn.pack(side="left", padx=2)
        
        self.redo_btn = ttk.Button(
            undo_frame,
            text="Redo",
            command=self.redo_change,
            style="Secondary.TButton",
            width=12
        )
        self.redo_btn.pack(side="left", padx=2)

        # Row 2: Previous/Next navigation
        nav_frame = tk.Frame(nav_container, bg=COLORS["background"])
        nav_frame.pack(fill="x", pady=(0, 5))
        
        self.prev_btn = ttk.Button(
            nav_frame,
            text="◄ Previous",
            style="Secondary.TButton",
            width=12
        )
        self.prev_btn.pack(side="left", padx=2)
        
        self.next_btn = ttk.Button(
            nav_frame,
            text="Next ►",
            style="Secondary.TButton",
            width=12
        )
        self.next_btn.pack(side="left", padx=2)

        # Row 3: Up/Down movement
        move_frame = tk.Frame(nav_container, bg=COLORS["background"])
        move_frame.pack(fill="x", pady=(0, 5))
        
        self.up_btn = ttk.Button(
            move_frame,
            text="▲ Move Up",
            style="Secondary.TButton",
            width=12
        )
        self.up_btn.pack(side="left", padx=2)
        
        self.down_btn = ttk.Button(
            move_frame,
            text="▼ Move Down",
            style="Secondary.TButton",
            width=12
        )
        self.down_btn.pack(side="left", padx=2)

        # Row 4: Save actions
        save_frame = tk.Frame(nav_container, bg=COLORS["background"])
        save_frame.pack(fill="x", pady=(0, 5))
        
        self.save_btn = ttk.Button(
            save_frame,
            text="Save",
            style="Primary.TButton",
            width=12,
            command=self.save_current
        )
        self.save_btn.pack(side="left", padx=2)
        
        self.save_exit_btn = ttk.Button(
            save_frame,
            text="Save & Exit",
            style="Accent.TButton",
            width=12,
            command=self.save_and_exit
        )
        self.save_exit_btn.pack(side="left", padx=2)

        # Row 5: Exit button
        exit_frame = tk.Frame(nav_container, bg=COLORS["background"])
        exit_frame.pack(fill="x", pady=(0, 5))
        
        self.exit_btn = ttk.Button(
            exit_frame,
            text="Exit",
            style="Accent.TButton",
            width=12,
            command=self.on_exit
        )
        self.exit_btn.pack(side="left", padx=2)

    def set_button_commands(
        self,
        prev_command: Callable,
        next_command: Callable,
        save_command: Callable,
        up_command: Callable,
        down_command: Callable,
        exit_command: Callable
    ) -> None:
        """
        Set callback functions for navigation buttons.
        
        Args:
            prev_command: Function for previous button
            next_command: Function for next button
            save_command: Function for save button
            up_command: Function for up button
            down_command: Function for down button
            exit_command: Function for exit button
        """
        self.prev_btn.config(command=prev_command)
        self.next_btn.config(command=next_command)
        self.save_btn.config(command=save_command)
        self.up_btn.config(command=up_command)
        self.down_btn.config(command=down_command)
        self.exit_btn.config(command=exit_command)

    def create_export_section(self) -> None:
        """Create export controls with proper config handling."""
        ttk.Label(
            self.export_frame,
            text="Export Settings:",
            style="Bold.TLabel"
        ).pack(anchor="w", pady=(10, 5))
        
        # Format selection
        format_frame = ttk.Frame(self.export_frame)
        format_frame.pack(fill="x", pady=5)
        
        ttk.Label(format_frame, text="Format:").pack(side="left")
        self.export_format = tk.StringVar(value=self.export_settings["format"])
        ttk.Combobox(
            format_frame,
            textvariable=self.export_format,
            values=["webp", "jpg", "png"],
            state="readonly",
            width=8
        ).pack(side="left", padx=5)
        
        # Quality control
        quality_frame = ttk.Frame(self.export_frame)
        quality_frame.pack(fill="x", pady=5)
        
        ttk.Label(quality_frame, text="Quality:").pack(side="left")
        self.export_quality = tk.IntVar(value=self.export_settings["quality"])
        ttk.Scale(
            quality_frame,
            from_=1,
            to=100,
            variable=self.export_quality,
            command=lambda v: self.quality_label.config(text=f"{int(float(v))}%")
        ).pack(side="left", expand=True, fill="x", padx=5)
        self.quality_label = ttk.Label(quality_frame, text=f"{self.export_settings['quality']}%")
        self.quality_label.pack(side="left")
        
        # Resize toggle
        self.resize_enabled = tk.BooleanVar(value=self.export_settings["resize_enabled"])
        ttk.Checkbutton(
            self.export_frame,
            text="Resize on Export",
            variable=self.resize_enabled,
            command=self.toggle_resize_fields
        ).pack(anchor="w", pady=5)
        
        # Resize dimensions
        self.resize_frame = ttk.Frame(self.export_frame)
        self.max_width = tk.IntVar(value=self.export_settings["max_width"])
        self.max_height = tk.IntVar(value=self.export_settings["max_height"])
        
        ttk.Label(self.resize_frame, text="Max Width:").grid(row=0, column=0, sticky="e")
        ttk.Entry(self.resize_frame, textvariable=self.max_width, width=6).grid(row=0, column=1, padx=5)
        ttk.Label(self.resize_frame, text="px").grid(row=0, column=2, sticky="w")
        
        ttk.Label(self.resize_frame, text="Max Height:").grid(row=1, column=0, sticky="e")
        ttk.Entry(self.resize_frame, textvariable=self.max_height, width=6).grid(row=1, column=1, padx=5)
        ttk.Label(self.resize_frame, text="px").grid(row=1, column=2, sticky="w")
        
        self.toggle_resize_fields()  # Set initial state
        
        # Export button
        ttk.Button(
            self.export_frame,
            text="Export Selected",
            command=self.on_export,
            style="Accent.TButton"
        ).pack(pady=10)

    def toggle_resize_fields(self) -> None:
        """Show/hide resize controls based on checkbox state."""
        if self.resize_enabled.get():
            self.resize_frame.pack(fill="x", padx=10)
        else:
            self.resize_frame.pack_forget()

    def setup_bindings(self) -> None:
        """Set up keyboard and mouse bindings."""
        # Undo/Redo shortcuts
        self.bind_all("<Control-z>", lambda e: self.undo_change())
        self.bind_all("<Control-y>", lambda e: self.redo_change())
        self.bind_all("<Control-s>", lambda e: self.save_current())

    def load_tag_suggestions(self) -> None:
        """Load tag suggestions from configuration."""
        self.tag_suggestions = self.config.get("tag_suggestions", [])
        if hasattr(self, 'keywords_entry'):  # Safety check
            self.keywords_entry["values"] = self.tag_suggestions
        else:
            print("Warning: keywords_entry not available when loading suggestions")

    def load_image_data(self, data: Dict) -> None:
        """
        Load image metadata into the form.
        
        Args:
            data: Dictionary containing image metadata
        """
        self.current_data = data
        
        # Store original state for change tracking
        self.original_state = {
            'filename': data.get('filename', data.get('url', '')),
            'title': data.get('title', ''),
            'caption': data.get('caption', ''),
            'keywords': data.get('keywords', []),
            'alt_text': data.get('alt_text', ''),
            'headline': data.get('headline', ''),
            'featured': data.get('featured', False)
        }
        
        # Clear previous entries
        self.filename_entry.delete(0, tk.END)
        self.title_entry.delete(0, tk.END)
        self.caption_entry.delete("1.0", tk.END)
        self.keywords_entry.delete(0, tk.END)
        self.alt_text_entry.delete("1.0", tk.END)
        self.headline_entry.delete(0, tk.END)
        
        # Populate form fields
        if data:
            self.filename_entry.insert(0, self.original_state['filename'])
            self.title_entry.insert(0, self.original_state['title'])
            self.caption_entry.insert("1.0", self.original_state['caption'])
            self.keywords_entry.insert(0, ", ".join(self.original_state['keywords']))
            self.alt_text_entry.insert("1.0", self.original_state['alt_text'])
            self.headline_entry.insert(0, self.original_state['headline'])
            self.featured_var.set(self.original_state['featured'])
            
            # Visual feedback for featured state
            if self.original_state['featured']:
                self.featured_cb.config(fg="#FFD700")  # Gold when featured
            else:
                self.featured_cb.config(fg=COLORS["dark"])  # Normal color
            
            # Update modified date if available
            if "modified_date" in data:
                mod_date = datetime.fromisoformat(data["modified_date"]).strftime("%Y-%m-%d %H:%M")
                self.status_cb(f"Last modified: {mod_date}")

        # Clear history for new image
        self.history = HistoryManager()
        self.update_undo_redo_buttons()

    def get_image_data(self) -> Dict:
        """
        Get edited metadata from the form.
        
        Returns:
            Dictionary with updated image metadata
        """
        if not self.current_data:
            return {}
            
        return {
            "filename": self.filename_entry.get().strip(),
            "title": self.title_entry.get().strip(),
            "caption": self.caption_entry.get("1.0", "end-1c").strip(),
            "keywords": [k.strip() for k in self.keywords_entry.get().split(",") if k.strip()],
            "alt_text": self.alt_text_entry.get("1.0", "end-1c").strip(),
            "headline": self.headline_entry.get().strip(),
            "featured": self.featured_var.get(),
            "modified_date": datetime.now().isoformat()
        }

    def save_current(self) -> None:
        """Save metadata for current image."""
        if not self.current_data:
            return
            
        new_data = self.get_image_data()
        self.current_data.update(new_data)
        self.status_cb("Changes saved successfully")
        self.original_state = new_data.copy()
        self.history = HistoryManager()  # Clear history after save

    def save_and_exit(self) -> None:
        """Save current changes and exit."""
        self.save_current()
        self.on_exit()

    # Event handlers
    def on_filename_change(self, event=None) -> None:
        """Handle filename changes."""
        if self.current_data:
            old_val = self.original_state.get('filename', '')
            new_val = self.filename_entry.get().strip()
            if old_val != new_val:
                self.history.record_change('filename', old_val, new_val)
                self.update_undo_redo_buttons()

    def on_title_change(self, event=None) -> None:
        """Handle title changes."""
        if self.current_data:
            old_val = self.original_state.get('title', '')
            new_val = self.title_entry.get().strip()
            if old_val != new_val:
                self.history.record_change('title', old_val, new_val)
                self.update_undo_redo_buttons()

    def on_caption_change(self, event=None) -> None:
        """Handle caption changes."""
        if self.current_data:
            old_val = self.original_state.get('caption', '')
            new_val = self.caption_entry.get("1.0", "end-1c").strip()
            if old_val != new_val:
                self.history.record_change('caption', old_val, new_val)
                self.update_undo_redo_buttons()

    def on_tags_change(self, event=None) -> None:
        """Handle tag changes."""
        if self.current_data:
            old_val = self.original_state.get('keywords', [])
            new_val = [k.strip() for k in self.keywords_entry.get().split(",") if k.strip()]
            if old_val != new_val:
                self.history.record_change('keywords', old_val, new_val)
                self.update_undo_redo_buttons()

    def on_tag_selected(self, event=None) -> None:
        """Handle tag selection from dropdown."""
        current_tags = [k.strip() for k in self.keywords_entry.get().split(",") if k.strip()]
        selected = self.keywords_entry.get()
        
        if selected and selected not in current_tags:
            new_tags = current_tags + [selected]
            self.keywords_entry.set(", ".join(new_tags))
            self.on_tags_change()

    def on_alt_text_change(self, event=None) -> None:
        """Handle alt text changes."""
        if self.current_data:
            old_val = self.original_state.get('alt_text', '')
            new_val = self.alt_text_entry.get("1.0", "end-1c").strip()
            if old_val != new_val:
                self.history.record_change('alt_text', old_val, new_val)
                self.update_undo_redo_buttons()

    def on_headline_change(self, event=None) -> None:
        """Handle headline changes."""
        if self.current_data:
            old_val = self.original_state.get('headline', '')
            new_val = self.headline_entry.get().strip()
            if old_val != new_val:
                self.history.record_change('headline', old_val, new_val)
                self.update_undo_redo_buttons()

    def on_featured_change(self) -> None:
        """Handle featured checkbox changes."""
        if self.current_data:
            old_val = self.original_state.get('featured', False)
            new_val = self.featured_var.get()
            if old_val != new_val:
                self.history.record_change('featured', old_val, new_val)
                self.update_undo_redo_buttons()
                # Update visual feedback
                if new_val:
                    self.featured_cb.config(fg="#FFD700")
                else:
                    self.featured_cb.config(fg=COLORS["dark"])

    def on_exit(self) -> None:
        """Handle exit button click."""
        if self.current_data and self.has_unsaved_changes():
            if messagebox.askyesno("Unsaved Changes", "Save changes before exiting?"):
                self.save_current()
        self.master.quit()

    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        if not self.current_data:
            return False
        current_state = self.get_image_data()
        return any(
            current_state[key] != self.original_state.get(key, '')
            for key in current_state
        )

    # Undo/Redo functionality
    def undo_change(self, event=None) -> None:
        """Undo the last change with thread safety."""
        change = self.history.get_undo_change()
        if change:
            with self.history._lock:
                self.history.redo_stack.append(change)
            self.apply_change(change['field'], change['old_value'])
            self.status_cb(f"Undo: {change['field']}")
            self.update_undo_redo_buttons()

    def redo_change(self, event=None) -> None:
        """Redo the last undone change with thread safety."""
        change = self.history.get_redo_change()
        if change:
            with self.history._lock:
                self.history.undo_stack.append(change)
            self.apply_change(change['field'], change['new_value'])
            self.status_cb(f"Redo: {change['field']}")
            self.update_undo_redo_buttons()

    def apply_change(self, field: str, value: Any) -> None:
        """Apply a change to the appropriate field."""
        if field == 'filename':
            self.filename_entry.delete(0, tk.END)
            self.filename_entry.insert(0, value)
        elif field == 'title':
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, value)
        elif field == 'caption':
            self.caption_entry.delete("1.0", tk.END)
            self.caption_entry.insert("1.0", value)
        elif field == 'keywords':
            self.keywords_entry.delete(0, tk.END)
            self.keywords_entry.insert(0, ", ".join(value))
        elif field == 'alt_text':
            self.alt_text_entry.delete("1.0", tk.END)
            self.alt_text_entry.insert("1.0", value)
        elif field == 'headline':
            self.headline_entry.delete(0, tk.END)
            self.headline_entry.insert(0, value)
        elif field == 'featured':
            self.featured_var.set(value)
            self.on_featured_change()  # Update visual state

    def update_undo_redo_buttons(self) -> None:
        """Update undo/redo button states based on history."""
        self.undo_btn["state"] = "normal" if self.history.undo_stack else "disabled"
        self.redo_btn["state"] = "normal" if self.history.redo_stack else "disabled"

    # Export functionality
    def on_export(self) -> None:
        """Handle export button click."""
        if not self.current_data:
            self.status_cb("No image selected for export")
            return
            
        export_settings = {
            "format": self.export_format.get(),
            "quality": self.export_quality.get(),
            "resize_enabled": self.resize_enabled.get(),
            "max_width": self.max_width.get(),
            "max_height": self.max_height.get()
        }
        
        # Update config
        self.config["export_settings"] = export_settings
        self.status_cb(f"Exporting with settings: {export_settings}")
        # Actual export implementation would go here