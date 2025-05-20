"""
Custom exceptions for the Henna Gallery application.
Provides specific exception classes for different error scenarios.
"""

class ImageProcessingError(Exception):
    """Exception raised for errors during image processing."""
    def __init__(self, message: str = "Image processing error occurred"):
        self.message = message
        super().__init__(self.message)

class GalleryConfigError(Exception):
    """Exception raised for configuration-related errors."""
    def __init__(self, message: str = "Gallery configuration error occurred"):
        self.message = message
        super().__init__(self.message)

class GalleryManagerError(Exception):
    """Exception raised for gallery management errors."""
    def __init__(self, message: str = "Gallery management error occurred"):
        self.message = message
        super().__init__(self.message)

class VisionAPIError(Exception):
    """Exception raised for Google Vision API related errors."""
    def __init__(self, message: str = "Vision API error occurred"):
        self.message = message
        super().__init__(self.message)

class FileValidationError(Exception):
    """Exception raised for file validation failures."""
    def __init__(self, message: str = "File validation failed"):
        self.message = message
        super().__init__(self.message)

class GalleryExportError(Exception):
    """Exception raised during gallery data export."""
    def __init__(self, message: str = "Export operation failed", problematic_files=None):
        self.message = message
        self.problematic_files = problematic_files or []
        super().__init__(self.message)

class ThreadOperationError(Exception):
    """Exception raised for threading-related errors."""
    def __init__(self, message: str = "Thread operation failed"):
        self.message = message
        super().__init__(self.message)

class UIError(Exception):
    """Exception raised for user interface related errors."""
    def __init__(self, message: str = "UI operation failed"):
        self.message = message
        super().__init__(self.message)

class DragOperationError(Exception):
    """Raised for drag-and-drop operation failures"""
    def __init__(self, message, operation_type=None):
        self.operation_type = operation_type
        super().__init__(message)