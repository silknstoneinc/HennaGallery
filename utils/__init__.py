"""
Utilities package for Henna Gallery application.
Contains helper functions and tools.
"""

# Import utility modules
from .image_utils import (
    validate_image_file,
    compute_image_hash,
    generate_thumbnail,
    resize_image,
    convert_to_webp,
    get_image_metadata,
    normalize_image_orientation,
    create_image_preview
)
from .file_utils import (
    slugify,
    ensure_directory_exists,
    load_json_data,
    save_json_data,
    get_files_by_extensions,
    safe_rename,
    copy_file_with_backup,
    get_file_modified_time,
    get_directory_size,
    create_unique_filename,
    sanitize_filename
)
from .thread_utils import (
    run_in_thread,
    schedule_callback,
    process_pending_callbacks,
    ThreadPool,
    CancellableTask
)

__all__ = [
    # Image utils
    'validate_image_file',
    'compute_image_hash',
    'generate_thumbnail',
    'resize_image',
    'convert_to_webp',
    'get_image_metadata',
    'normalize_image_orientation',
    'create_image_preview',
    
    # File utils
    'slugify',
    'ensure_directory_exists',
    'load_json_data',
    'save_json_data',
    'get_files_by_extensions',
    'safe_rename',
    'copy_file_with_backup',
    'get_file_modified_time',
    'get_directory_size',
    'create_unique_filename',
    'sanitize_filename',
    
    # Thread utils
    'run_in_thread',
    'schedule_callback',
    'process_pending_callbacks',
    'ThreadPool',
    'CancellableTask'
]