"""
Advanced Export Manager for Henna Gallery Editor
===============================================

Handles all gallery export operations with:
- Profile-based export configurations
- Parallel image processing
- HTML preview generation
- ZIP archive creation
- Comprehensive error handling

Key Features:
1. Threaded export operations for performance
2. Support for multiple export profiles
3. Automatic image resizing and optimization
4. Color palette extraction
5. Detailed error reporting

Usage:
>>> manager = ExportManager()
>>> result = manager.export_gallery(gallery_data, source_path, "web_ready")
"""

import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor

from config import EXPORT_PROFILES
from .exceptions import GalleryExportError
from utils.image_utils import extract_dominant_colors  # Added import

class ExportManager:
    """
    Central export controller for Henna Gallery.
    
    Attributes:
        executor: Thread pool for parallel processing
    """
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize export manager with thread pool.
        
        Args:
            max_workers: Maximum parallel threads (default: 4)
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def export_gallery(
        self,
        gallery_data: Dict,
        source_path: Path,
        profile_name: str = "web_ready",
        output_path: Optional[Path] = None,
        zip_output: bool = False
    ) -> Path:
        """
        Export gallery using specified profile.
        
        Args:
            gallery_data: Gallery data dictionary
            source_path: Path to source gallery folder
            profile_name: Name of export profile (default: "web_ready")
            output_path: Custom output path (optional)
            zip_output: Create ZIP archive (default: False)
            
        Returns:
            Path to exported folder or ZIP file
            
        Raises:
            GalleryExportError: If export fails with problematic files list
            
        Example:
            >>> export_path = manager.export_gallery(data, Path("gallery"))
        """
        if profile_name not in EXPORT_PROFILES:
            raise GalleryExportError(f"Unknown export profile: {profile_name}")
            
        profile = EXPORT_PROFILES[profile_name]
        gallery_slug = gallery_data['meta']['gallery_slug']
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Set up output paths
        if output_path is None:
            output_path = source_path / "exports" / f"{gallery_slug}_{profile_name}_{timestamp}"
        else:
            output_path = output_path / f"{gallery_slug}_{profile_name}_{timestamp}"
            
        (output_path / "images").mkdir(parents=True, exist_ok=True)
        (output_path / "data").mkdir(exist_ok=True)
        
        # Process images
        failed_files: List[str] = []  # Explicit type annotation
        futures = []
        
        for img_data in gallery_data['images']:
            future = self.executor.submit(
                self._export_image,
                img_data,
                source_path,
                output_path,
                profile,
                failed_files
            )
            futures.append(future)
            
        # Wait for completion
        for future in futures:
            future.result()
            
        if failed_files:
            raise GalleryExportError(
                f"Failed to process {len(failed_files)} files",
                problematic_files=failed_files
            )
        
        # Save manifest
        self._save_manifest(gallery_data, output_path)
        
        # Generate preview
        self._generate_html_preview(gallery_data, output_path)
        
        # Create ZIP if requested
        if zip_output:
            return self._create_zip_archive(output_path)
            
        return output_path
    
    def _export_image(
        self,
        img_data: Dict,
        source_path: Path,
        output_path: Path,
        profile: Dict,
        failed_files: List[str]  # Proper type annotation
    ) -> None:
        """
        Process and export a single image.
        
        Args:
            img_data: Image metadata dictionary
            source_path: Source directory path
            output_path: Output directory path
            profile: Export profile configuration
            failed_files: List to track failed exports
        """
        try:
            src_path = source_path / img_data['src']
            
            # Generate all required sizes
            img_data['srcset'] = self._generate_image_variants(
                src_path,
                output_path,
                profile['image_sizes']
            )
            
            # Extract colors if required
            if ('color_palette' in profile['required_fields'] and 
                'color_palette' not in img_data):
                img_data['color_palette'] = extract_dominant_colors(src_path)
                
        except Exception as e:
            failed_files.append(img_data['src'])
            print(f"Error processing {img_data['src']}: {str(e)}")
    
    def _generate_image_variants(
        self,
        src_path: Path,
        output_path: Path,
        size_configs: List[Tuple[str, Optional[Tuple[int, int]]]]
    ) -> Dict[str, str]:
        """
        Generate all image size variants.
        
        Args:
            src_path: Source image path
            output_path: Output directory
            size_configs: List of (name, dimensions) tuples
            
        Returns:
            Dictionary of variant names to relative paths
        """
        variants = {}
        for size_name, dimensions in size_configs:
            if dimensions is None:  # Original size
                dest_path = output_path / "images" / src_path.name
                shutil.copy2(src_path, dest_path)
                variants['original'] = f"images/{src_path.name}"
            else:
                resized_path = output_path / "images" / f"{src_path.stem}_{size_name}{src_path.suffix}"
                self._resize_image(src_path, resized_path, dimensions)
                variants[size_name] = f"images/{resized_path.name}"
        return variants
    
    def _resize_image(
        self,
        src_path: Path,
        dest_path: Path,
        dimensions: Tuple[int, int]
    ) -> None:
        """
        Resize image while maintaining aspect ratio.
        
        Args:
            src_path: Source image path
            dest_path: Destination path
            dimensions: (width, height) tuple
        """
        from PIL import Image
        img = Image.open(src_path)
        img.thumbnail(dimensions)
        img.save(dest_path, optimize=True, quality=85)
    
    def _save_manifest(
        self,
        gallery_data: Dict,
        output_path: Path
    ) -> None:
        """Save gallery manifest JSON."""
        manifest_path = output_path / "data" / "gallery.json"
        with open(manifest_path, 'w') as f:
            json.dump(gallery_data, f, indent=2)
    
    def _generate_html_preview(
        self,
        gallery_data: Dict,
        output_path: Path
    ) -> None:
        """
        Generate HTML preview of the gallery.
        
        Args:
            gallery_data: Gallery data dictionary
            output_path: Output directory path
        """
        preview_template = """<!DOCTYPE html>
        <html>
        <head>
            <title>{gallery_title} Preview</title>
            <style>
                body {{ font-family: sans-serif; margin: 20px; }}
                .gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
                .gallery-item {{ border: 1px solid #ddd; padding: 10px; border-radius: 5px; }}
                .gallery-item img {{ max-width: 100%; height: auto; }}
                .color-palette {{ display: flex; margin-top: 10px; }}
                .color-swatch {{ width: 30px; height: 30px; margin-right: 5px; }}
            </style>
        </head>
        <body>
            <h1>{gallery_title}</h1>
            <div class="gallery">{items}</div>
        </body>
        </html>"""
        
        item_template = """
        <div class="gallery-item">
            <img src="{image_url}" alt="{alt_text}">
            <h3>{headline}</h3>
            <div class="color-palette">{color_swatches}</div>
        </div>"""
        
        items_html = [
            item_template.format(
                image_url=img['srcset'].get('md', img['src']),
                alt_text=img['alt_text'],
                headline=img.get('headline', 'Henna Design'),
                color_swatches="".join(
                    f'<div class="color-swatch" style="background-color: {color};"></div>'
                    for color in img.get('color_palette', [])
                )
            )
            for img in gallery_data['images']
        ]
        
        with open(output_path / "preview.html", 'w') as f:
            f.write(preview_template.format(
                gallery_title=gallery_data['meta']['gallery_title'],
                items="\n".join(items_html)
            ))
    
    def _create_zip_archive(self, output_path: Path) -> Path:
        """
        Create ZIP archive of exported gallery.
        
        Args:
            output_path: Path to exported folder
            
        Returns:
            Path to created ZIP file
        """
        zip_path = output_path.parent / f"{output_path.name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in output_path.rglob('*'):
                zipf.write(file, file.relative_to(output_path.parent))
        shutil.rmtree(output_path)
        return zip_path