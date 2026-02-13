"""
Validation and sanitization functions for ZIM metadata and filenames.
"""


def validate_language_code(lang_code):
    """
    Validate language code format (3 letters for ISO 639-3).

    Args:
        lang_code: Language code to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not lang_code or len(lang_code) != 3 or not lang_code.isalpha():
        return False
    return True


def validate_filename(filename):
    """
    Validate ZIM filename (no special characters except dash/underscore).

    Args:
        filename: Filename to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not filename:
        return False
    invalid_chars = '<>:"/\\|?*'
    return not any(char in filename for char in invalid_chars)


def sanitize_filename(filename):
    """
    Sanitize filename by replacing spaces and removing invalid characters.

    Args:
        filename: Filename to sanitize

    Returns:
        str: Sanitized filename
    """
    filename = filename.replace(' ', '-')
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename
