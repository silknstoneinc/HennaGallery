"""
JSON schema validation for gallery data (v2.0).

Updated with:
- Better handling of legacy formats
- Consistent field preservation
- Removal of duplicate methods
"""

import json
from pathlib import Path
from typing import Dict, List, Union, Any
from datetime import datetime
import jsonschema
from jsonschema import validate

# v2.0 Gallery Schema - Updated to preserve all fields
GALLERY_SCHEMA = {
    "type": "object",
    "required": ["meta", "images"],
    "properties": {
        "meta": {
            "type": "object",
            "required": ["gallery_title"],
            "properties": {
                "gallery_title": {"type": "string"},
                "gallery_slug": {"type": ["string", "null"]},
                "created_date": {"type": ["string", "null"], "format": "date-time"},
                "last_updated": {"type": ["string", "null"], "format": "date-time"},
                "export_profiles": {"type": "array"}
            },
            "additionalProperties": True  # Allow other meta fields
        },
        "images": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["src"],
                "properties": {
                    "src": {"type": "string"},
                    "url": {"type": "string"},  # Keep for backward compatibility
                    "filename": {"type": "string"},  # Keep for backward compatibility
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "tags": {"type": "array", "items": {"type": "string"}},  # Keep for backward compatibility
                    "alt_text": {"type": "string"},
                    "caption": {"type": "string"},
                    "featured": {"type": "boolean"},
                    "order": {"type": "number"},
                    "sort_order": {"type": "number"},  # Keep for backward compatibility
                    "modified_date": {"type": "string", "format": "date-time"}
                },
                "additionalProperties": True  # Allow other image fields
            }
        }
    },
    "additionalProperties": True  # Allow root-level extra fields
}

class SchemaValidator:
    """
    Enhanced validator with:
    - Legacy format handling
    - Field preservation
    - Better error reporting
    """
    
    def __init__(self, schema: Dict = GALLERY_SCHEMA):
        self.schema = schema
        self.validator = jsonschema.Draft7Validator(schema)
    
    def ensure_v2_format(self, data: Union[Dict, List]) -> Dict:
        """Convert any format to proper v2 structure while preserving all fields"""
        if isinstance(data, list):
            return {
                "meta": self._generate_default_meta(),
                "images": self._normalize_images(data)
            }
        elif isinstance(data, dict):
            if 'images' not in data:
                data['images'] = []
            if 'meta' not in data:
                data['meta'] = self._generate_default_meta()
            data['images'] = self._normalize_images(data.get('images', []))
            return data
        return {
            "meta": self._generate_default_meta(),
            "images": []
        }
    
    def _normalize_images(self, images: List) -> List:
        """Ensure all images have required fields and preserve legacy fields"""
        normalized = []
        for img in images:
            # Ensure src exists (prefer url if available for backward compatibility)
            img.setdefault('src', img.get('url', ''))
            # Preserve all fields
            normalized_img = {
                **img,
                'keywords': self._normalize_keywords(
                    img.get('keywords', []),
                    img.get('tags', []),
                    img.get('categories', [])
                )
            }
            # Remove empty fields
            normalized.append({k: v for k, v in normalized_img.items() if v is not None})
        return normalized
    
    def validate_gallery(self, gallery_data: Union[Dict, List]) -> bool:
        """Handle both v1 and v2 formats during validation"""
        try:
            # Convert to v2 format if needed
            gallery_data = self.ensure_v2_format(gallery_data)
            
            # Validate against schema
            validate(instance=gallery_data, schema=self.schema)
            return True
            
        except jsonschema.ValidationError as e:
            print(f"Validation error: {e.message}")
            return False
    
    def get_validation_errors(self, gallery_data: Dict) -> List[str]:
        """Get detailed validation error messages."""
        errors = []
        gallery_data = self.ensure_v2_format(gallery_data)
        
        for error in sorted(self.validator.iter_errors(gallery_data), key=str):
            errors.append(f"{error.json_path}: {error.message}")
        return errors
    
    def _generate_default_meta(self) -> Dict:
        """Generate default metadata for migrated files"""
        return {
            "gallery_title": "Migrated Gallery",
            "gallery_slug": "migrated-gallery",
            "created_date": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "export_profiles": []
        }
    
    def _normalize_keywords(self, *keyword_sources: List) -> List[str]:
        """Consolidate keywords from multiple legacy fields"""
        keywords = set()
        for source in keyword_sources:
            if isinstance(source, list):
                keywords.update(str(kw).strip().lower() for kw in source if kw)
            elif source:
                keywords.add(str(source).strip().lower())
        return sorted(keywords)
    
    def validate_gallery_data(self, gallery_data: Dict, folder_path: Path) -> Dict:
        """Returns normalized data or raises ValidationError"""
        # First validate basic schema
        gallery_data = self.ensure_v2_format(gallery_data)
        
        if not self.validate_gallery(gallery_data):
            raise ValueError("Invalid gallery schema")
        
        # Validate and normalize images
        validated_images = []
        for i, img in enumerate(gallery_data.get('images', [])):
            try:
                # Validate image file exists
                img_path = Path(folder_path) / (img.get('url') or img['src'])
                if not img_path.exists():
                    raise ValueError(f"Image file not found: {img_path}")
                    
                # Normalize fields
                validated_img = {
                    "src": str(img_path.name),
                    "url": str(img_path.name),
                    "filename": img_path.name,
                    "index": i,
                    "order": i,
                    "total": len(gallery_data['images']),  # Will be updated later
                    **{k: v for k, v in img.items() if k not in ('src', 'url', 'filename')}
                }
                validated_images.append(validated_img)
                
            except Exception as e:
                print(f"Skipping invalid image {i}: {str(e)}")
                continue
        
        # Update total counts for all images
        for img in validated_images:
            img['total'] = len(validated_images)
        
        return {
            **gallery_data,
            "images": validated_images
        }

    def _validate_image(self, img: Dict, folder_path: Path, index: int) -> Dict:
        """Validate and normalize individual image"""
        # Ensure required fields
        if 'src' not in img and 'url' not in img:
            raise ValueError("Missing both src and url fields")
            
        # Normalize file reference
        img_path = Path(folder_path) / (img.get('url') or img['src'])
        if not img_path.exists():
            raise ValueError(f"Image file not found: {img_path}")
            
        # Normalize fields
        normalized = {
            "src": str(img_path.name),
            "url": str(img_path.name),
            "filename": img_path.name,
            "order": index,  # Force sequential ordering
            "index": index,
            "total": len(gallery_data['images']),  # Consistent total
            **{k: v for k, v in img.items() if k not in ('src', 'url', 'filename')}
        }
        
        # Validate types
        if not isinstance(normalized.get('keywords', []), list):
            normalized['keywords'] = []
            
        return normalized