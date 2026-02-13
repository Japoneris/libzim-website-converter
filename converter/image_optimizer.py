"""
Image optimization utilities for reducing ZIM file size.
"""

import logging

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


def optimize_image(image_path, max_width=1920, quality=85):
    """
    Optimize image by resizing and compressing.

    Args:
        image_path: Path to image file
        max_width: Maximum width for resizing
        quality: JPEG quality (1-100)

    Returns:
        tuple: (optimized_data, original_size, new_size) or None if failed/not needed
    """
    if not PILLOW_AVAILABLE:
        return None

    try:
        with Image.open(image_path) as img:
            original_size = image_path.stat().st_size

            if original_size < 50 * 1024:
                return None

            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            from io import BytesIO
            output = BytesIO()

            fmt = img.format or 'PNG'
            if fmt == 'JPEG' or fmt == 'JPG':
                img.save(output, format='JPEG', quality=quality, optimize=True)
            elif fmt == 'PNG':
                img.save(output, format='PNG', optimize=True)
            else:
                return None

            new_size = output.tell()

            if new_size < original_size:
                return (output.getvalue(), original_size, new_size)

            return None

    except Exception as e:
        logging.debug(f"Failed to optimize image {image_path}: {e}")
        return None


def is_pillow_available():
    """Check if Pillow library is available."""
    return PILLOW_AVAILABLE
