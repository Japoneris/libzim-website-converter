#!/usr/bin/env python3
"""
HTTrack Wrapper for ZimSite

Wrapper around httrack to download websites and prepare them for ZIM conversion.
Creates download folder, downloads content, and generates config file.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


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


def create_config_file(name, url, config_dir='config'):
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
        "language": "eng"
    }

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

    # Create config file
    print(f"\nCreating config file...")
    config_file = create_config_file(name, args.url, args.config_dir)
    print(f"Config file created: {config_file}")

    print(f"\n=== Summary ===")
    print(f"Project name: {name}")
    print(f"Download directory: {download_dir}")
    print(f"Config file: {config_file}")

    if not args.skip_download:
        print(f"\nNext steps:")
        print(f"1. Review and edit config file: {config_file}")
        print(f"2. Convert to ZIM:")
        print(f"   python3 website_converter.py {download_dir}/*/ --config {config_file}")


if __name__ == "__main__":
    main()
