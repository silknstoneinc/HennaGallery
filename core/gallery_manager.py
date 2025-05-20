"""
Core gallery management functionality.
Handles folder processing, image organization, and metadata management.
Updated with transaction safety and proper imports.
"""

import json
import os
import time
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Callable, Optional, Tuple
from collections import defaultdict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config import (
    SUPPORTED_EXTENSIONS,
    HASH_TRACK_FILE,
    THUMBNAIL_SIZE,
    BATCH_SIZE,
    EXPORT_PROFILES
)
from .vision_processor import VisionProcessor
from .exceptions import GalleryManagerError, ImageProcessingError
from utils.file_utils import (
    load_json_data,
    save_json_data,
    ensure_directory_exists,
    compute_image_hash,
    slugify
)
from utils.image_utils import validate_image_file, extract_dominant_colors

class FolderWatcher(FileSystemEventHandler):
    """Main class for managing gallery folders and images with v2.0 schema support."""
    
    def __init__(self, callback: Callable[[str], None]):
        """
        Initialize the folder watcher.
        
        Args:
            callback: Function to call when changes are detected
        """
        super().__init__()
        self.callback = callback
        self.observer = Observer()
        
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory and event.src_path.lower().endswith(SUPPORTED_EXTENSIONS):
            self.callback(os.path.dirname(event.src_path))

    def watch(self, path: str) -> None:
        """Start watching the specified path."""
        self.observer.schedule(self, path, recursive=True)
        self.observer.start()

    def stop(self) -> None:
        """Stop the folder watcher."""
        self.observer.stop()
        self.observer.join()


class GalleryManager:
    """Main class for managing gallery folders and images."""
    
    def __init__(self):
        """Initialize the gallery manager with a vision processor."""
        self.vision = VisionProcessor()
        self.watcher = None

    def _folder_transaction(self, folder_path: Path):
        """Context manager for transaction safety"""
        json_path = folder_path / f"{folder_path.name}.json"
        backup = json_path.with_suffix('.bak')
        
        class Transaction:
            def __enter__(tx_self):
                if json_path.exists():
                    shutil.copy2(json_path, backup)
            
            def __exit__(tx_self, *exc):
                if any(exc) and backup.exists():
                    shutil.copy2(backup, json_path)
                backup.unlink(missing_ok=True)
        
        return Transaction()

    def process_folder(
        self,
        folder_path: Path,
        folder_name: str,
        hash_data: Dict[str, Dict],
        updated_hashes: Dict[str, Dict],
        new_entries_all: List[Dict],
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> None:
        """
        Process all images in a folder with batch support.
        Wrapped in transaction safety.
        """
        try:
            with self._folder_transaction(folder_path):
                self._process_folder_unsafe(
                    folder_path,
                    folder_name,
                    hash_data,
                    updated_hashes,
                    new_entries_all,
                    progress_callback
                )
        except Exception as e:
            raise GalleryManagerError(f"Error processing folder {folder_name}: {str(e)}")

    def _process_folder_unsafe(
        self,
        folder_path: Path,
        folder_name: str,
        hash_data: Dict[str, Dict],
        updated_hashes: Dict[str, Dict],
        new_entries_all: List[Dict],
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> None:
        """Actual folder processing implementation with transaction safety."""
        json_path = folder_path / f"{folder_name}.json"
        
        # Load existing JSON data or create new
        json_data = []
        existing_urls = set()
        
        if json_path.exists():
            json_data = load_json_data(json_path)
            existing_urls = {entry['url'] for entry in json_data}

        # Get all valid image files in folder
        image_files = [
            f for f in os.listdir(folder_path) 
            if f.lower().endswith(SUPPORTED_EXTENSIONS) and 
            validate_image_file(folder_path / f)
        ]
        
        new_entries = []
        processed_count = 0
        batch_count = 0

        for img_file in image_files:
            try:
                full_path = folder_path / img_file
                img_hash = compute_image_hash(full_path)

                # Skip if already processed
                if img_hash in hash_data:
                    existing_info = hash_data[img_hash]
                    correct_path = folder_path / existing_info["filename"]
                    if not correct_path.exists() and img_file != existing_info["filename"]:
                        os.rename(full_path, correct_path)
                    continue

                # Skip if already in JSON but not hashed
                if img_file in existing_urls:
                    continue

                # Process new image - keep 'tags' variable for processing but store as 'keywords' in JSON
                tags = self.vision.analyze_image(full_path)
                folder_slug = slugify(folder_name)
                tag_slug = "-".join([slugify(t) for t in tags[:2]])
                hash_slug = img_hash[:6]
                new_name = f"{folder_slug}-{tag_slug}-{hash_slug}{full_path.suffix.lower()}"
                new_path = folder_path / new_name

                if not new_path.exists():
                    os.rename(full_path, new_path)

                # Add to hash tracking - keep 'tags' here for internal processing
                updated_hashes[img_hash] = {
                    "filename": new_name,
                    "tags": tags,  # Internal use only
                    "processed_date": datetime.now().isoformat()
                }

                # Create new entry - use 'keywords' instead of 'tags' in the JSON output
                new_entries.insert(0, {
                    "url": new_name,
                    "caption": f"{folder_name.title()} - {' '.join(tags[:3]).title()}",
                    "keywords": tags,  # This is the main field we'll use
                    "alt_text": self.vision.generate_alt_text(folder_name, tags),
                    "headline": self.vision.generate_headline(folder_name, tags),
                    "featured": False,
                    "order": 0,
                    # Removed the "tags" field from JSON output
                    "processed_date": datetime.now().isoformat(),
                    "modified_date": datetime.now().isoformat()
                })
                
                # Add cleanup for existing entries:
                for entry in json_data:
                    if 'categories' in entry:
                        entry['keywords'] = entry.get('keywords', []) + entry['categories']
                        del entry['categories']

                processed_count += 1
                batch_count += 1

                # Process in batches to prevent memory issues
                if batch_count >= BATCH_SIZE and progress_callback:
                    progress_callback(folder_name, processed_count, len(image_files))
                    batch_count = 0
                    time.sleep(1)  # Brief pause between batches

            except ImageProcessingError as e:
                print(f"Skipping {img_file}: {str(e)}")
                continue

        # Update order for existing entries
        for entry in json_data:
            entry["order"] = entry.get("order", 0) + len(new_entries)
            # Clean existing entries by moving 'tags' to 'keywords' if needed
            if 'tags' in entry and 'keywords' not in entry:
                entry['keywords'] = entry['tags']
                del entry['tags']

        # Combine new and existing entries (new first)
        combined = new_entries + [
            entry for entry in json_data 
            if entry['url'] not in {e['url'] for e in new_entries}
        ]
        
        # Save updated JSON
        save_json_data(json_path, combined)

        new_entries_all.extend(new_entries)
        
        if progress_callback:
            progress_callback(folder_name, processed_count, len(image_files))

    def start_folder_watcher(self, path: str, callback: Callable[[str], None]) -> None:
        """
        Start watching a folder for changes.
        
        Args:
            path: Path to watch
            callback: Function to call when changes are detected
        """
        if self.watcher:
            self.watcher.stop()
        
        self.watcher = FolderWatcher(callback)
        self.watcher.watch(path)

    def stop_folder_watcher(self) -> None:
        """Stop watching folders for changes."""
        if self.watcher:
            self.watcher.stop()
            self.watcher = None