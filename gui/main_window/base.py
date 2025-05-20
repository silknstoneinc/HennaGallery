"""
gui/main_window/base.py

Main Application Window - Core controller for the gallery application

Responsibilities:
- Main window setup and layout
- Core application state management
- Handler initialization and coordination
- Event binding and routing
- UI panel management

Dependencies:
- All GUI panels (left, center, right, status)
- Core handlers (folder, image, batch, sort)
- Drag handlers (reorder, folder move)
"""

import os
import json
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from PIL import Image

from config import get_color

# GUI Components
from gui.left_panel import LeftPanel
from gui.center_panel import CenterPanel
from gui.right_panel import RightPanel
from gui.status_bar import StatusBar
from gui.styles import configure_styles
from core.migration import JsonMigrator
from core.schema_validator import SchemaValidator
from core.migration import JsonMigrator  # or wherever your JsonMigrator class is defined

# Utilities
from utils.thread_utils import run_in_thread

# Core Systems
from core.gallery_manager import GalleryManager
from core.vision_processor import VisionProcessor

# Main Window Handlers
from .handlers.folder_manager import FolderManager
from .handlers.image_manager import ImageManager
from .handlers.batch_processor import BatchProcessor
from .handlers.image_sorter import ImageSorter
from ..drag_handlers.drag_handler import DragHandler

class MainWindow(tk.Frame):
    """Main application window controller."""
    
    def __init__(self, master: tk.Tk, config: Dict[str, Any]):
        super().__init__(master)
        self.root = master
        self.config = config
        
        # darg_config
        self.drag_config = {
            'ghost_opacity': 0.8,
            'valid_drop_color': "#B4A7D6", 
            'invalid_drop_color': "#FF9999",
            'scroll_speed': 10
        }
        # Initialize core systems
        self._init_core_components()
        
        # Application state
        self.current_folder: Optional[str] = None
        self.current_image_index: int = 0
        self.images: List[Dict[str, Any]] = []
        
        # Setup UI and handlers
        self._setup_window()
        self._create_widgets()
        self._setup_core_handlers()  # ← New non-drag handlers
        self._setup_drag_system()    # ← New unified drag system
        self._final_setup()
        # Add these lines with other instance variables
        self._drag_initialized = False
        self._pending_drag_operations = []
        
    def _init_core_components(self):
        """Initialize core application systems."""
        configure_styles(self.root)
        self.gallery_manager = GalleryManager()
        self.vision_processor = VisionProcessor()
        
    def _setup_window(self):
        """Configure main window properties."""
        self.root.title("Silk & Stone Henna Gallery Tool")
        self.root.geometry("1400x950")
        self.root.minsize(1100, 800)
        self.root.configure(bg=get_color("background", "#F9F7F4"))
        self.pack(expand=True, fill="both", padx=0, pady=0)
        self.configure(bg=get_color("background", "#F9F7F4"))
        
    def _create_widgets(self):
        """Create and layout all main UI components."""
        # Status Bar
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(side="bottom", fill="x")
        
        # Main container frame
        self.main_frame = tk.Frame(self, bg=get_color("background", "#F9F7F4"))
        self.main_frame.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Left Panel - Folders
        self.left_panel = LeftPanel(
            self.main_frame, 
            self.on_folder_select,
            self.status_bar.update_status
        )
        self.left_panel.pack(side="left", fill="y", padx=(0, 5))
        self.left_panel.configure(width=340)  # Set fixed width

        # Center Panel - Image Display
        self.center_panel = CenterPanel(
            self.main_frame,
            self.status_bar.update_status,
            self  # Pass MainWindow reference explicitly
        )
        #self.center_panel.master = self
        self.center_panel.pack(side="left", fill="both", expand=True, padx=5)
        
        # Right Panel - Metadata Editing
        self.right_panel = RightPanel(
            self.main_frame,
            self.status_bar.update_status,
            self.config
        )
        self.right_panel.pack(side="right", fill="y", padx=(5, 0))
        self.right_panel.configure(width=420)  # Set fixed width

    def _setup_core_handlers(self):
        """Initialize NON-DRAG handlers only (called from __init__)"""
        self.folder_manager = FolderManager(self)
        self.image_manager = ImageManager(self)
        self.batch_processor = BatchProcessor(self)
        self.image_sorter = ImageSorter(self)

    def _setup_drag_system(self):
        if hasattr(self, '_drag_system_initialized'):
            return
            
        print("=== DRAG SYSTEM INITIALIZATION ===")
        self.drag_config = {
            'ghost_opacity': 0.8,
            'valid_drop_color': "#B4A7D6",
            'invalid_drop_color': "#FF9999",
            'ghost_offset_x': 15,
            'ghost_offset_y': 15,
            'drag_threshold': 5
        }
        
        # Add initialization tracking
        self._drag_initialized = False
        self._pending_drag_operations = []
        
        self.drag_handler = DragHandler(main_window=self, config=self.drag_config)
        
        def connect_drag_handler():
            if hasattr(self.center_panel, 'setup_drag_handlers'):
                self.center_panel.setup_drag_handlers(self.drag_handler)
                print("✓ Drag handler fully connected")
                
                # Force grid view update to ensure thumbnails exist
                if hasattr(self.center_panel, 'grid_view'):
                    self.center_panel.grid_view.update_view()
                    
                # Mark as initialized and process pending operations
                self._drag_initialized = True
                for operation in self._pending_drag_operations:
                    operation()
                self._pending_drag_operations.clear()
                
                # Verify the connection
                print(f"Source view type: {type(self.center_panel.grid_view)}")
                print(f"Folders panel type: {type(self.left_panel.folders_frame)}")
            else:
                self.after(100, connect_drag_handler)
        
        self.after(300, connect_drag_handler)
        self._drag_system_initialized = True
    
    def _verify_drag_setup(self):
        """Verify and setup drag bindings when UI is ready"""
        if not hasattr(self.center_panel, 'grid_view'):
            self.after(100, self._verify_drag_setup)
            return
            
        self.center_panel.grid_view.bind("<<ThumbnailsLoaded>>", self._setup_thumbnail_drag_bindings)
        print("Drag system ready for thumbnail bindings")
        
    def _setup_thumbnail_drag_bindings(self):
        """Setup drag bindings when thumbnails are actually loaded"""
        print("\n=== SETTING UP THUMBNAIL DRAG BINDINGS ===")
        
        if not hasattr(self.center_panel.grid_view, 'grid_inner_frame'):
            print("No grid inner frame found")
            return
            
        thumbnails = self.center_panel.grid_view.grid_inner_frame.winfo_children()
        print(f"Found {len(thumbnails)} thumbnails to configure")
        
        for thumb in thumbnails:
            if hasattr(thumb, '_setup_bindings'):
                thumb._setup_bindings()
                print(f"Configured drag for thumbnail {thumb}")
        
    def _final_setup(self):
        """Final initialization steps."""
        self.setup_navigation_callbacks()
        self.bind_events()
        self._setup_view_specific_bindings()
        self._create_menu()
        
    def setup_navigation_callbacks(self):
        """Connect navigation controls."""
        self.center_panel.set_navigation_callbacks(
            next_cb=self.show_next_image,
            prev_cb=self.show_previous_image
        )

    def bind_events(self):
        """Bind UI events to handlers."""
        self.right_panel.set_button_commands(
            prev_command=self.show_previous_image,
            next_command=self.show_next_image,
            save_command=self.save_current_image,
            up_command=self.move_image_up,
            down_command=self.move_image_down,
            exit_command=self.root.quit
        )

    def _setup_view_specific_bindings(self):
        """Configure bindings appropriate for each view"""
        # Single view - only pan/zoom
        if hasattr(self.center_panel, 'single_view'):
            canvas = self.center_panel.single_view.canvas
            canvas.unbind("<ButtonPress-1>")
            canvas.unbind("<B1-Motion>")
            
            canvas.bind("<MouseWheel>", lambda e: self.center_panel.zoom_in() if e.delta > 0 else self.center_panel.zoom_out())
            canvas.bind("<Button-4>", lambda e: self.center_panel.zoom_in())
            canvas.bind("<Button-5>", lambda e: self.center_panel.zoom_out())
            
            # Panning bindings
            canvas.bind("<ButtonPress-1>", self.center_panel.start_pan)
            canvas.bind("<B1-Motion>", self.center_panel.pan_image)
            canvas.bind("<ButtonRelease-1>", self.center_panel.end_pan)

        # Grid view - drag handled by reorder_handler
    # -------------------- Core Functionality -------------------- #

    def on_folder_select(self, folder: Dict[str, str]) -> None:
        """Enhanced folder selection with debug logging and robust view updating"""
        print(f"Folder selected: {folder['name']} (path: {folder['path']})")
        
        try:
            self.current_folder = folder['path']
            folder_name = os.path.basename(folder['path'])
            json_path = os.path.join(folder['path'], f"{folder_name}.json")
            
            print(f"Looking for JSON at: {json_path}")
            
            if not os.path.exists(json_path):
                print("No JSON file found, creating empty gallery")
                self._handle_empty_gallery(folder)
                self.status_bar.update_status(f"No gallery data found in {folder['name']}")
                self._force_view_refresh()
                return
                
            # Load and validate data
            print("Loading JSON data...")
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Initialize migration tools
            migrator = JsonMigrator(backup_dir=os.path.join(folder['path'], "backups"))
            validator = SchemaValidator()
            
            # Check if migration needed
            file_format = migrator.detect_format(data)
            print(f"Detected format: {file_format}")
            
            if file_format != "v2":
                print("Migration needed, starting process...")
                if not migrator.safe_migrate_file(Path(json_path), parent_window=self.root):
                    self.status_bar.update_status("Migration cancelled or failed", alert=True)
                    self._force_view_refresh()
                    return
                
                # Reload after migration
                print("Reloading migrated data...")
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # Process images - modified section
            print("Processing images...")
            
            try:
                # Validate and get normalized data
                validated_data = validator.validate_gallery_data(data, Path(self.current_folder))
                self.images = validated_data['images']
                
                # Update UI regardless of whether there are images
                self.center_panel.folder_name_var.set(folder['name'])
                self.left_panel.update_folder_display(folder['path'], len(self.images))

                if not self.images:
                    self.status_bar.update_status(f"No valid images found in {folder['name']}")
                    self._handle_empty_gallery(folder)
                    return
                    
            except Exception as e:
                self.status_bar.update_status(f"Error loading images: {str(e)}", alert=True)
                self._handle_empty_gallery(folder)
                return
            
            # Normalize fields
            for img in self.images:
                img.setdefault('src', img.get('url', ''))
                img.setdefault('url', img['src'])  # Ensure both fields exist
                img.setdefault('filename', os.path.basename(img['src']))
                img.setdefault('alt_text', '')
                img.setdefault('order', img.get('sort_order', 0))
                img.setdefault('keywords', img.get('tags', []))
            
            # Update UI
            print("Updating UI...")
            self.current_image_index = 0
            
            # Always update folder display first
            self.left_panel.update_folder_display(folder['path'], len(self.images))
            
            if self.images:
                try:
                    self._update_current_image_display()
                    status = f"Loaded {len(self.images)} images from {folder['name']}"
                except Exception as img_error:
                    print(f"Error displaying images: {str(img_error)}")
                    self._handle_empty_gallery(folder)
                    status = f"Loaded {len(self.images)} images (some may be invalid)"
            else:
                self._handle_empty_gallery(folder)
                status = f"No valid images found in {folder['name']}"
            
            self.status_bar.update_status(status)
            self.update_navigation_buttons()
            
            # Force view refresh in all cases
            self._force_view_refresh()
            print("Folder selection complete")

        except Exception as e:
            error_msg = f"Error loading folder: {str(e)}"
            print(error_msg)
            self.status_bar.update_status(error_msg, alert=True)
            self._handle_empty_gallery(folder)
            self._force_view_refresh()

    def _force_view_refresh(self):
        """Ensure proper view refresh using verified CenterPanel methods"""
        if hasattr(self, 'center_panel'):
            if hasattr(self.center_panel, 'current_view'):
                if self.center_panel.current_view == "grid":
                    # Force complete grid view rebuild
                    self.center_panel.grid_view.update_view()
                else:
                    # CORRECTED: Use the EXACT method from CenterPanel
                    if hasattr(self.center_panel, 'show_image'):  # This matches your CenterPanel implementation
                        self.center_panel.show_image(
                            Path(self.current_folder) / self.images[self.current_image_index]['url'],
                            self.images[self.current_image_index]
                        )
            
            # Update folder name display
            if hasattr(self.center_panel, 'folder_name_var') and hasattr(self, 'current_folder'):
                self.center_panel.folder_name_var.set(os.path.basename(self.current_folder))

    def _handle_empty_gallery(self, folder: Dict[str, str]) -> None:
        """Handle empty or invalid gallery state"""
        self.images = []
        self.center_panel.folder_name_var.set(folder['name'])  # Add this line
        self.center_panel.show_placeholder()
        self.right_panel.load_image_data({})
        self.left_panel.update_folder_display(folder['path'], 0)

        # Force grid view update if in grid mode
        if hasattr(self.center_panel, 'grid_view') and self.center_panel.current_view == "grid":
            self.center_panel.grid_view.update_view()
        
    def _update_current_image_display(self):
        """Centralized method to update all image displays."""
        if not self.images or not (0 <= self.current_image_index < len(self.images)):
            return
            
        img_data = self.images[self.current_image_index]
        
        # Ensure required fields exist
        img_path = Path(self.current_folder) / img_data.get('url', img_data.get('src', ''))
        img_data['index'] = self.current_image_index
        img_data['total'] = len(self.images)
        
        # Update all UI components
        self.center_panel.show_image(img_path, img_data)
        self.right_panel.load_image_data(img_data)
        self.update_navigation_buttons()
        
    def show_current_image(self) -> None:
        """Display the currently selected image."""
        self._update_current_image_display()

    # -------------------- Image Management -------------------- #

    def move_image_up(self) -> None:
        """Move current image up in order."""
        if 0 < self.current_image_index < len(self.images):
            self._swap_images(self.current_image_index, self.current_image_index - 1)
            self.current_image_index -= 1
            self._after_reorder()
    
    def move_image_down(self) -> None:
        """Move current image down in order."""
        if 0 <= self.current_image_index < len(self.images) - 1:
            self._swap_images(self.current_image_index, self.current_image_index + 1)
            self.current_image_index += 1
            self._after_reorder()

    def _swap_images(self, index1: int, index2: int) -> None:
        """Swap two images in the list."""
        self.images[index1], self.images[index2] = self.images[index2], self.images[index1]
        self.save_folder_data()

    def _after_reorder(self) -> None:
        """Common operations after reordering."""
        self.show_current_image()
        self.center_panel.update_grid_view()

    def reorder_images(self, from_index, to_index):
        """Reorder images and update JSON"""
        if not (0 <= from_index < len(self.images)) or not (0 <= to_index < len(self.images)):
            return

        if from_index == to_index:
            return

        # Move the image
        img_data = self.images.pop(from_index)
        self.images.insert(to_index, img_data)

        # Update all sort orders and indexes
        for i, img in enumerate(self.images):
            img['sort_order'] = i
            img['order'] = i
            img['index'] = i  # Update index if needed

        # Update current image index if needed
        if self.current_image_index == from_index:
            self.current_image_index = to_index
        elif from_index < self.current_image_index <= to_index:
            self.current_image_index -= 1
        elif to_index <= self.current_image_index < from_index:
            self.current_image_index += 1

        # Save changes with proper validation
        self.save_folder_data()
        
        # Update UI
        self.center_panel.update_grid_view()
        
        # If we moved the current image, refresh its display
        if self.current_image_index == to_index:
            self.show_current_image()
    
    # -------------------- File Operations -------------------- #

    def save_current_image(self) -> None:
        """Save metadata for current image."""
        if 0 <= self.current_image_index < len(self.images):
            img_data = self.right_panel.get_image_data()
            self.images[self.current_image_index].update(img_data)
            self.save_folder_data()
            messagebox.showinfo("Saved", "Image data updated successfully")

    def save_folder_data(self) -> None:
        """Enhanced save method with robust validation and backward compatibility"""
        if not self.current_folder:
            return
            
        folder_name = os.path.basename(self.current_folder)
        json_path = os.path.join(self.current_folder, f"{folder_name}.json")
        
        # Create a copy of images to avoid modifying original data
        images_to_save = [img.copy() for img in self.images]
        
        # Clean and normalize data while preserving all existing fields
        for img in images_to_save:
            # Ensure backward compatibility with tags/keywords
            if 'tags' in img and 'keywords' not in img:
                img['keywords'] = img['tags']
            
            # Remove deprecated 'tags' field if present
            img.pop('tags', None)
            
            # Ensure required fields exist with defaults
            img.setdefault('src', img.get('url', ''))
            img.setdefault('url', img['src'])
            img.setdefault('filename', os.path.basename(img['url']))
            img.setdefault('alt_text', '')
            
            # Maintain sort order consistency
            img.setdefault('sort_order', img.get('order', 0))
            img['order'] = img['sort_order']  # Keep both fields in sync
            
            # Add timestamp if missing
            if 'modified_date' not in img:
                img['modified_date'] = datetime.now().isoformat()
        
        # Build complete data structure preserving all existing meta fields
        data = {
            "meta": self._get_meta(),  # Preserves existing meta generation
            "images": images_to_save
        }
        
        # Validate with enhanced checks
        from core.schema_validator import SchemaValidator
        validator = SchemaValidator()
        
        if validator.validate_gallery(data):
            # Create backup before saving
            backup_path = os.path.join(self.current_folder, "backups", f"{folder_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            try:
                # Save backup first
                if os.path.exists(json_path):
                    shutil.copy2(json_path, backup_path)
                
                # Save new version
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
            except Exception as e:
                self.status_bar.update_status(f"Save failed: {str(e)}", alert=True)
                # Attempt to restore from backup if available
                if os.path.exists(backup_path):
                    try:
                        shutil.copy2(backup_path, json_path)
                    except:
                        pass
                raise
        else:
            errors = validator.get_validation_errors(data)
            error_msg = "Cannot save invalid data:\n" + "\n".join(errors)
            messagebox.showerror("Validation Failed", error_msg)
            self.status_bar.update_status("Validation failed - data not saved", alert=True)
    
    # -------------------- Menu Actions -------------------- #
    def _create_menu(self):
        """Create the main menu bar using the MainMenu class."""
        from .menu import MainMenu
        self.menu = MainMenu(self)

    def show_next_image(self) -> None:
        """Navigate to next image in current folder."""
        if self.current_image_index < len(self.images) - 1:
            self.current_image_index += 1
            self._update_current_image_display()

    # - select_root_folder()
    def select_root_folder(self):
        """Select the root folder containing all galleries."""
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.gallery_manager.root_folder = folder_path
            self.status_bar.update_status(f"Root folder set to: {folder_path}")
            folders = self.get_folder_list()
            self.left_panel.load_folders(folders)

    # - get_folder_list()
    def get_folder_list(self) -> List[Dict[str, Any]]:
        """Enhanced folder scanning with health checks"""
        folders = []
        if not hasattr(self.gallery_manager, 'root_folder'):
            return folders
            
        migrator = JsonMigrator()
        
        for item in sorted(os.listdir(self.gallery_manager.root_folder)):
            full_path = os.path.join(self.gallery_manager.root_folder, item)
            
            if not os.path.isdir(full_path):
                continue
                
            try:
                json_path = os.path.join(full_path, f"{item}.json")
                image_count = 0  # Default count
                
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    # Get image count from either v1 or v2 format
                    image_count = len(data.get('images', [])) if isinstance(data, dict) else len(data)
                
                thumb = self.find_first_image(full_path)
                
                folders.append({
                    'name': item,
                    'path': full_path,
                    'thumbnail_path': thumb,
                    'image_count': image_count  # Now properly set
                })
                
            except Exception as e:
                print(f"Error scanning folder {item}: {str(e)}")
                folders.append({
                    'name': item,
                    'path': full_path,
                    'thumbnail_path': None,
                    'image_count': 0
                })
                
        return folders

    # - find_first_image()
    def find_first_image(self, folder_path: str) -> Optional[str]:
        """Find first valid image in folder for thumbnail preview."""
        valid_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')
        
        try:
            for f in sorted(os.listdir(folder_path)):
                if f.lower().endswith(valid_extensions):
                    full_path = os.path.join(folder_path, f)
                    try:
                        with Image.open(full_path) as img:
                            img.verify()
                        return full_path
                    except (IOError, SyntaxError):
                        continue
        except PermissionError:
            self.status_bar.update_status(f"Permission denied accessing images in {folder_path}", temporary=True)
            
        return None

    # - show_current_image()
    def show_current_image(self) -> None:
        """Display the currently selected image."""
        if 0 <= self.current_image_index < len(self.images):
            img_data = self.images[self.current_image_index]
            img_path = Path(self.current_folder) / img_data['url']
            
            # Add index and total to metadata
            img_data['index'] = self.current_image_index
            img_data['total'] = len(self.images)
            
            self.center_panel.show_image(img_path, img_data)
            self.right_panel.load_image_data(img_data)
            
            # Update button states
            self.update_navigation_buttons()
            
            self.status_bar.update_status(
                f"Image {self.current_image_index + 1} of {len(self.images)}")

    # - update_navigation_buttons()
    def update_navigation_buttons(self):
        """Enable/disable navigation buttons based on current position"""
        has_images = len(self.images) > 0
        self.right_panel.prev_btn["state"] = "normal" if has_images and self.current_image_index > 0 else "disabled"
        self.right_panel.next_btn["state"] = "normal" if has_images and self.current_image_index < len(self.images) - 1 else "disabled"
        self.right_panel.up_btn["state"] = "normal" if has_images and self.current_image_index > 0 else "disabled"
        self.right_panel.down_btn["state"] = "normal" if has_images and self.current_image_index < len(self.images) - 1 else "disabled"
    
    def show_previous_image(self) -> None:
        """Navigate to previous image in current folder."""
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self._update_current_image_display()

    def move_image_up(self) -> None:
        """Move current image up in the order."""
        if 0 < self.current_image_index < len(self.images):
            self.images[self.current_image_index], self.images[self.current_image_index - 1] = \
                self.images[self.current_image_index - 1], self.images[self.current_image_index]
            self.current_image_index -= 1
            self.save_folder_data()
            self.show_current_image()
            self.center_panel.update_grid_view()

    def move_image_down(self) -> None:
        """Move current image down in the order."""
        if 0 <= self.current_image_index < len(self.images) - 1:
            self.images[self.current_image_index], self.images[self.current_image_index + 1] = \
                self.images[self.current_image_index + 1], self.images[self.current_image_index]
            self.current_image_index += 1
            self.save_folder_data()
            self.show_current_image()
            self.center_panel.update_grid_view()

    def save_current_image(self) -> None:
        """Save metadata for current image."""
        if 0 <= self.current_image_index < len(self.images):
            img_data = self.right_panel.get_image_data()
            self.images[self.current_image_index].update(img_data)
            self.save_folder_data()
            messagebox.showinfo("Saved", "Image data updated successfully")

    def start_batch_process(self) -> None:
        """Start batch processing of all folders."""
        if not hasattr(self.gallery_manager, 'root_folder'):
            messagebox.showerror("Error", "Please select root folder first")
            return

        def process_task() -> int:
            """Background task to process all folders."""
            total = 0
            folders = self.get_folder_list()
            for i, folder in enumerate(folders):
                count = self.gallery_manager.process_folder(folder['path'])
                total += count
                progress = (i + 1) / len(folders) * 100
                self.status_bar.update_status(
                    f"Processed {folder['name']} ({count} new images)", 
                    progress
                )
            return total

        def on_complete(total: int) -> None:
            """Callback when batch processing completes."""
            messagebox.showinfo(
                "Complete", 
                f"Batch processing completed\n{total} new images processed"
            )
            self.left_panel.load_folders(self.get_folder_list())

        run_in_thread(process_task, on_complete)

    def refresh_current_folder(self) -> None:
        """Reload the currently selected folder."""
        if self.current_folder:
            self.on_folder_select({
                'name': os.path.basename(self.current_folder),
                'path': self.current_folder
            })
    
    def reorder_images(self, from_index, to_index):
        """Reorder images in the list."""
        if 0 <= from_index < len(self.images) and 0 <= to_index <= len(self.images):
            if from_index == to_index:
                return
                
            item = self.images.pop(from_index)
            self.images.insert(to_index, item)
            
            # Update current image index if needed
            if self.current_image_index == from_index:
                self.current_image_index = to_index
            elif from_index < self.current_image_index <= to_index:
                self.current_image_index -= 1
            elif to_index <= self.current_image_index < from_index:
                self.current_image_index += 1
                
            self.save_folder_data()
            self.center_panel.update_grid_view()
            
            # Update the single view if showing the moved image
            if self.current_image_index == to_index:
                self.show_current_image()

    def move_image_to_folder(self, index: int, folder_path: str) -> None:
        """Enhanced folder move with transaction safety"""
        try:
            # Validate paths
            src_path = Path(self.current_folder)
            dest_path = Path(folder_path)
            
            if not dest_path.exists():
                raise ValueError("Target folder doesn't exist")
                
            if src_path == dest_path:
                raise ValueError("Cannot move to same folder")
                
            # Get image data
            if index < 0 or index >= len(self.images):
                raise IndexError("Invalid image index")
                
            img_data = self.images[index]
            src_file = src_path / img_data['url']
            
            if not src_file.exists():
                raise FileNotFoundError(f"Source image missing: {src_file}")
                
            # Generate new filename using gallery naming convention
            folder_name = dest_path.name
            tags = img_data.get('keywords', [])
            img_hash = self.compute_image_hash(src_file)
            new_name = f"{self.slugify(folder_name)}-{self.slugify('-'.join(tags[:2]))}-{img_hash[:6]}{src_file.suffix.lower()}"
            new_name = "".join(c for c in new_name if c.isalnum() or c in ('-', '_', '.'))
            dest_file = dest_path / new_name

            # Transaction block
            try:
                # Move physical file
                shutil.move(src_file, dest_file)
                
                # Update source JSON
                self.images.pop(index)
                self.save_folder_data()
                
                # Update destination JSON
                dest_json = dest_path / f"{dest_path.name}.json"
                dest_data = {"images": []}
                
                if dest_json.exists():
                    with open(dest_json, 'r', encoding='utf-8') as f:
                        dest_data = json.load(f)
                    
                # Update image data with new filename
                img_data['url'] = new_name
                img_data['filename'] = new_name
                img_data['modified_date'] = datetime.now().isoformat()
                dest_data['images'].insert(0, img_data)
                
                # Save destination JSON
                with open(dest_json, 'w', encoding='utf-8') as f:
                    json.dump(dest_data, f, indent=2, ensure_ascii=False)
                    
                # Update UI
                self.refresh_current_folder()  # This reloads the current folder
                self.left_panel.load_folders(self.get_folder_list())  # Updates folder list
                self.center_panel.update_grid_view()  # Force immediate grid refresh
                
            except Exception as e:
                # Try to move file back if something failed
                if dest_file.exists():
                    try:
                        shutil.move(dest_file, src_file)
                    except Exception:
                        pass
                raise
                
        except Exception as e:
            self.status_bar.update_status(f"Move failed: {str(e)}")
            raise

    def compute_image_hash(self, filepath: Path) -> str:
        """Compute a simple hash of an image file for naming purposes"""
        try:
            with open(filepath, 'rb') as f:
                return str(hash(f.read()))
        except Exception:
            return str(hash(str(filepath)))

    def sort_images_az(self):
        """Sort images A-Z by filename"""
        if self.images:
            self.images.sort(key=lambda x: x['url'].lower())
            self.current_image_index = 0
            self.save_folder_data()
            self.show_current_image()
            self.center_panel.update_grid_view()
            messagebox.showinfo("Sorted", "Images sorted A-Z by filename")

    def sort_images_za(self):
        """Sort images Z-A by filename"""
        if self.images:
            self.images.sort(key=lambda x: x['url'].lower(), reverse=True)
            self.current_image_index = 0
            self.save_folder_data()
            self.show_current_image()
            self.center_panel.update_grid_view()
            messagebox.showinfo("Sorted", "Images sorted Z-A by filename")

    def sort_images_featured(self):
        """Sort images with featured first"""
        if self.images:
            self.images.sort(key=lambda x: not x.get('featured', False))
            self.current_image_index = 0
            self.save_folder_data()
            self.show_current_image()
            self.center_panel.update_grid_view()
            messagebox.showinfo("Sorted", "Featured images moved to top")

    def _get_meta(self) -> Dict[str, Any]:
        """
        Generate v2.0 metadata for current folder.
        
        Returns:
            Dict: Contains:
                - gallery_title (from folder name)
                - gallery_slug (auto-generated)
                - timestamps
                - Empty export_profiles
        """
        folder_name = os.path.basename(self.current_folder)
        now = datetime.now().isoformat()
        
        return {
            "gallery_title": folder_name,
            "gallery_slug": folder_name.lower().replace(" ", "-"),
            "created_date": now,  # Would ideally load from original if available
            "last_updated": now,
            "export_profiles": []
        }
    
    def slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug"""
        import unicodedata
        import re
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        text = re.sub(r'[^\w\s-]', '', text).strip().lower()
        return re.sub(r'[-\s]+', '-', text)
    
    from contextlib import contextmanager
    import tempfile
    import os

    @contextmanager
    def _folder_transaction(self, folder_path: Path):
        """
        Context manager for safe folder operations.
        Creates backups of critical files and can rollback on failure.
        
        Usage:
        with self._folder_transaction(folder_path):
            # Perform file operations here
            # If any operation fails, the context manager will attempt cleanup
        """
        backup_dir = tempfile.mkdtemp()  # Create temp backup directory
        backed_up_files = []
        
        try:
            # Backup any existing JSON files in the folder
            json_files = list(folder_path.glob('*.json'))
            for json_file in json_files:
                backup_path = Path(backup_dir) / json_file.name
                shutil.copy2(json_file, backup_path)
                backed_up_files.append((json_file, backup_path))
            
            yield  # This is where your operation executes
            
        except Exception as e:
            # Restore backups if something went wrong
            self.status_bar.update_status(f"Operation failed, restoring backups...")
            for original, backup in backed_up_files:
                try:
                    shutil.copy2(backup, original)
                except Exception as restore_error:
                    self.status_bar.update_status(f"Failed to restore {original.name}: {str(restore_error)}")
            
            raise  # Re-raise the original exception
            
        finally:
            # Clean up backup files
            try:
                shutil.rmtree(backup_dir)
            except Exception as cleanup_error:
                self.status_bar.update_status(f"Could not clean up backups: {str(cleanup_error)}")