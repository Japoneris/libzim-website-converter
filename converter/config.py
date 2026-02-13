"""
Configuration and logging setup utilities.
"""

import json
import logging
import sys
from pathlib import Path


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
    Load configuration from JSON file if it exists.

    Args:
        config_path: Path to JSON configuration file

    Returns:
        dict: Configuration dictionary (empty if failed)
    """
    config_file = Path(config_path)
    if not config_file.exists():
        return {}

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in config file: {e}")
        return {}
    except Exception as e:
        logging.error(f"Failed to load config file: {e}")
        return {}
