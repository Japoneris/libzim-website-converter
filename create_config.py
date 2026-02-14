#!/usr/bin/env python3
"""
Interactive config file builder for ZimSite.

Creates a JSON configuration file with all settings needed by website_converter.py.
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ISO 639-3 codes (common subset)
COMMON_LANGUAGES = {
    "eng": "English",
    "fra": "French",
    "deu": "German",
    "spa": "Spanish",
    "ita": "Italian",
    "por": "Portuguese",
    "nld": "Dutch",
    "rus": "Russian",
    "zho": "Chinese",
    "jpn": "Japanese",
    "kor": "Korean",
    "ara": "Arabic",
}


def validate_language_code(code):
    """Check that code is a 3-letter lowercase string."""
    return bool(re.match(r'^[a-z]{3}$', code))


def validate_filename(name):
    """Check for invalid filename characters."""
    invalid = '<>:"/\\|?*'
    return all(c not in name for c in invalid) and len(name) > 0


def sanitize_filename(name):
    """Remove invalid characters from filename."""
    invalid = '<>:"/\\|?* '
    for c in invalid:
        name = name.replace(c, '-')
    name = re.sub(r'-+', '-', name).strip('-')
    return name or 'unnamed'


def prompt(label, default=None, required=False, validator=None, sanitizer=None):
    """Prompt the user for a value with optional default, validation, and sanitization."""
    while True:
        if default:
            raw = input(f"  {label} [{default}]: ").strip()
        else:
            raw = input(f"  {label}: ").strip()

        value = raw or default

        if required and not value:
            print("    This field is required.")
            continue

        if value and validator and not validator(value):
            if sanitizer:
                fixed = sanitizer(value)
                print(f"    Invalid input. Using sanitized value: {fixed}")
                return fixed
            print("    Invalid input. Please try again.")
            continue

        return value


def detect_site_path(base_dir):
    """Auto-detect the site content directory inside a download folder."""
    base = Path(base_dir)
    if not base.is_dir():
        return None

    # Look for subdirectories that look like domain names (contain a dot)
    candidates = []
    for child in sorted(base.iterdir()):
        if child.is_dir() and child.name not in ('hts-cache', '_external'):
            candidates.append(child)

    if len(candidates) == 1:
        return str(candidates[0])

    if len(candidates) > 1:
        print(f"\n  Multiple subdirectories found in {base_dir}:")
        for i, c in enumerate(candidates, 1):
            print(f"    {i}. {c.name}")
        choice = input(f"  Choose [1]: ").strip()
        try:
            idx = int(choice) - 1 if choice else 0
            return str(candidates[idx])
        except (ValueError, IndexError):
            return str(candidates[0])

    # No subdirectories — the base dir might be the site itself
    return str(base)


def main():
    parser = argparse.ArgumentParser(
        description="Interactively create a ZimSite configuration file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python3 create_config.py

  # Start with a known site path
  python3 create_config.py --site-path downloads/my-site/example.com

  # Specify output config path
  python3 create_config.py --output config/my-site.json
        """
    )

    parser.add_argument("--site-path", help="Path to the site content directory")
    parser.add_argument("--output", help="Output config file path (default: config/<name>.json)")

    args = parser.parse_args()

    print("=== ZimSite Config Builder ===\n")

    # 1. Site path
    if args.site_path:
        site_path = args.site_path
        print(f"  Site path: {site_path}")
    else:
        print("Where is the website content?")
        print("  (e.g., downloads/my-site/example.com or myblog/_site/)")
        hint = input("  Enter path or parent directory to scan: ").strip()

        if not hint:
            print("Error: site path is required.")
            sys.exit(1)

        p = Path(hint)
        if not p.exists():
            print(f"Error: path does not exist: {hint}")
            sys.exit(1)

        # Check if the path has HTML files directly
        html_files = list(p.glob("*.html"))
        if html_files:
            site_path = str(p)
        else:
            detected = detect_site_path(hint)
            if detected:
                site_path = detected
                print(f"  Detected site content: {site_path}")
            else:
                site_path = hint

    # Verify the path exists
    if not Path(site_path).is_dir():
        print(f"Warning: {site_path} does not exist or is not a directory.")
        cont = input("  Continue anyway? [y/N]: ").strip().lower()
        if cont != 'y':
            sys.exit(1)

    print()

    # 2. Metadata
    print("=== Metadata ===")
    name = prompt("Name (used as ZIM filename)", required=True,
                  validator=validate_filename, sanitizer=sanitize_filename)
    title = prompt("Title", default=name.replace('-', ' ').title(), required=True)
    creator = prompt("Creator", default="Unknown", required=True)
    publisher = prompt("Publisher", default="You")
    description = prompt("Description", required=True)

    print(f"\n  Common language codes: {', '.join(f'{k} ({v})' for k, v in list(COMMON_LANGUAGES.items())[:6])}")
    language = prompt("Language (ISO 639-3)", default="eng", required=True,
                      validator=validate_language_code)

    print()

    # 3. Options
    print("=== Options ===")
    output_path = prompt("Output directory for ZIM files", default="zim_files")
    icon = prompt("Icon path", default="icons/comment.png")

    resolve_ext = input("  Resolve external dependencies? [y/N]: ").strip().lower() == 'y'
    cleanup = input("  Clean up unreferenced assets? [y/N]: ").strip().lower() == 'y'
    optimize = input("  Optimize images? [y/N]: ").strip().lower() == 'y'

    max_width = 1920
    quality = 85
    if optimize:
        w = prompt("Max image width", default="1920")
        try:
            max_width = int(w)
        except ValueError:
            max_width = 1920
        q = prompt("JPEG quality (1-100)", default="85")
        try:
            quality = int(q)
        except ValueError:
            quality = 85

    # Build config
    config = {
        "site_path": site_path,
        "output_path": output_path,
        "icon": icon,
        "name": name,
        "title": title,
        "creator": creator,
        "publisher": publisher,
        "description": description,
        "language": language,
        "resolve_external": resolve_ext,
        "cleanup": cleanup,
        "optimize_images": optimize,
    }

    if optimize:
        config["max_image_width"] = max_width
        config["image_quality"] = quality

    # Determine output path
    if args.output:
        out_file = Path(args.output)
    else:
        out_file = Path("config") / f"{name}.json"

    out_file.parent.mkdir(parents=True, exist_ok=True)

    if out_file.exists():
        overwrite = input(f"\n  {out_file} already exists. Overwrite? [y/N]: ").strip().lower()
        if overwrite != 'y':
            print("Aborted.")
            sys.exit(0)

    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\n=== Config saved to {out_file} ===")
    print(f"\nTo create the ZIM file:")
    print(f"  python3 website_converter.py {out_file}")


if __name__ == "__main__":
    main()
