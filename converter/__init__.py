"""
ZIM Converter Package

A modular package for converting static websites to ZIM archive format.
"""

from .config import load_config, setup_logging, validate_config
from .external_deps import replace_external_urls, resolve_external_dependencies
from .file_processor import (
    cleanup_unreferenced,
    process_dry_run,
    process_files,
    process_html_content,
)
from .image_optimizer import is_pillow_available, optimize_image
from .mime_types import MIME_TYPES, get_mime_type
from .path_utils import resolve_main_page
from .report_generator import generate_link_validation_report
from .validation import sanitize_filename, validate_filename, validate_language_code
from .zim_item import MyItem

__all__ = [
    'MyItem',
    'validate_language_code',
    'validate_filename',
    'sanitize_filename',
    'setup_logging',
    'load_config',
    'validate_config',
    'optimize_image',
    'is_pillow_available',
    'generate_link_validation_report',
    'MIME_TYPES',
    'get_mime_type',
    'process_html_content',
    'process_dry_run',
    'process_files',
    'cleanup_unreferenced',
    'resolve_external_dependencies',
    'replace_external_urls',
    'resolve_main_page',
]

__version__ = '1.0.0'
