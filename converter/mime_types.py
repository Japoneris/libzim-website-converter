"""
MIME type mappings for common file extensions.

Source: https://developer.mozilla.org/fr/docs/Web/HTTP/MIME_types/Common_types
"""

MIME_TYPES = {
    "bin": "application/octet-stream",
    "bmp": "image/bmp",
    "bz": "application/x-bzip",
    "bz2": "application/x-bzip2",
    "pdf": "application/pdf",
    "css": "text/css",
    "csv": "text/csv",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "epub": "application/epub+zip",
    "gif": "image/gif",
    "ico": "image/x-icon",
    "ics": "text/calendar",
    "jar": "application/java-archive",
    "js": "application/javascript",
    "json": "application/json",
    "mid": "audio/midi",
    "midi": "audio/midi",
    "mpeg": "video/mpeg",
    "mp4": "video/mp4",
    "odp": "application/vnd.oasis.opendocument.presentation",
    "ods": "application/vnd.oasis.opendocument.spreadsheet",
    "odt": "application/vnd.oasis.opendocument.text",
    "otf": "font/otf",
    "ppt": "application/vnd.ms-powerpoint",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "rar": "application/x-rar-compressed",
    "scss": "text/x-scss",
    "sh": "application/x-sh",
    "svg": "image/svg+xml",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "xml": "application/xml",
    "tif": "image/tiff",
    "txt": "text/plain",
    "ts": "application/typescript",
    "ttf": "font/ttf",
    "woff": "font/woff",
    "woff2": "font/woff2",
    "eot": "application/vnd.ms-fontobject",
    "wav": "audio/x-wav",
    "webp": "image/webp",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "zip": "application/zip",
}


def get_mime_type(extension):
    """
    Get MIME type for a file extension.

    Args:
        extension: File extension (without dot)

    Returns:
        str: MIME type or None if not found
    """
    return MIME_TYPES.get(extension.lower())
