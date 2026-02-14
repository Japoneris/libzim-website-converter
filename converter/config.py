"""
Configuration and logging setup utilities.
"""

import json
import logging
import sys
from pathlib import Path


# Default values for optional config fields
CONFIG_DEFAULTS = {
    "output_path": "zim_files",
    "icon": "icons/comment.png",
    "publisher": "You",
    "resolve_external": False,
    "cleanup": False,
    "optimize_images": False,
    "max_image_width": 1920,
    "image_quality": 85,
}

# Fields that must be present in the config file
REQUIRED_FIELDS = ["site_path", "name", "title", "creator", "description", "language"]


def setup_logging(verbose=False, quiet=False):
    """
    Configure logging based on verbosity settings.

    Args:
        verbose: Enable DEBUG level logging
        quiet: Enable ERROR level logging only

    Returns:
        Logger instance
    """
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        stream=sys.stdout
    )
    return logging.getLogger(__name__)


def load_config(config_path):
    """
    Load configuration from JSON file.

    Args:
        config_path: Path to JSON configuration file

    Returns:
        dict: Configuration dictionary

    Raises:
        SystemExit: If the file doesn't exist or has invalid JSON
    """
    config_file = Path(config_path)
    if not config_file.exists():
        logging.error(f"Config file not found: {config_path}")
        sys.exit(1)

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in config file: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Failed to load config file: {e}")
        sys.exit(1)


def validate_config(config):
    """
    Validate required fields and apply defaults for optional fields.

    Args:
        config: Configuration dictionary loaded from JSON

    Returns:
        dict: Config with defaults applied

    Raises:
        SystemExit: If required fields are missing
    """
    missing = [f for f in REQUIRED_FIELDS if not config.get(f)]
    if missing:
        logging.error(f"Missing required config fields: {', '.join(missing)}")
        logging.error(f"Required fields: {', '.join(REQUIRED_FIELDS)}")
        sys.exit(1)

    # Apply defaults for optional fields
    for key, default in CONFIG_DEFAULTS.items():
        config.setdefault(key, default)

    return config
