"""
ZIM Converter Package

A modular package for converting static websites to ZIM archive format.
"""

from .zim_item import MyItem
from .validation import validate_language_code, validate_filename, sanitize_filename
from .config import setup_logging, load_config
from .image_optimizer import optimize_image, is_pillow_available
from .report_generator import generate_link_validation_report
from .mime_types import MIME_TYPES, get_mime_type
from .file_processor import process_html_content, process_dry_run, process_files, cleanup_unreferenced
from .external_deps import resolve_external_dependencies, replace_external_urls

__all__ = [
    'MyItem',
    'validate_language_code',
    'validate_filename',
    'sanitize_filename',
    'setup_logging',
    'load_config',
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
]

__version__ = '1.0.0'
