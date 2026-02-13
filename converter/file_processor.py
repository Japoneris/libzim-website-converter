"""
File processing logic for ZIM conversion.
"""

import logging
import re
from pathlib import Path

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from .zim_item import MyItem
from .mime_types import MIME_TYPES
from .image_optimizer import optimize_image
from .external_deps import replace_external_urls


def process_html_content(data, depth, filepath, load_path, lst_missing_index, relpath):
    """
    Process HTML content: fix paths and validate index links.

    Args:
        data: HTML content string
        depth: Directory depth of the file
        filepath: Path to the HTML file
        load_path: Root path of the site
        lst_missing_index: List to collect missing index warnings
        relpath: Relative path of the file

    Returns:
        str: Processed HTML content
    """
    data = data.replace('href="/', 'href="{}'.format("../" * depth))
    data = data.replace('src="/', 'src="{}'.format("../" * depth))
    data = data.replace('url(/', 'url({}'.format("../" * depth))
    data = data.replace('url("/', 'url("{}'.format("../" * depth))

    def check_and_replace_index(match):
        link = match.group(1)
        index_path = load_path / link.lstrip('/') / 'index.html'

        if index_path.exists():
            return link + '/index.html"'
        else:
            warning_msg = f"{relpath} -> Link '{link}/' has no index.html"
            if warning_msg not in lst_missing_index:
                lst_missing_index.append(warning_msg)
            return link + '/"'

    data = re.sub(r'((?:href="|src=")(?:\.\./)*[^"]*/)(?=")', check_and_replace_index, data)
    return data


def find_referenced_assets(all_files, load_path):
    """
    Scan all HTML and CSS files to build a set of referenced asset paths.

    Returns:
        set: Relative paths (from load_path) of all referenced assets.
    """
    referenced = set()

    # Patterns to extract references from HTML
    html_patterns = [
        re.compile(r'(?:href|src|poster|data-src)=["\']([^"\'#?]+)', re.IGNORECASE),
        re.compile(r'srcset=["\']([^"\']+)["\']', re.IGNORECASE),
        re.compile(r'url\(["\']?([^"\')\s#?]+)', re.IGNORECASE),
    ]
    # Pattern for CSS url() references
    css_url_pattern = re.compile(r'url\(["\']?([^"\')\s#?]+)', re.IGNORECASE)

    for filepath in all_files:
        ext = filepath.suffix.lower()
        if ext not in ('.html', '.htm', '.css'):
            continue

        try:
            content = filepath.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue

        file_dir = filepath.parent

        if ext in ('.html', '.htm'):
            patterns = html_patterns
        else:
            patterns = [css_url_pattern]

        for pattern in patterns:
            for match in pattern.finditer(content):
                raw = match.group(1)

                # srcset has comma-separated entries like "img.png 2x, img2.png 3x"
                if 'srcset' in (match.group(0) or ''):
                    entries = raw.split(',')
                    refs = [e.strip().split()[0] for e in entries if e.strip()]
                else:
                    refs = [raw]

                for ref in refs:
                    ref = ref.strip()
                    # Skip external URLs, data URIs, anchors, empty
                    if not ref or ref.startswith(('http://', 'https://', '//', 'data:', 'mailto:', '#', 'javascript:')):
                        continue

                    # Resolve the reference relative to the file's directory
                    if ref.startswith('/'):
                        resolved = load_path / ref.lstrip('/')
                    else:
                        resolved = (file_dir / ref).resolve()

                    try:
                        relpath = str(resolved.relative_to(load_path.resolve()))
                    except ValueError:
                        # Outside the site directory
                        continue

                    referenced.add(relpath)

                    # If it's a directory-like reference, also add index.html
                    if relpath.endswith('/') or not Path(relpath).suffix:
                        referenced.add(relpath.rstrip('/') + '/index.html')

    return referenced


def cleanup_unreferenced(all_files, load_path, logger):
    """
    Filter out non-HTML files that are not referenced by any HTML or CSS file.

    Args:
        all_files: List of all files to process
        load_path: Root path of the site
        logger: Logger instance

    Returns:
        tuple: (filtered_files, removed_count)
    """
    logger.info("Scanning for referenced assets...")
    referenced = find_referenced_assets(all_files, load_path)
    logger.info(f"Found {len(referenced)} asset references in HTML/CSS files")

    filtered = []
    removed = []

    for filepath in all_files:
        relpath = str(filepath.relative_to(load_path))
        ext = filepath.suffix.lower()

        # Always keep HTML/CSS files
        if ext in ('.html', '.htm', '.css'):
            filtered.append(filepath)
            continue

        # Keep the asset if it's referenced
        if relpath in referenced:
            filtered.append(filepath)
        else:
            removed.append(relpath)

    if removed:
        logger.info(f"Cleanup: removing {len(removed)} unreferenced assets")
        if logger.isEnabledFor(logging.DEBUG):
            for r in removed:
                logger.debug(f"  Unreferenced: {r}")

    return filtered, len(removed)


def process_dry_run(all_files, load_path, args, lst_unknown, lst_missing_index, lst_errors, url_mapping=None):
    """
    Analyze files without creating ZIM (dry-run mode).

    Args:
        all_files: List of all files to process
        load_path: Root path of the site
        args: Command-line arguments
        lst_unknown: List to collect unknown extensions
        lst_missing_index: List to collect missing index warnings
        lst_errors: List to collect errors

    Returns:
        tuple: (images_optimized, bytes_saved)
    """
    images_optimized = 0
    bytes_saved = 0

    use_progress_bar = TQDM_AVAILABLE and not args.no_progress and not args.quiet and not args.verbose
    file_iterator = tqdm(all_files, desc="Analyzing", unit="file") if use_progress_bar else all_files

    for filepath in file_iterator:
        relpath = str(filepath.relative_to(load_path))
        ext = filepath.suffix.lstrip(".").lower()

        if args.verbose:
            logging.debug(f"Analyzing: {relpath}")

        try:
            if ext not in MIME_TYPES and not (str(filepath).endswith(".html") or str(filepath).endswith(".htm")):
                lst_unknown.append(ext)

            if str(filepath).endswith(".html") or str(filepath).endswith(".htm"):
                with open(filepath, "r", encoding="utf-8", errors="replace") as fp:
                    data = fp.read()
                    links = re.findall(r'href="([^"]+/)"', data)
                    for link in links:
                        index_path = load_path / link.lstrip('/') / 'index.html'
                        if not index_path.exists():
                            warning_msg = f"{relpath} -> Link '{link}' has no index.html"
                            if warning_msg not in lst_missing_index:
                                lst_missing_index.append(warning_msg)

            if args.optimize_images and ext in ['jpg', 'jpeg', 'png']:
                result = optimize_image(filepath, args.max_image_width, args.image_quality)
                if result:
                    _, orig_size, new_size = result
                    images_optimized += 1
                    bytes_saved += (orig_size - new_size)

        except Exception as e:
            logging.error(f"Failed to analyze {filepath}: {e}")
            lst_errors.append(f"{relpath} ({type(e).__name__})")

    return images_optimized, bytes_saved


def process_files(creator, all_files, load_path, args, lst_unknown, lst_missing_index, lst_errors, url_mapping=None):
    """
    Process all files and add them to ZIM archive.

    Args:
        creator: ZIM Creator instance
        all_files: List of all files to process
        load_path: Root path of the site
        args: Command-line arguments
        lst_unknown: List to collect unknown extensions
        lst_missing_index: List to collect missing index warnings
        lst_errors: List to collect errors

    Returns:
        tuple: (images_optimized, bytes_saved)
    """
    images_optimized = 0
    bytes_saved = 0

    use_progress_bar = TQDM_AVAILABLE and not args.no_progress and not args.quiet and not args.verbose
    file_iterator = tqdm(all_files, desc="Processing", unit="file") if use_progress_bar else all_files

    for filepath in file_iterator:
        relpath = str(filepath.relative_to(load_path))
        depth = relpath.count("/")
        title = filepath.stem
        ext = filepath.suffix.lstrip(".").lower()

        if args.verbose:
            logging.debug(f"Depth: {depth} \t{relpath}")

        try:
            if ext in MIME_TYPES:
                mime = MIME_TYPES[ext]

                if args.optimize_images and ext in ['jpg', 'jpeg', 'png']:
                    result = optimize_image(filepath, args.max_image_width, args.image_quality)
                    if result:
                        optimized_data, orig_size, new_size = result
                        images_optimized += 1
                        bytes_saved += (orig_size - new_size)
                        item = MyItem(title=title, path=relpath, content=optimized_data, mimetype=mime)
                        if args.verbose:
                            logging.debug(f"Optimized {relpath}: {orig_size} -> {new_size} bytes")
                    else:
                        item = MyItem(title=title, path=relpath, fpath=str(filepath), mimetype=mime)
                elif url_mapping and ext == 'css':
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='replace') as fp:
                            css_data = fp.read()
                        css_data = replace_external_urls(css_data, url_mapping, depth)
                        item = MyItem(title=title, path=relpath, content=css_data, mimetype=mime)
                    except Exception as e:
                        logging.warning(f"CSS rewrite failed for {relpath}, using original: {e}")
                        item = MyItem(title=title, path=relpath, fpath=str(filepath), mimetype=mime)
                else:
                    item = MyItem(title=title, path=relpath, fpath=str(filepath), mimetype=mime)

            elif str(filepath).endswith(".html") or str(filepath).endswith(".htm"):
                with open(filepath, "r", encoding="utf-8", errors="replace") as fp:
                    data = fp.read()

                data = process_html_content(data, depth, filepath, load_path, lst_missing_index, relpath)
                if url_mapping:
                    data = replace_external_urls(data, url_mapping, depth)
                item = MyItem(title=title, path=relpath, content=data)

            else:
                logging.debug(f"Unknown mimetype: {relpath}")
                lst_unknown.append(relpath.rsplit(".", 1)[-1])
                item = MyItem(title=title, path=relpath, fpath=str(filepath))

            creator.add_item(item)

        except PermissionError:
            logging.error(f"Permission denied reading file: {filepath}")
            lst_errors.append(f"{relpath} (Permission denied)")
        except UnicodeDecodeError as e:
            logging.error(f"Encoding error in file {filepath}: {e}")
            lst_errors.append(f"{relpath} (Encoding error)")
        except Exception as e:
            logging.error(f"Failed to process file {filepath}: {e}")
            lst_errors.append(f"{relpath} ({type(e).__name__})")

    return images_optimized, bytes_saved
