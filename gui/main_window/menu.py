# gui/main_window/menu.py
"""
Main menu implementation for the Henna Gallery Editor.

Provides:
- MainMenu class for menu creation and management
- Menu item configuration with proper callbacks
- Theming support using config colors
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING
from config import get_color

if TYPE_CHECKING:
    from .base import MainWindow

class MainMenu:
    """
    Handles creation and management of the main application menu.
    
    Attributes:
        main_window (MainWindow): Reference to the main window instance
        menubar (tk.Menu): The main menu bar
    """
    
    def __init__(self, main_window: 'MainWindow'):
        """
        Initialize the menu system.
        
        Args:
            main_window: Reference to the main window instance
        """
        self.main_window = main_window
        self.menubar = tk.Menu(main_window.root, bg=get_color("background", "#F9F7F4"))
        self._create_menu()

    def _create_menu(self):
        """Create and configure the main menu bar."""
        # File Menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(
            label="Select Root Folder", 
            command=self.main_window.select_root_folder
        )
        file_menu.add_command(
            label="Batch Process", 
            command=self.main_window.start_batch_process
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.main_window.root.quit)
        self.menubar.add_cascade(label="File", menu=file_menu)

        # Edit Menu
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        edit_menu.add_command(
            label="Refresh", 
            command=self.main_window.refresh_current_folder
        )
        edit_menu.add_command(
            label="Sort Images (A-Z)", 
            command=self.main_window.sort_images_az
        )
        edit_menu.add_command(
            label="Sort Images (Z-A)", 
            command=self.main_window.sort_images_za
        )
        edit_menu.add_command(
            label="Sort by Featured", 
            command=self.main_window.sort_images_featured
        )
        self.menubar.add_cascade(label="Edit", menu=edit_menu)

        # Set the menu
        self.main_window.root.config(menu=self.menubar)

def create_main_menu(main_window: 'MainWindow'):
    """
    Legacy function for backward compatibility.
    Creates a MainMenu instance and returns the menubar.
    
    Args:
        main_window: Reference to the main window instance
        
    Returns:
        tk.Menu: The created menu bar
    """
    menu = MainMenu(main_window)
    return menu.menubar