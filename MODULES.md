# Website Converter Modules

This document describes the modular structure of the website converter.

## Project Structure

```
ZimSite/
├── website_converter.py       # CLI entry point (main(argv))
├── httrack_wrapper.py         # HTTrack wrapper utility
├── create_config.py           # Interactive config file builder
├── converter/                 # Converter package (all modules)
│   ├── __init__.py            # Public API re-exports
│   ├── zim_item.py            # ZIM Item wrapper
│   ├── validation.py          # Shared validation/sanitization
│   ├── config.py              # Configuration & logging
│   ├── path_utils.py          # Main-page path resolution
│   ├── image_optimizer.py     # Image optimization
│   ├── report_generator.py    # HTML report generation
│   ├── mime_types.py          # MIME type mappings
│   ├── external_deps.py       # External URL discovery/download/rewrite
│   └── file_processor.py      # Core file processing
├── tests/                     # Unit tests (pytest)
├── docs/                      # Numbered feature notes
├── pytest.ini                 # Test configuration
├── ruff.toml                  # Lint configuration
├── config/                    # Configuration files
├── icons/                     # Icon resources
└── zim_files/                 # Output directory
```

## Module Overview

The original monolithic `website_converter.py` (720 lines) was split into a package. Current line counts:

### Main Scripts

- **website_converter.py** (291 lines) - Argument parsing, config-driven orchestration, ZIM creation. The body lives in `main(argv=None)`, so the CLI can be imported and smoke-tested.
- **httrack_wrapper.py** (402 lines) - Downloads a website with httrack, discovers a favicon, and writes a config file.
- **create_config.py** (236 lines) - Interactive config builder. Shares `converter.validation` helpers with the converter instead of defining its own.

### Converter Package (`converter/`)

1. **zim_item.py** (37 lines)
   - `MyItem` class wrapping libzim `Item`
   - Handles content providers (string, bytes, file)

2. **validation.py** (51 lines)
   - `validate_language_code()` - ISO 639-3-shaped, case-insensitive 3-letter codes
   - `validate_filename()` - Check for invalid characters
   - `sanitize_filename()` - Clean up filenames
   - Single source of truth; also imported by `create_config.py`

3. **config.py** (106 lines)
   - `CONFIG_DEFAULTS`, `REQUIRED_FIELDS`
   - `setup_logging()`, `load_config()`, `validate_config()`

4. **path_utils.py** (25 lines)
   - `resolve_main_page()` - URL-decodes the configured main page and resolves it against the site directory

5. **image_optimizer.py** (63 lines)
   - `optimize_image()` - Resize and compress images, preserving JPEG/PNG format
   - `is_pillow_available()` - Check for the optional Pillow dependency

6. **report_generator.py** (121 lines)
   - `generate_link_validation_report()` - Create an HTML report
   - Shows missing index pages, unknown MIME types, and errors

7. **mime_types.py** (77 lines)
   - `MIME_TYPES` dictionary - Extension to MIME type mapping
   - `get_mime_type()` - Lookup helper

8. **external_deps.py** (289 lines)
   - `find_external_urls()`, `url_to_local_path()`, `download_resource()`
   - `resolve_external_dependencies()` - Download CDN assets into `_external/`
   - `replace_external_urls()` - Rewrite URLs in memory for offline use

9. **file_processor.py** (316 lines)
   - `process_html_content()` - Fix root-relative paths and validate index links
   - `find_referenced_assets()`, `cleanup_unreferenced()` - Drop unreferenced assets
   - `process_dry_run()` - Analyze files without creating a ZIM
   - `process_files()` - Main file processing and ZIM item creation

## Benefits of This Structure

- **Maintainability**: Each module has a single, clear responsibility
- **Readability**: Smaller files are easier to understand and navigate
- **Testability**: Individual modules are tested independently in `tests/`
- **Reusability**: Modules can be imported and used in other projects
- **Extensibility**: New features can be added without modifying core logic

## Usage

The config file is the only positional argument:

```bash
python3 create_config.py --site-path myblog/_site/ --output config/myblog.json
python3 website_converter.py config/myblog.json
```

## Tests

Unit tests live in `tests/` and mirror the modules:

- `test_validation.py` - shared validators and config-builder parity
- `test_file_processor.py` - HTML path rewriting and index-link validation
- `test_image_optimizer.py` - format preservation and small-image skip
- `test_report_generator.py` - HTML report renders without breaking on CSS braces
- `test_path_utils.py` - main-page resolution
- `test_cli.py` - CLI help smoke test

```bash
my_env/bin/python -m pytest -q
```

### Linting

`ruff.toml` pins the lint rules (pyflakes, pycodestyle error codes, import order, bugbear and pyupgrade) and excludes generated/large directories (`downloads/`, `zim_files/`, `my_env/`, `.hermes/`).

```bash
my_env/bin/ruff check .          # zero errors expected
my_env/bin/ruff check --fix .    # apply safe fixes
```

## Module Dependencies

```
website_converter.py
├── config (logging, configuration)
├── validation (input validation)
├── path_utils (main-page resolution)
├── image_optimizer (optional image processing)
├── report_generator (HTML reports)
├── external_deps (CDN asset download/rewrite)
└── file_processor
    ├── zim_item (ZIM item wrapper)
    ├── mime_types (MIME type mappings)
    ├── image_optimizer (optional image processing)
    └── external_deps (URL rewriting)
```
