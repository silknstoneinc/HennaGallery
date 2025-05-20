"""
Google Vision API processor for image analysis.
Handles all interactions with the Google Cloud Vision API.
"""

from google.cloud import vision
from typing import List
import os
from PIL import Image, UnidentifiedImageError
from pathlib import Path

from config import SUPPORTED_EXTENSIONS
from utils.image_utils import compute_image_hash
from .exceptions import ImageProcessingError

class VisionProcessor:
    """
    Handles image processing using Google Cloud Vision API.
    
    Attributes:
        client: Google Vision API client
    """
    
    def __init__(self):
        """Initialize the Vision API client."""
        try:
            self.client = vision.ImageAnnotatorClient()
        except Exception as e:
            raise ImageProcessingError(f"Failed to initialize Vision API client: {str(e)}")

    def analyze_image(self, image_path: Path) -> List[str]:
        """
        Analyze an image using Google Vision API and return relevant labels.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of detected labels (strings)
            
        Raises:
            ImageProcessingError: If analysis fails
        """
        if not image_path.exists():
            raise ImageProcessingError(f"Image file not found: {image_path}")
            
        if image_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ImageProcessingError(f"Unsupported image format: {image_path.suffix}")

        try:
            # Validate the image first
            self._validate_image(image_path)
            
            # Perform Vision API analysis
            with open(image_path, 'rb') as img_file:
                content = img_file.read()
            
            image = vision.Image(content=content)
            response = self.client.label_detection(image=image)
            
            # Extract and return the top 6 labels
            return [label.description.lower() for label in response.label_annotations][:6]
            
        except Exception as e:
            raise ImageProcessingError(f"Vision API error on {image_path.name}: {str(e)}")

    def _validate_image(self, image_path: Path) -> bool:
        """
        Validate that a file is a proper image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            True if valid image, False otherwise
            
        Raises:
            ImageProcessingError: If image is invalid
        """
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except (IOError, UnidentifiedImageError) as e:
            raise ImageProcessingError(f"Invalid image file {image_path.name}: {str(e)}")

    def generate_alt_text(self, caption: str, keywords: List[str]) -> str:
        """
        Generate alt text for images based on caption and keywords.
        
        Args:
            caption: Image caption
            keywords: List of keywords/tags
            
        Returns:
            Generated alt text string
        """
        if caption:
            return f"Detailed view of {caption.lower()}"
        elif keywords:
            return f"Close-up of {' '.join(keywords[:3])}"
        return "Henna design close-up"

    def generate_headline(self, caption: str, keywords: List[str]) -> str:
        """
        Generate headline for images based on caption and keywords.
        
        Args:
            caption: Image caption
            keywords: List of keywords/tags
            
        Returns:
            Generated headline string
        """
        if keywords:
            return keywords[0].capitalize()
        elif caption:
            return caption.split()[0].capitalize()
        return "Henna Art"