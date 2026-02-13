"""
External dependency resolution for ZIM archives.

Detects external URLs in HTML/CSS files, downloads them locally into
`_external/` within the site directory, and provides URL rewriting
so resources work offline.
"""

import hashlib
import logging
import os
import re
import ssl
import urllib.request
from pathlib import Path
from urllib.parse import urlparse, unquote

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


# Regex patterns for external resource URLs in HTML/CSS
# Matches src="https://..." or src="//..."
_RE_SRC = re.compile(r'src=["\']((https?:)?//[^"\']+)["\']')
# Matches <link ... href="https://..." or href="//..." (but NOT <a href=...)
_RE_LINK_HREF = re.compile(r'<link\b[^>]*\bhref=["\']((https?:)?//[^"\']+)["\']')
# Matches url(https://...) or url("https://...") or url('https://...')
_RE_CSS_URL = re.compile(r'url\(["\']?((https?:)?//[^"\')\s]+)["\']?\)')
# Matches @import "https://..." or @import url(...)
_RE_CSS_IMPORT = re.compile(r'@import\s+["\']((https?:)?//[^"\']+)["\']')


def find_external_urls(content):
    """
    Find all external (http/https/protocol-relative) resource URLs in HTML or CSS content.

    Does NOT match <a href="..."> navigation links.

    Args:
        content: HTML or CSS content string

    Returns:
        set: Unique external URLs found
    """
    urls = set()
    for pattern in (_RE_SRC, _RE_LINK_HREF, _RE_CSS_URL, _RE_CSS_IMPORT):
        for match in pattern.finditer(content):
            urls.add(match.group(1))
    return urls


def url_to_local_path(url):
    """
    Convert a URL to a safe local path under `_external/`.

    Protocol-relative URLs are normalized to https.
    Query strings get an MD5 hash suffix.
    '@' characters in paths are replaced with '_'.

    Args:
        url: External URL string

    Returns:
        str: Local path relative to site root (e.g. '_external/cdn.example.com/path/file.js')
    """
    if url.startswith('//'):
        url = 'https:' + url

    parsed = urlparse(url)
    domain = parsed.netloc
    path = unquote(parsed.path).lstrip('/')

    # Replace @ with _ for safe filenames
    path = path.replace('@', '_')

    # Handle query strings
    if parsed.query:
        query_hash = hashlib.md5(parsed.query.encode()).hexdigest()[:8]
        # Determine extension from path or default to .css for stylesheet endpoints
        _, ext = os.path.splitext(path)
        if ext:
            base = path[:len(path) - len(ext)]
            path = f"{base}_q_{query_hash}{ext}"
        else:
            path = f"{path}_q_{query_hash}.css"

    # Ensure we have a filename (not just a directory)
    if not path or path.endswith('/'):
        path = path + 'index'

    return f"_external/{domain}/{path}"


def download_resource(url, dest_path):
    """
    Download a URL to a local file path.

    Uses Mozilla User-Agent. 30s timeout. Skips if already downloaded.

    Args:
        url: URL to download
        dest_path: Local filesystem path to save to

    Returns:
        bool: True if downloaded (or already exists), False on failure
    """
    logger = logging.getLogger(__name__)

    dest = Path(dest_path)
    if dest.exists() and dest.stat().st_size > 0:
        return True

    if url.startswith('//'):
        url = 'https:' + url

    dest.parent.mkdir(parents=True, exist_ok=True)

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0'
    }
    req = urllib.request.Request(url, headers=headers)

    # Create SSL context that works with most CDNs
    ctx = ssl.create_default_context()

    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
            data = response.read()
            with open(dest, 'wb') as f:
                f.write(data)
        logger.debug(f"Downloaded: {url} -> {dest_path}")
        return True
    except Exception as e:
        logger.warning(f"Failed to download {url}: {e}")
        return False


def resolve_external_dependencies(load_path, logger):
    """
    Main entry point: scan site files for external URLs, download them locally.

    1. Scan all HTML/CSS files for external URLs
    2. Download each to `_external/{domain}/{path}`
    3. Recursively scan downloaded CSS files for nested URLs (max depth 3)
    4. Return mapping of {original_url: local_relative_path}

    Args:
        load_path: Path to the site root directory
        logger: Logger instance

    Returns:
        dict: Mapping of original URL -> local relative path
    """
    load_path = Path(load_path)
    url_mapping = {}
    urls_to_download = set()

    # Phase 1: Scan existing HTML/CSS files
    logger.info("Scanning for external dependencies...")
    for pattern in ('**/*.html', '**/*.htm', '**/*.css'):
        for filepath in load_path.glob(pattern):
            # Skip _external directory itself
            if '_external' in filepath.parts:
                continue
            try:
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                urls = find_external_urls(content)
                urls_to_download.update(urls)
            except Exception as e:
                logger.warning(f"Failed to scan {filepath}: {e}")

    if not urls_to_download:
        logger.info("No external dependencies found.")
        return {}

    logger.info(f"Found {len(urls_to_download)} external URLs to resolve.")

    # Phase 2: Download all resources
    downloaded_css = []
    url_iter = tqdm(urls_to_download, desc="Downloading", unit="file") if TQDM_AVAILABLE else urls_to_download
    for url in url_iter:
        local_path = url_to_local_path(url)
        dest = load_path / local_path
        if download_resource(url, dest):
            url_mapping[url] = local_path
            # Track CSS files for recursive scanning
            if local_path.endswith('.css'):
                downloaded_css.append((local_path, 1))

    # Phase 3: Recursively scan downloaded CSS files (max depth 3)
    if TQDM_AVAILABLE and downloaded_css:
        pbar = tqdm(desc="Resolving nested CSS", unit="file")
    else:
        pbar = None
    while downloaded_css:
        css_path, depth = downloaded_css.pop(0)
        if depth > 3:
            continue
        full_path = load_path / css_path
        if not full_path.exists():
            continue
        try:
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            nested_urls = find_external_urls(content)
            for url in nested_urls:
                if url in url_mapping:
                    continue
                local_path = url_to_local_path(url)
                dest = load_path / local_path
                if download_resource(url, dest):
                    url_mapping[url] = local_path
                    if pbar is not None:
                        pbar.update(1)
                    if local_path.endswith('.css'):
                        downloaded_css.append((local_path, depth + 1))
        except Exception as e:
            logger.warning(f"Failed to scan nested CSS {css_path}: {e}")
    if pbar is not None:
        pbar.close()

    # Phase 4: Register alternate protocol forms
    # For each URL, ensure both // and https:// forms are mapped
    extras = {}
    for url, local_path in url_mapping.items():
        if url.startswith('https://'):
            alt = '//' + url[len('https://'):]
            if alt not in url_mapping:
                extras[alt] = local_path
        elif url.startswith('//'):
            alt = 'https:' + url
            if alt not in url_mapping:
                extras[alt] = local_path
    url_mapping.update(extras)

    logger.info(f"Resolved {len(url_mapping)} external dependencies.")
    return url_mapping


def replace_external_urls(content, url_mapping, depth):
    """
    Replace external URLs in content with local relative paths.

    Simple string replacement - external URLs are unique strings.
    Files are never modified on disk; this operates in-memory.

    Args:
        content: HTML or CSS content string
        url_mapping: dict mapping {original_url: local_relative_path}
        depth: Directory depth of the file being processed (for ../ prefix)

    Returns:
        str: Content with external URLs replaced by local paths
    """
    prefix = "../" * depth
    # Sort by length descending so longer URLs are replaced first
    # (prevents partial replacements of shorter URLs that are substrings)
    for url in sorted(url_mapping.keys(), key=len, reverse=True):
        local_path = url_mapping[url]
        content = content.replace(url, prefix + local_path)
    return content
