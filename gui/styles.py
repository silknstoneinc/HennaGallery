"""
Enhanced style configuration for Henna Gallery Editor.
Centralizes all visual styling including colors, fonts, and widget styles.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Tuple

from config import get_color

# ========== COLOR DEFINITIONS ==========
COLORS: Dict[str, str] = {
     # Core colors
    "primary": "#5D9B7F",  # Keep this saturated green
    "primary_dark": "#3E7A5F",
    "primary_light": "#D1E9D8",
    "secondary": "#D8C6B8",
    "secondary_dark": "#B8A495",
    "secondary_light": "#E8DED3",
    "accent": "#7E6BAB",  # Keep this saturated purple
    "accent_dark": "#5E4D8B",
    "accent_light": "#D3CAEB",

    "info_bg": "#5A5A5A",  # Dark gray for info panel
    "info_fg": "white",     # Text color
    "tooltip_bg": "#FFFFFF", # White background for tooltip
    "tooltip_fg": "#333333", # Dark text for tooltip
    
    # Grayscale
    "dark": "#5A5A5A",
    "darker": "#3A3A3A",
    "dark_light": "#7A7A7A",
    
    # Backgrounds
    "background": "#F9F7F4",
    "background_dark": "#EDEAE4",
    "background_light": "#FFFFFF",
    
    # Highlights
    "highlight": "#F1D1A1",
    "highlight_dark": "#E0B87A",
    "highlight_light": "#F8E5C8",
    
    # Status colors
    "success": "#4CAF50",
    "warning": "#FFC107",
    "error": "#F44336",
    "info": "#2196F3",
    
    # Text and special colors
    "button_text": "#5E4D8B",  # White text for dark buttons (keep only one) FFFFF
    "button_text_light": "#333333",  # Dark text for light buttons
    "exit_bg": "#C62828",  # Keep the brighter red (remove the D32F2F version)
    "export_bg": "#F5F5F5",
    "export_border": "#E0E0E0",
    "section_shadow": "#BDBDBD"
}

# ========== FONT DEFINITIONS ==========
FONTS: Dict[str, Tuple] = {
    "title": ("Georgia", 24, "bold"),
    "heading": ("Georgia", 18, "bold"),
    "subheading": ("Georgia", 14),
    "body": ("Georgia", 12),
    "body_bold": ("Georgia", 12, "bold"),
    "small": ("Georgia", 10),
    "small_bold": ("Georgia", 10, "bold"),
    "code": ("Courier New", 11)
}

def configure_styles(root: tk.Tk) -> None:
    """Configure ttk widget styles with improved button contrast."""
    style = ttk.Style(root)
    
    # Base button style
    style.configure("TButton",
        font=FONTS["body"],
        padding=8,  # Increased padding for better spacing
        relief="raised",
        borderwidth=1
    )

    # Frame styles
    style.configure("TFrame", background=COLORS["background"])
    
    # Button styles
    style.configure("TButton",
        font=FONTS["body"],
        padding=6,
        background=COLORS["primary"],
        foreground=COLORS["dark"]
    )
    style.map("TButton",
        background=[
            ("active", COLORS["primary_dark"]),
            ("disabled", COLORS["background_dark"])
        ],
        foreground=[
            ("disabled", COLORS["dark_light"]),
            ("pressed", "white"), 
            ("active", "white")
        ]
    )
    
    # Special button styles with better contrast
    button_styles = {
        "TButton": {
            "background": COLORS["primary"],
            "foreground": COLORS["button_text"],  # White text
            "active_bg": COLORS["primary_dark"],
            "disabled_fg": COLORS["dark_light"]
        },
        "Primary.TButton": {
            "background": COLORS["primary"], # Green background
            "foreground": "#8E0000",  # Force white text
            "font": FONTS["body_bold"],
            "active_bg": COLORS["primary_dark"] # Slightly lighter when active
        },
        "Accent.TButton": {
            "background": COLORS["accent"], # Purple background
            "foreground": "#8E0000",  # Force white text
            "font": FONTS["body_bold"],
            "active_bg": COLORS["accent_dark"] # Dark when active
        },
        "Warning.TButton": {
            "background": COLORS["exit_bg"],
            "foreground": COLORS["button_text"],
            "font": FONTS["body_bold"],
            "active_bg": "#8E0000"  # Darker red
        },
        "Secondary.TButton": {
            "background": COLORS["secondary_light"],  # Light background
            "foreground": COLORS["darker"],  # Dark text
            "font": FONTS["body"],
            "active_bg": COLORS["secondary"]
        }
    }
    
    for style_name, config in button_styles.items():
        style.configure(style_name,
            background=config["background"],
            foreground=config["foreground"],
            font=config.get("font", FONTS["body"]),
            padding=6
        )
        style.map(style_name,
            background=[
                ("active", config["active_bg"]),
                ("disabled", COLORS["background_dark"])
            ],
            foreground=[
                ("disabled", COLORS["dark_light"])
            ]
        )
    
    # Entry fields
    style.configure("TEntry",
        fieldbackground=COLORS["background_light"],
        foreground=COLORS["dark"],
        padding=5,
        insertcolor=COLORS["primary"]
    )
    
    # Combobox
    style.configure("TCombobox",
        fieldbackground=COLORS["background_light"],
        foreground=COLORS["dark"],
        selectbackground=COLORS["primary_light"]
    )
    
    # Scrollbars
    style.configure("TScrollbar",
        background=COLORS["secondary"],
        troughcolor=COLORS["background_dark"],
        gripcount=0,
        arrowsize=12
    )
    style.map("TScrollbar",
        background=[("active", COLORS["secondary_dark"])]
    )
    
    # Progressbar
    style.configure("Horizontal.TProgressbar",
        background=COLORS["primary"],
        troughcolor=COLORS["background_dark"],
        thickness=12,
        bordercolor=COLORS["background"],
        lightcolor=COLORS["primary_light"],
        darkcolor=COLORS["primary_dark"]
    )
    
    # Notebook (tabs)
    style.configure("TNotebook",
        background=COLORS["background_dark"],
        tabmargins=(2, 2, 2, 0)
    )
    style.configure("TNotebook.Tab",
        background=COLORS["secondary"],
        foreground=COLORS["dark"],
        padding=(10, 5),
        font=FONTS["body"]
    )
    style.map("TNotebook.Tab",
        background=[
            ("selected", COLORS["background"]),
            ("active", COLORS["secondary_light"])
        ],
        expand=[("selected", (1, 1, 1, 0))]
    )
    
    # Treeview (for tables/lists)
    style.configure("Treeview",
        background=COLORS["background_light"],
        foreground=COLORS["dark"],
        fieldbackground=COLORS["background_light"],
        rowheight=25
    )
    style.configure("Treeview.Heading",
        background=COLORS["secondary"],
        foreground=COLORS["dark"],
        font=FONTS["body_bold"],
        padding=(5, 5, 5, 5)
    )
    style.map("Treeview",
        background=[("selected", COLORS["primary_light"])],
        foreground=[("selected", COLORS["dark"])]
    )
    
    # Toolbutton style for view mode toggles
    style.configure("Toolbutton",
        font=FONTS["body"],
        padding=5,
        relief="flat"
    )
    style.map("Toolbutton",
        background=[
            ("selected", COLORS["primary_light"]),
            ("active", COLORS["secondary_light"])
        ],
        relief=[("pressed", "sunken")]
    )
    
    # Bold label style
    style.configure("Bold.TLabel",
        font=FONTS["body_bold"]
    )

    # Add hover effects for all buttons
    style.map("TButton",
        background=[
            ("active", COLORS["primary_dark"]),
            ("pressed", COLORS["primary_dark"]),
            ("disabled", COLORS["background_dark"])
        ],
        foreground=[
            ("disabled", COLORS["dark_light"])
        ],
        relief=[
            ("pressed", "sunken"),
            ("!pressed", "raised")
        ]
    )

