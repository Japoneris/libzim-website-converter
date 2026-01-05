"""
Given a `_site/` with all pages / assets in, create .zim

a webpage should refer to style / assets using `href=/assets/`.
Otherwise, it should handle page relativity itself.


"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

from libzim.writer import Creator, Item, StringProvider, FileProvider, Hint



# Class provided in python openzim documentation
class MyItem(Item):
    def __init__(self, title, path, content="", fpath=None, mimetype="text/html"):
        super().__init__()
        self.path = path
        self.title = title
        self.content = content
        self.fpath = fpath
        self.mimetype = mimetype

    def get_path(self):
        return self.path

    def get_title(self):
        return self.title

    def get_mimetype(self):
        return self.mimetype #"text/html"

    def get_contentprovider(self):
        if self.fpath is not None:
            return FileProvider(self.fpath)

        # Handle both string and bytes content
        if isinstance(self.content, bytes):
            from libzim.writer import Blob
            return Blob(self.content)
        return StringProvider(self.content)

    def get_hints(self):
        return {Hint.FRONT_ARTICLE: True}


# Validation functions
def validate_language_code(lang_code):
    """Validate language code format (3 letters for ISO 639-3)."""
    if not lang_code or len(lang_code) != 3 or not lang_code.isalpha():
        return False
    return True


def validate_filename(filename):
    """Validate ZIM filename (no special characters except dash/underscore)."""
    if not filename:
        return False
    # Remove spaces and check for invalid characters
    invalid_chars = '<>:"/\\|?*'
    return not any(char in filename for char in invalid_chars)


def sanitize_filename(filename):
    """Sanitize filename by replacing spaces and removing invalid characters."""
    # Replace spaces with hyphens
    filename = filename.replace(' ', '-')
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename


def setup_logging(verbose=False, quiet=False):
    """Configure logging based on verbosity settings."""
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
    """Load configuration from JSON file if it exists."""
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


def optimize_image(image_path, max_width=1920, quality=85):
    """
    Optimize image by resizing and compressing.
    Returns: (optimized_data, original_size, new_size) or None if failed/not needed.
    """
    if not PILLOW_AVAILABLE:
        return None

    try:
        with Image.open(image_path) as img:
            original_size = image_path.stat().st_size

            # Skip small images
            if original_size < 50 * 1024:  # 50KB threshold
                return None

            # Resize if too large
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # Save optimized version to bytes
            from io import BytesIO
            output = BytesIO()

            # Determine format
            fmt = img.format or 'PNG'
            if fmt == 'JPEG' or fmt == 'JPG':
                img.save(output, format='JPEG', quality=quality, optimize=True)
            elif fmt == 'PNG':
                img.save(output, format='PNG', optimize=True)
            else:
                return None

            new_size = output.tell()

            # Only use optimized version if it's smaller
            if new_size < original_size:
                return (output.getvalue(), original_size, new_size)

            return None

    except Exception as e:
        logging.debug(f"Failed to optimize image {image_path}: {e}")
        return None


def generate_link_validation_report(lst_missing_index, lst_unknown, lst_errors, output_path):
    """Generate an HTML report of link validation issues."""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZIM Conversion Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-box { background: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #4CAF50; }
        .stat-box.warning { border-left-color: #ff9800; }
        .stat-box.error { border-left-color: #f44336; }
        .stat-number { font-size: 32px; font-weight: bold; color: #333; }
        .stat-label { color: #666; font-size: 14px; }
        .issue-list { background: #fafafa; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .issue-item { padding: 8px; margin: 5px 0; background: white; border-left: 3px solid #ff9800; }
        .error-item { border-left-color: #f44336; }
        code { background: #e0e0e0; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
        .timestamp { color: #999; font-size: 12px; text-align: right; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ZIM Conversion Report</h1>

        <div class="summary">
            <div class="stat-box warning">
                <div class="stat-number">{missing_links_count}</div>
                <div class="stat-label">Missing Index Pages</div>
            </div>
            <div class="stat-box warning">
                <div class="stat-number">{unknown_mime_count}</div>
                <div class="stat-label">Unknown MIME Types</div>
            </div>
            <div class="stat-box error">
                <div class="stat-number">{errors_count}</div>
                <div class="stat-label">Processing Errors</div>
            </div>
        </div>

        {missing_section}
        {mime_section}
        {error_section}

        <div class="timestamp">Generated: {timestamp}</div>
    </div>
</body>
</html>"""

    # Build sections
    missing_section = ""
    if lst_missing_index:
        items = "\n".join([f'<div class="issue-item">{item}</div>' for item in lst_missing_index])
        missing_section = f"""
        <h2>Missing Index Pages ({len(lst_missing_index)})</h2>
        <p>Links ending with <code>/</code> but no <code>index.html</code> file found:</p>
        <div class="issue-list">{items}</div>
        """

    mime_section = ""
    if lst_unknown:
        unique_unknown = sorted(set(lst_unknown))
        items = "\n".join([f'<div class="issue-item"><code>.{ext}</code></div>' for ext in unique_unknown])
        mime_section = f"""
        <h2>Unknown MIME Types ({len(unique_unknown)})</h2>
        <p>File extensions without registered MIME types (treated as HTML):</p>
        <div class="issue-list">{items}</div>
        """

    error_section = ""
    if lst_errors:
        items = "\n".join([f'<div class="issue-item error-item">{item}</div>' for item in lst_errors])
        error_section = f"""
        <h2>Processing Errors ({len(lst_errors)})</h2>
        <p>Files that failed to process:</p>
        <div class="issue-list">{items}</div>
        """

    # Fill template
    html_content = html_content.format(
        missing_links_count=len(lst_missing_index),
        unknown_mime_count=len(set(lst_unknown)),
        errors_count=len(lst_errors),
        missing_section=missing_section,
        mime_section=mime_section,
        error_section=error_section,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    # Write report
    report_path = Path(output_path) / "conversion_report.html"
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return report_path
    except Exception as e:
        logging.error(f"Failed to generate report: {e}")
        return None


# Get the list here if necessary:
# https://developer.mozilla.org/fr/docs/Web/HTTP/MIME_types/Common_types

dic_mime = {
    "bin": "application/octet-stream",
    "bmp": "image/bmp",
    "bz":  "application/x-bzip",
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
    "js":  "application/javascript",
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
    "tif": "image/tiff",
    "txt": "text/plain",
    "ts":  "application/typescript",
    "ttf": "font/ttf",
    "wav": "audio/x-wav",
    "webp": "image/webp",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xml": "application/xml",
    "zip": "application/zip",
    
    
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert static websites to ZIM archive format for offline viewing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (prompts for metadata)
  python3 website_converter.py myblog/_site/

  # Non-interactive mode (all metadata via flags)
  python3 website_converter.py myblog/_site/ --name "My Blog" --title "Personal Blog" \\
    --creator "John Doe" --description "My personal blog" --language eng \\
    --non-interactive

  # Using a configuration file
  python3 website_converter.py myblog/_site/ --config config.json
        """
    )

    parser.add_argument("site_path", help="Path to the compiled website directory")
    parser.add_argument("--output_path", default="zim", help="Output directory for ZIM file (default: zim)")
    parser.add_argument("--icon", default="icons/comment.png", help="Path to ZIM icon (default: icons/comment.png)")

    # Metadata arguments
    parser.add_argument("--name", help="ZIM filename (without .zim extension)")
    parser.add_argument("--title", help="ZIM title metadata")
    parser.add_argument("--creator", help="Creator name")
    parser.add_argument("--publisher", default="You", help="Publisher name (default: You)")
    parser.add_argument("--description", help="Description of the content")
    parser.add_argument("--language", help="ISO 639-3 language code (e.g., eng, fra)")

    # Configuration and verbosity
    parser.add_argument("--config", help="Path to JSON configuration file")
    parser.add_argument("--non-interactive", action="store_true", help="Non-interactive mode (no prompts, use flags or config)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output (DEBUG level)")
    parser.add_argument("--quiet", action="store_true", help="Suppress all output except errors")

    # Phase 3 features
    parser.add_argument("--dry-run", action="store_true", help="Analyze and report without creating ZIM file")
    parser.add_argument("--optimize-images", action="store_true", help="Optimize images (resize/compress) - requires Pillow")
    parser.add_argument("--max-image-width", type=int, default=1920, help="Maximum image width for optimization (default: 1920)")
    parser.add_argument("--image-quality", type=int, default=85, help="JPEG quality for optimization (default: 85)")
    parser.add_argument("--report", action="store_true", help="Generate HTML validation report")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bar (useful for logging)")

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(verbose=args.verbose, quiet=args.quiet)

    # Check feature dependencies
    if args.optimize_images and not PILLOW_AVAILABLE:
        logger.warning("--optimize-images requires Pillow. Install with: pip install Pillow")
        logger.warning("Continuing without image optimization.")
        args.optimize_images = False

    if not args.no_progress and not TQDM_AVAILABLE and not args.quiet:
        logger.info("tqdm not available. Install with: pip install tqdm for progress bars.")

    if args.dry_run:
        logger.info("=== DRY RUN MODE - No ZIM file will be created ===")

    # Load configuration file if provided
    config = {}
    if args.config:
        logger.info(f"Loading configuration from {args.config}")
        config = load_config(args.config)

    # Validate and prepare paths
    load_path = Path(args.site_path)
    if not load_path.exists():
        logger.error(f"Site path does not exist: {load_path}")
        sys.exit(1)
    if not load_path.is_dir():
        logger.error(f"Site path is not a directory: {load_path}")
        sys.exit(1)

    save_path = Path(args.output_path)
    try:
        save_path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        logger.error(f"Permission denied creating output directory: {save_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to create output directory: {e}")
        sys.exit(1)

    # Get metadata (priority: CLI args > config file > interactive prompts > defaults)
    if args.non_interactive:
        # Non-interactive mode: require all metadata
        filename = args.name or config.get('name')
        lang = args.language or config.get('language')
        creator = args.creator or config.get('creator')
        description = args.description or config.get('description')
        title = args.title or config.get('title')
        publisher = args.publisher or config.get('publisher', 'You')

        if not all([filename, lang, creator, description, title]):
            logger.error("Non-interactive mode requires: --name, --language, --creator, --description, --title")
            sys.exit(1)
    else:
        # Interactive mode with defaults from CLI/config
        filename = args.name or config.get('name') or input("ZIM name? \t") or "test"

        if not args.quiet:
            print("For language code, see https://documentation.abes.fr/guide/html/formats/CodesLanguesISO639-3.htm")
        lang = args.language or config.get('language') or input("Language? (eng | fra): \t") or "eng"

        creator = args.creator or config.get('creator') or input("Creator? \t") or "unknown"
        description = args.description or config.get('description') or input("Description? \t") or "This is a test or the field was left empty"
        title = args.title or config.get('title') or input("Title? \t") or "ABC-Test"
        publisher = args.publisher or config.get('publisher', 'You')

    # Validate and sanitize inputs
    if not validate_language_code(lang):
        logger.warning(f"Invalid language code '{lang}'. Using 'eng' as fallback.")
        lang = "eng"

    if not validate_filename(filename):
        logger.warning(f"Invalid filename '{filename}'. Sanitizing...")
        filename = sanitize_filename(filename)
        logger.info(f"Sanitized filename: {filename}")

    current_date = datetime.today().strftime('%Y-%m-%d')

    # Load icon
    illustration = None
    icon_path = Path(args.icon)
    try:
        with open(icon_path, "rb") as fp:
            illustration = fp.read()
    except FileNotFoundError:
        logger.warning(f"Icon file not found: {icon_path}. Proceeding without icon.")
    except PermissionError:
        logger.warning(f"Permission denied reading icon: {icon_path}. Proceeding without icon.")
    except Exception as e:
        logger.warning(f"Failed to read icon: {e}. Proceeding without icon.")

    dic_metadata = {
        "creator": creator,
        "description": description,
        "name": filename,  # Use actual filename instead of hardcoded value
        "publisher": publisher,
        "title": title,
        "language": lang,
        "date": current_date,
    }

    if args.dry_run:
        logger.info("=== Analyzing Website (Dry Run) ===")
    else:
        logger.info("=== Building ZIM Archive ===")

    lst_unknown = [] # for unknown mime-type to add
    lst_missing_index = [] # for links ending with / but no index.html exists
    lst_errors = [] # for files that failed to process
    images_optimized = 0
    bytes_saved = 0

    # Count files for progress bar
    all_files = [f for f in load_path.rglob("*") if f.is_file()]
    total_files = len(all_files)
    logger.info(f"Found {total_files} files to process")

    # Setup progress bar if available and not disabled
    use_progress_bar = TQDM_AVAILABLE and not args.no_progress and not args.quiet and not args.verbose

    if args.dry_run:
        # Dry run mode - analyze without creating ZIM
        logger.info("Analyzing files (no ZIM file will be created)...")

        file_iterator = tqdm(all_files, desc="Analyzing", unit="file") if use_progress_bar else all_files

        for filepath in file_iterator:
            relpath = str(filepath.relative_to(load_path))
            ext = filepath.suffix.lstrip(".").lower()

            if args.verbose:
                logger.debug(f"Analyzing: {relpath}")

            try:
                # Check MIME type
                if ext not in dic_mime and not (str(filepath).endswith(".html") or str(filepath).endswith(".htm")):
                    lst_unknown.append(ext)

                # Check HTML files for missing index links
                if str(filepath).endswith(".html") or str(filepath).endswith(".htm"):
                    with open(filepath, "r", encoding="utf-8", errors="replace") as fp:
                        data = fp.read()
                        # Simple check for links ending with /
                        import re
                        links = re.findall(r'href="([^"]+/)"', data)
                        for link in links:
                            index_path = load_path / link.lstrip('/') / 'index.html'
                            if not index_path.exists():
                                warning_msg = f"{relpath} -> Link '{link}' has no index.html"
                                if warning_msg not in lst_missing_index:
                                    lst_missing_index.append(warning_msg)

                # Check image optimization potential
                if args.optimize_images and ext in ['jpg', 'jpeg', 'png']:
                    result = optimize_image(filepath, args.max_image_width, args.image_quality)
                    if result:
                        _, orig_size, new_size = result
                        images_optimized += 1
                        bytes_saved += (orig_size - new_size)

            except Exception as e:
                logger.error(f"Failed to analyze {filepath}: {e}")
                lst_errors.append(f"{relpath} ({type(e).__name__})")

    else:
        # Normal mode - create ZIM file
        try:
            with Creator(str(save_path / f"{filename}.zim")).config_indexing(True, lang) as creator:
                # Assume main entry page is index.html
                creator.set_mainpath("index.html")

                # Add illustration if available
                if illustration:
                    try:
                        creator.add_illustration(48, illustration)
                    except Exception as e:
                        logger.warning(f"Failed to add illustration: {e}")

                file_iterator = tqdm(all_files, desc="Processing", unit="file") if use_progress_bar else all_files

                for filepath in file_iterator:
                    relpath = str(filepath.relative_to(load_path))
                    depth = relpath.count("/")
                    title = filepath.stem
                    ext = filepath.suffix.lstrip(".")

                    if args.verbose:
                        logger.debug(f"Depth: {depth} \t{relpath}")

                    # Normalize extension to lowercase
                    ext = ext.lower()

                try:
                    if ext in dic_mime:
                        mime = dic_mime[ext]

                        # Try to optimize images if enabled
                        if args.optimize_images and ext in ['jpg', 'jpeg', 'png']:
                            result = optimize_image(filepath, args.max_image_width, args.image_quality)
                            if result:
                                optimized_data, orig_size, new_size = result
                                images_optimized += 1
                                bytes_saved += (orig_size - new_size)
                                # Use optimized data instead of file
                                item = MyItem(title=title,
                                     path=relpath,
                                     content=optimized_data,
                                     mimetype=mime)
                                if args.verbose:
                                    logger.debug(f"Optimized {relpath}: {orig_size} -> {new_size} bytes")
                            else:
                                # Use original file
                                item = MyItem(title=title,
                                     path=relpath,
                                     fpath=str(filepath),
                                    mimetype=mime)
                        else:
                            # No optimization, use file directly
                            item = MyItem(title=title,
                                 path=relpath,
                                 fpath=str(filepath),
                                mimetype=mime)

                    elif str(filepath).endswith(".html") or str(filepath).endswith(".htm"):
                        # HTML file
                        with open(filepath, "r", encoding="utf-8", errors="replace") as fp:
                            data = fp.read()

                        # Replace absolute reference by relative reference to get access to sources
                        data = data.replace('href="/', 'href="{}'.format("../" * depth))
                        data = data.replace('src="/', 'src="{}'.format("../" * depth))
                        data = data.replace('url(/', 'url({}'.format("../" * depth))
                        data = data.replace('url("/', 'url("{}'.format("../" * depth))

                        # Check and replace links ending with / to /index.html only if index.html exists
                        def check_and_replace_index(match):
                            link = match.group(1)  # Get the path before the /"
                            # Construct the absolute path to check
                            index_path = load_path / link.lstrip('/') / 'index.html'

                            if index_path.exists():
                                return link + '/index.html"'
                            else:
                                # Collect warning for missing index
                                warning_msg = f"{relpath} -> Link '{link}/' has no index.html"
                                if warning_msg not in lst_missing_index:
                                    lst_missing_index.append(warning_msg)
                                return link + '/"'  # Keep original link

                        # Replace only verified index pages
                        data = re.sub(r'((?:href="|src=")(?:\.\./)*[^"]*/)(?=")', check_and_replace_index, data)

                        item = MyItem(title=title,
                               path=relpath,
                               content=data)
                    else:
                        logger.debug(f"Unknown mimetype: {relpath}")
                        lst_unknown.append(relpath.rsplit(".", 1)[-1])

                        item = MyItem(title=title,
                                path=relpath,
                                fpath=str(filepath)) # will be considered as html

                    creator.add_item(item)

                except PermissionError:
                    logger.error(f"Permission denied reading file: {filepath}")
                    lst_errors.append(f"{relpath} (Permission denied)")
                except UnicodeDecodeError as e:
                    logger.error(f"Encoding error in file {filepath}: {e}")
                    lst_errors.append(f"{relpath} (Encoding error)")
                except Exception as e:
                    logger.error(f"Failed to process file {filepath}: {e}")
                    lst_errors.append(f"{relpath} ({type(e).__name__})")

                if not args.quiet and use_progress_bar:
                    print()  # Clear progress line

                logger.info("=== Adding metadata ===")
                # metadata
                try:
                    for name, value in dic_metadata.items():
                        creator.add_metadata(name.title(), value)
                        # .title() fx just uppercase the first letter
                except Exception as e:
                    logger.error(f"Failed to add metadata: {e}")

                logger.info("=== Compiling ZIM (this may take a while) ===")

        except Exception as e:
            logger.error(f"Failed to create ZIM archive: {e}")
            sys.exit(1)

    # Summary report
    if args.dry_run:
        logger.info("=== Dry Run Analysis Complete ===")
        logger.info(f"Analyzed {total_files} files")
    else:
        logger.info("=== ZIM Archive Created Successfully ===")
        logger.info(f"Output: {save_path / f'{filename}.zim'}")
        logger.info(f"Processed {total_files} files")

    # Image optimization stats
    if args.optimize_images and images_optimized > 0:
        logger.info(f"\n=== Image Optimization ===")
        logger.info(f"Optimized {images_optimized} images")
        logger.info(f"Saved {bytes_saved / 1024 / 1024:.2f} MB")

    # Validation warnings
    if lst_unknown:
        logger.warning(f"\nMissing mimetypes for {len(set(lst_unknown))} extensions:")
        logger.warning(", ".join(sorted(set(lst_unknown))))

    if lst_missing_index:
        logger.warning(f"\n{len(lst_missing_index)} links ending with / but no index.html found:")
        if args.verbose:
            for warning in lst_missing_index:
                logger.warning(f"  {warning}")
        else:
            logger.warning(f"  (use --verbose to see all warnings)")

    if lst_errors:
        logger.error(f"\n{len(lst_errors)} files failed to process:")
        if args.verbose:
            for error in lst_errors:
                logger.error(f"  {error}")
        else:
            logger.error(f"  (use --verbose to see all errors)")

    # Generate HTML report if requested
    if args.report or args.dry_run:
        logger.info("\n=== Generating Validation Report ===")
        report_path = generate_link_validation_report(lst_missing_index, lst_unknown, lst_errors, save_path)
        if report_path:
            logger.info(f"Report saved to: {report_path}")
        else:
            logger.error("Failed to generate report")
