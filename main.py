#!/usr/bin/env python3
"""Main entry point with window identification"""
import sys
import os
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Set up correct base path depending on if frozen or not
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_DIR = os.path.join(BASE_DIR, "config")
CACHE_FILE = os.path.join(BASE_DIR, "file_cache.json")

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from gui.main_window import MainWindow
from config import load_config

CREDENTIAL_FOLDER = PROJECT_ROOT / "config"
CREDENTIAL_FILENAME = "silknstoneproduction_vision_api_key.json"
CREDENTIAL_PATH = CREDENTIAL_FOLDER / CREDENTIAL_FILENAME


def ensure_google_credentials():
    """Ensure Google Vision API credentials are available, or prompt user to select them"""
    if not CREDENTIAL_PATH.exists():
        # Temporarily initialize a hidden root window for dialogs
        temp_root = tk.Tk()
        temp_root.withdraw()

        messagebox.showinfo(
            "Google Credential Missing",
            "Please select your Google Vision API credential JSON file to proceed."
        )

        selected_file = filedialog.askopenfilename(
            title="Select Google Vision Credential JSON File",
            filetypes=[("JSON files", "*.json")]
        )

        if not selected_file:
            messagebox.showerror(
                "Credential Required",
                "Credential file is required to use this app. Exiting now."
            )
            sys.exit(1)

        os.makedirs(CREDENTIAL_FOLDER, exist_ok=True)
        shutil.copy(selected_file, CREDENTIAL_PATH)
        messagebox.showinfo("Success", "Credential file saved successfully.")

    # Set environment variable
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(CREDENTIAL_PATH)


class Application:
    def __init__(self):
        # ✅ Phase 0: Ensure credentials
        ensure_google_credentials()

        # ✅ Phase 1: Configuration (loads API client)
        self.config = load_config()

        # ✅ Phase 2: GUI setup
        self.root = tk.Tk()
        self._setup_root_window()
        self.main_window = MainWindow(self.root, self.config)
        self.root.mainloop()

    def _setup_root_window(self):
        self.root.title("Silk & Stone Henna Gallery Tool")
        self.root.geometry("1400x950")
        self.root.minsize(1100, 800)
        self.root.configure(bg='white')


if __name__ == "__main__":
    app = Application()
