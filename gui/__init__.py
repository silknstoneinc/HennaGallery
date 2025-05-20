"""
GUI package for Henna Gallery application.
Contains all user interface components.
"""

# Import main UI components
from .main_window import MainWindow
from .left_panel import LeftPanel
from .center_panel import CenterPanel
from .right_panel import RightPanel
from .status_bar import StatusBar
from .styles import COLORS, FONTS, configure_styles

__all__ = [
    'MainWindow',
    'LeftPanel',
    'CenterPanel',
    'RightPanel',
    'StatusBar',
    'COLORS',
    'FONTS',
    'configure_styles'
]