#!/usr/bin/env python3
"""
HTTrack Wrapper for ZimSite

Wrapper around httrack to download websites and prepare them for ZIM conversion.
Creates download folder, downloads content, and generates config file.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, urljoin

try:
    import urllib.request
    URLLIB_AVAILABLE = True
except ImportError:
    URLLIB_AVAILABLE = False

try:
    from PIL import Image
    import io
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


def derive_name_from_url(url):
    """Extract a sensible name from a URL."""
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path

    # Remove common prefixes
    domain = domain.replace('www.', '')

    # Get path component if it exists
    path = parsed.path.strip('/')

    if path:
        # Use last part of path
        name = path.split('/')[-1]
    else:
        # Use domain name
        name = domain.split('.')[0]

    # Sanitize name
    name = name.replace(' ', '-').replace('_', '-')
    invalid_chars = '<>:"/\\|?*.'
    for char in invalid_chars:
        name = name.replace(char, '')

    return name.lower()


def create_config_file(name, url, config_dir='config', resolve_external=False, icon=None):
    """Create a configuration file for the downloaded website."""
    config_dir = Path(config_dir)
    config_dir.mkdir(exist_ok=True)

    config_file = config_dir / f"{name}.json"

    # Parse domain for title
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    title = domain.replace('www.', '').replace('.com', '').replace('.org', '').replace('.net', '')
    title = title.replace('-', ' ').replace('_', ' ').title()

    config_data = {
        "name": name,
        "title": title,
        "creator": "Unknown",
        "publisher": "Downloaded via HTTrack",
        "description": f"Offline copy of {url}",
        "language": "eng",
        "resolve_external": resolve_external
    }

    if icon:
        config_data["icon"] = icon

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)

    return config_file


def run_httrack(url, output_dir, additional_args=None):
    """Run httrack to download website."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Base httrack command
    cmd = ['httrack', url, '-O', str(output_path)]

    # Add additional arguments if provided
    if additional_args:
        cmd.extend(additional_args)

    print(f"Running httrack to download {url}...")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error: httrack failed with return code {e.returncode}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("Error: httrack not found. Install with: sudo apt install httrack", file=sys.stderr)
        return False


def find_favicon_in_download(download_dir):
    """Look for a favicon in the httrack downloaded files."""
    download_path = Path(download_dir)

    # Common favicon filenames, ordered by preference
    favicon_names = ['favicon.ico', 'favicon.png', 'favicon.svg',
                     'apple-touch-icon.png', 'apple-touch-icon-precomposed.png']

    # Search recursively for favicon files
    for name in favicon_names:
        matches = list(download_path.rglob(name))
        if matches:
            return matches[0]

    # Try to find favicon link in downloaded HTML
    for html_file in download_path.rglob('index.html'):
        try:
            content = html_file.read_text(encoding='utf-8', errors='ignore')
            # Match <link rel="icon" ...> or <link rel="shortcut icon" ...>
            pattern = r'<link[^>]+rel=["\'](?:shortcut )?icon["\'][^>]+href=["\']([^"\']+)["\']'
            match = re.search(pattern, content, re.IGNORECASE)
            if not match:
                # Try reversed order: href before rel
                pattern = r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\'](?:shortcut )?icon["\']'
                match = re.search(pattern, content, re.IGNORECASE)
            if match:
                href = match.group(1)
                # Resolve relative path from the HTML file's directory
                if not href.startswith(('http://', 'https://', '//')):
                    candidate = (html_file.parent / href).resolve()
                    if candidate.is_file():
                        return candidate
                # Try from download root (absolute path like /favicon.ico)
                if href.startswith('/'):
                    for subdir in download_path.iterdir():
                        if subdir.is_dir():
                            candidate = subdir / href.lstrip('/')
                            if candidate.is_file():
                                return candidate
        except Exception:
            continue

    return None


def fetch_favicon_from_url(url):
    """Try to download the favicon directly from the website."""
    if not URLLIB_AVAILABLE:
        return None

    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # Try common favicon URLs
    favicon_urls = [
        urljoin(base_url, '/favicon.ico'),
        urljoin(base_url, '/favicon.png'),
        urljoin(base_url, '/apple-touch-icon.png'),
    ]

    # Also try to parse the page for a favicon link
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            pattern = r'<link[^>]+rel=["\'](?:shortcut )?icon["\'][^>]+href=["\']([^"\']+)["\']'
            match = re.search(pattern, html, re.IGNORECASE)
            if not match:
                pattern = r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\'](?:shortcut )?icon["\']'
                match = re.search(pattern, html, re.IGNORECASE)
            if match:
                href = match.group(1)
                resolved = urljoin(url, href)
                # Insert at the beginning so it's tried first
                favicon_urls.insert(0, resolved)
    except Exception:
        pass

    for fav_url in favicon_urls:
        try:
            req = urllib.request.Request(fav_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'image' in content_type or fav_url.endswith(('.ico', '.png', '.svg')):
                        return response.read(), fav_url
        except Exception:
            continue

    return None


def convert_favicon_to_png(image_data, output_path, size=48):
    """Convert favicon data to a 48x48 PNG suitable for ZIM."""
    if PILLOW_AVAILABLE:
        try:
            img = Image.open(io.BytesIO(image_data))
            # For ICO files with multiple sizes, pick the best one
            if hasattr(img, 'n_frames') and img.format == 'ICO':
                # ICO files can have multiple sizes, Pillow picks the first
                pass
            img = img.convert('RGBA')
            img = img.resize((size, size), Image.LANCZOS)
            img.save(output_path, 'PNG')
            return True
        except Exception as e:
            print(f"Warning: Failed to convert favicon with Pillow: {e}")
            return False
    else:
        # Without Pillow, save raw data only if it's already PNG
        if image_data[:8] == b'\x89PNG\r\n\x1a\n':
            with open(output_path, 'wb') as f:
                f.write(image_data)
            return True
        else:
            print("Warning: Pillow not installed, cannot convert favicon to PNG.")
            print("  Install with: pip install Pillow")
            return False


def fetch_and_save_favicon(url, download_dir, name, icons_dir='icons'):
    """Try to find/download a favicon and save it as a PNG icon.

    Returns the path to the saved icon, or None if not found.
    """
    icons_path = Path(icons_dir)
    icons_path.mkdir(exist_ok=True)
    output_path = icons_path / f"{name}.png"

    # First, look in the downloaded files
    print("Looking for favicon in downloaded files...")
    local_favicon = find_favicon_in_download(download_dir)
    if local_favicon:
        print(f"  Found local favicon: {local_favicon}")
        image_data = local_favicon.read_bytes()
        if convert_favicon_to_png(image_data, output_path):
            print(f"  Saved icon: {output_path}")
            return str(output_path)

    # Second, try fetching directly from the website
    print("Fetching favicon from website...")
    result = fetch_favicon_from_url(url)
    if result:
        image_data, fav_url = result
        print(f"  Found favicon at: {fav_url}")
        if convert_favicon_to_png(image_data, output_path):
            print(f"  Saved icon: {output_path}")
            return str(output_path)

    print("  No favicon found.")
    return None


def main():
    parser = argparse.ArgumentParser(
        description="HTTrack wrapper for downloading websites and preparing for ZIM conversion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download with auto-generated name
  python3 httrack_wrapper.py https://example.com/docs/

  # Download with custom name
  python3 httrack_wrapper.py https://example.com/docs/ --name mydocs

  # Download to custom output directory
  python3 httrack_wrapper.py https://example.com/ --output downloads/example

  # Pass additional httrack options
  python3 httrack_wrapper.py https://example.com/ --httrack-args "-r3 --max-rate=1000000"
        """
    )

    parser.add_argument("url", help="URL to download")
    parser.add_argument("--name", help="Name for the project (auto-generated from URL if not provided)")
    parser.add_argument("--output", default="downloads", help="Output directory for downloads (default: downloads)")
    parser.add_argument("--config-dir", default="config", help="Directory for config files (default: config)")
    parser.add_argument("--httrack-args", help="Additional arguments to pass to httrack (as a quoted string)")
    parser.add_argument("--skip-download", action="store_true", help="Skip download, only create config file")
    parser.add_argument("--resolve-external", action="store_true", help="Enable external dependency resolution during ZIM conversion")
    parser.add_argument("--no-favicon", action="store_true", help="Skip favicon fetching")

    args = parser.parse_args()

    # Determine project name
    if args.name:
        name = args.name
    else:
        name = derive_name_from_url(args.url)
        print(f"Auto-generated name: {name}")

    # Create download directory path
    download_dir = Path(args.output) / name

    # Download with httrack if not skipping
    if not args.skip_download:
        # Parse additional httrack arguments
        httrack_args = args.httrack_args.split() if args.httrack_args else []

        success = run_httrack(args.url, download_dir, httrack_args)
        if not success:
            print("Download failed. Config file will still be created.", file=sys.stderr)
    else:
        print("Skipping download (--skip-download)")
        download_dir.mkdir(parents=True, exist_ok=True)

    # Try to fetch favicon
    icon_path = None
    if not args.no_favicon:
        print(f"\n=== Fetching Favicon ===")
        icon_path = fetch_and_save_favicon(args.url, download_dir, name)

    # Create config file
    print(f"\nCreating config file...")
    config_file = create_config_file(name, args.url, args.config_dir,
                                     resolve_external=args.resolve_external,
                                     icon=icon_path)
    print(f"Config file created: {config_file}")

    print(f"\n=== Summary ===")
    print(f"Project name: {name}")
    print(f"Download directory: {download_dir}")
    print(f"Config file: {config_file}")
    print(f"Icon: {icon_path or 'not found (using default)'}")
    print(f"Resolve external deps: {args.resolve_external}")

    if not args.skip_download:
        print(f"\nNext steps:")
        print(f"1. Review and edit config file: {config_file}")
        print(f"2. Convert to ZIM:")
        print(f"   python3 website_converter.py {download_dir}/*/ --config {config_file}")


if __name__ == "__main__":
    main()
