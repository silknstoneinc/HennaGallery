"""
Environment utility functions for Henna Gallery Editor.
Handles system and dependency validation.
"""

from __future__ import annotations
import sys
import platform
from typing import Dict, Tuple, List
from pathlib import Path

def validate_environment(requirements: List[str] = None) -> Dict[str, Any]:
    """
    Validate the system environment meets requirements.
    
    Args:
        requirements: List of required packages (optional)
        
    Returns:
        Dictionary with:
        - os_info: Operating system details
        - python_version: Python version
        - missing_packages: List of missing packages
        - all_valid: Boolean if all requirements met
    """
    result = {
        'os_info': {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version()
        },
        'python_version': sys.version.split()[0],
        'missing_packages': [],
        'all_valid': True
    }
    
    if requirements:
        try:
            from importlib.metadata import distribution
            for pkg in requirements:
                try:
                    distribution(pkg)
                except:
                    result['missing_packages'].append(pkg)
            result['all_valid'] = len(result['missing_packages']) == 0
        except ImportError:
            # Fallback for older Python versions
            import pkg_resources
            for pkg in requirements:
                try:
                    pkg_resources.get_distribution(pkg)
                except:
                    result['missing_packages'].append(pkg)
            result['all_valid'] = len(result['missing_packages']) == 0
    
    return result