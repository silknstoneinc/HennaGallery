"""
JSON migration system for gallery data (v1.x → v2.0).

Handles:
- Detection of legacy JSON formats
- Schema-compliant transformation
- Backup creation
- Metadata generation

Dependencies:
- schema_validator (for validation)
- datetime (for timestamp generation)
"""

"""
Handles migration of all legacy JSON formats to v2.0 schema.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Union
import shutil
from .schema_validator import SchemaValidator
import hashlib
from pathlib import Path
import tkinter.messagebox as messagebox

class JsonMigrator:
    """
    Handles all legacy JSON format migrations with improved detection.
    """
    
    def __init__(self, backup_dir: str = "backups"):
        self.validator = SchemaValidator()
        self.backup_dir = backup_dir

    def detect_format(self, data: Union[Dict, List]) -> str:
        """
        Detect JSON format version with improved checks
        
        Returns:
            "v1" - Dict with 'title' and 'images'
            "v1a" - Direct array of images
            "v2" - Valid v2.0 format
            "unknown" - Unrecognized
        """
        if isinstance(data, dict):
            if 'meta' in data and 'images' in data:
                return "v2"
            elif 'images' in data:
                return "v1"
        elif isinstance(data, list):
            return "v1a"
        return "unknown"

    def needs_migration(self, file_path: Path) -> bool:
        """Check if file needs migration"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self.detect_format(data) != "v2"
        except (json.JSONDecodeError, OSError):
            return False

    def migrate_file(self, file_path: Path, parent_window=None) -> bool:
        """
        Safe migration with backup and user confirmation
        Returns True if migration succeeded or was unnecessary
        """
        if not self.needs_migration(file_path):
            return True
            
        try:
            # Load original data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Create verified backup
            backup_path = self._create_backup(file_path)
            
            # Get user confirmation
            if parent_window:
                confirm = messagebox.askyesno(
                    "Update Required",
                    f"Gallery {file_path.stem} needs format update.\n"
                    f"Backup created at: {backup_path}\n"
                    "Proceed with automatic update?",
                    parent=parent_window
                )
                if not confirm:
                    return False
            
            # Perform migration
            migrated_data = self._migrate_data(data, file_path.parent)
            
            # Save migrated file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(migrated_data, f, indent=2, ensure_ascii=False)
            return True
            
        except Exception as e:
            print(f"Migration failed for {file_path}: {str(e)}")
            return False

    def _migrate_data(self, data: Union[Dict, List], folder_path: Path) -> Dict:
        """Ensure we always return proper v2 structure"""
        format_type = self.detect_format(data)
        folder_name = folder_path.name
        now = datetime.now().isoformat()
        
        # Base v2 structure
        result = {
            "meta": {
                "gallery_title": folder_name,
                "gallery_slug": folder_name.lower().replace(" ", "-"),
                "created_date": now,
                "last_updated": now,
                "export_profiles": []
            },
            "images": []
        }
        
        # Handle different formats
        if format_type == "v1":
            result["meta"].update({
                "gallery_title": data.get("title", folder_name),
                "created_date": data.get("created", now)
            })
            result["images"] = data.get("images", [])
        elif format_type == "v1a":
            result["images"] = data
        elif format_type == "v2":
            return data  # Already correct format
            
        # Transform images
        for img in result["images"]:
            if 'categories' in img:
                img['keywords'] = img.get('keywords', []) + img['categories']
                del img['categories']
            if 'tags' in img and 'keywords' not in img:
                img['keywords'] = img['tags']
                
        return result
        
    def migrate_any_to_v2(self, legacy_data: Union[Dict, List], folder_path: str) -> Dict:
        """
        Enhanced migrator with:
        - Field normalization
        - Type coercion
        - Default value injection
        """
        
        format_type = self.detect_format(legacy_data)
        folder_name = Path(folder_path).name
        now = datetime.now().isoformat()
        
        # Base v2 structure
        migrated = {
            "meta": {
                "gallery_title": folder_name,
                "gallery_slug": folder_name.lower().replace(" ", "-"),
                "created_date": now,
                "last_updated": now,
                "export_profiles": []
            },
            "images": []
        }
        
        # Handle different formats
        if format_type == "v1":
            migrated["meta"].update({
                "gallery_title": legacy_data.get("title", folder_name),
                "created_date": legacy_data.get("created", now)
            })
            image_list = legacy_data.get("images", [])
        elif format_type == "v1a":
            image_list = legacy_data
        else:
            return legacy_data  # Already v2 or unknown
            
        # Transform images
         # Transform images - preserve ALL fields
        for idx, img in enumerate(image_list):
            migrated_img = {
                "src": img.get("url") or img.get("filename", f"image_{idx}.jpg"),
                "keywords": self._normalize_keywords(
                    img.get('keywords', []),
                    img.get('tags', []),
                    img.get('categories', [])
                ),
                # Preserve all existing fields
                **{k: v for k, v in img.items() 
                if k not in ('url', 'filename', 'tags', 'categories')}
            }
            
            # Special handling for order/sort_order
            if 'order' not in migrated_img and 'sort_order' in img:
                migrated_img['order'] = img['sort_order']
                
            migrated["images"].append(migrated_img)
        
        return migrated

    def _normalize_keywords(self, *keyword_sources: List) -> List[str]:
        """
        Consolidates keywords from multiple legacy fields.
        
        Args:
            *keyword_sources: Multiple keyword lists to merge
            
        Returns:
            Single deduplicated list of strings
        """
        keywords = set()
        for source in keyword_sources:
            if isinstance(source, list):
                keywords.update(str(kw).strip().lower() for kw in source if kw)
            elif source:
                keywords.add(str(source).strip().lower())
        return sorted(keywords)

    def safe_migrate_file(self, file_path: Path, parent_window=None) -> bool:
        """Safe migration with better error handling and debugging"""
        try:
            # Debug: Print file being processed (KEEP EXISTING)
            print(f"Attempting to migrate: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Debug: Print detected format (KEEP EXISTING)
            file_format = self.detect_format(data)
            print(f"Detected format: {file_format}")
            
            # Skip if already v2 and valid (KEEP EXISTING BUT ENHANCE VALIDATION)
            if file_format == "v2" and self.validator.validate_gallery(data):
                print("File is already v2 and valid")
                # ADDED: Normalize image indices even if format is valid
                data = self._normalize_image_indices(data, file_path.parent)
                if not self.validator.validate_gallery(data):
                    print("Found inconsistencies in valid v2 file, fixing...")
                    data = self._normalize_image_indices(data, file_path.parent)
                
                # Save normalized data
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                return True
                
            # Create verified backup (KEEP EXISTING)
            try:
                backup_path = self._create_backup(file_path)
                print(f"Created backup at: {backup_path}")
            except Exception as backup_error:
                print(f"Backup failed: {str(backup_error)}")
                if parent_window:
                    messagebox.showerror("Backup Failed", 
                        f"Could not create backup:\n{str(backup_error)}", 
                        parent=parent_window)
                return False
            
            # Get user confirmation if needed (KEEP EXISTING)
            if parent_window and file_format != "v2":
                confirm = messagebox.askyesno(
                    "Update Required",
                    f"Gallery {file_path.stem} needs format update.\n"
                    f"Backup created at: {backup_path}\n"
                    "Proceed with automatic update?",
                    parent=parent_window
                )
                if not confirm:
                    print("User cancelled migration")
                    return False
            
            # Perform migration (KEEP EXISTING BUT ADD NORMALIZATION)
            migrated_data = self.migrate_any_to_v2(data, file_path.parent)
            print("Migration completed, validating...")
            
            # ADDED: Normalize image indices after migration
            migrated_data = self._normalize_image_indices(migrated_data, file_path.parent)
            
            # Validate before saving (KEEP EXISTING)
            if not self.validator.validate_gallery(migrated_data):
                errors = self.validator.get_validation_errors(migrated_data)
                print(f"Validation failed: {errors}")
                if parent_window:
                    messagebox.showerror(
                        "Validation Failed",
                        "Could not migrate due to validation errors:\n" + 
                        "\n".join(errors),
                        parent=parent_window
                    )
                return False
            
            # Save migrated file (KEEP EXISTING)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(migrated_data, f, indent=2, ensure_ascii=False)
            
            print("Migration successful")
            return True
            
        except Exception as e:
            error_msg = f"Migration failed for {file_path}: {str(e)}"
            print(error_msg)
            if parent_window:
                messagebox.showerror("Migration Error", error_msg, parent=parent_window)
            return False

    def _normalize_image_indices(self, gallery_data: Dict, folder_path: Path) -> Dict:
        """NEW: Ensure consistent image indices and validate file existence"""
        if not isinstance(gallery_data.get('images'), list):
            return gallery_data
        
        validated_images = []
        for i, img in enumerate(gallery_data['images']):
            try:
                # Normalize required fields
                img = {**img}  # Create copy to avoid modifying original
                
                # Ensure src/url consistency
                img_path = Path(folder_path) / (img.get('url') or img.get('src', f'image_{i}.jpg'))
                img['src'] = str(img_path.name)
                img['url'] = str(img_path.name)
                img['filename'] = img_path.name
                                
                # Only keep if file exists
                if img_path.exists():
                    validated_images.append(img)
                else:
                    print(f"Skipping missing image file: {img_path}")
                    
            except Exception as e:
                print(f"Skipping invalid image {i}: {str(e)}")

        # Update ALL images with correct total count
        for i, img in enumerate(validated_images):
            img['index'] = i
            img['order'] = i
            img['total'] = len(validated_images)  # <-- Use validated count
        
        return {
            **gallery_data,
            'images': validated_images
        }
        
    def _create_backup(self, original_path: Path) -> Path:
        """
        Creates a timestamped backup with checksum verification.
        
        Args:
            original_path: Path to original JSON file
            
        Returns:
            Path to backup file
            
        Raises:
            IOError: If backup fails
        """
        backup_dir = Path(self.backup_dir)
        backup_dir.mkdir(exist_ok=True, parents=True)
        
        # Generate unique backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{original_path.stem}_v2backup_{timestamp}{original_path.suffix}"
        
        # Create checksum of original
        original_checksum = hashlib.md5(original_path.read_bytes()).hexdigest()
        
        # Atomic copy operation
        temp_path = backup_path.with_suffix('.tmp')
        shutil.copy2(original_path, temp_path)
        
        # Verify backup integrity
        if hashlib.md5(temp_path.read_bytes()).hexdigest() != original_checksum:
            temp_path.unlink()
            raise IOError("Backup verification failed")
            
        temp_path.rename(backup_path)
        return backup_path
    
    def check_gallery_health(self, file_path: Path) -> Dict:
        """
        Returns health status of a gallery file
        Returns: {
            'needs_migration': bool,
            'is_valid': bool,
            'backup_path': str,
            'errors': List[str]
        }
        """
        result = {
            'needs_migration': False,
            'is_valid': True,
            'backup_path': None,
            'errors': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            result['needs_migration'] = self.detect_format(data) != "v2"
            
            if not self.validator.validate_gallery(data):
                result['is_valid'] = False
                result['errors'] = self.validator.get_validation_errors(data)
                
        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f"File error: {str(e)}")
        
        return result
    