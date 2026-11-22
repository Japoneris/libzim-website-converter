# Transform a Static Website into a ZIM File

A Python script to convert static websites into [ZIM archives](https://wiki.openzim.org/wiki/ZIM_file_format) for offline viewing with [Kiwix](https://kiwix.org/).

Uses [python-libzim](https://github.com/openzim/python-libzim) to create ZIM files with automatic path conversion, image optimization, and validation.

## Installation

```bash
# Required
pip install libzim

# Optional (for additional features)
pip install tqdm Pillow

# Or install everything, including the test runner, at once
pip install -r requirements.txt
```

## Quick Start

The JSON config file is the only required argument; it holds every project setting.

```bash
# 1. Create a config file (interactive helper)
python3 create_config.py --site-path myblog/_site/ --output config/myblog.json

# 2. Convert it to a ZIM archive
python3 website_converter.py config/myblog.json

# 3. Analyze without writing a ZIM
python3 website_converter.py config/myblog.json --dry-run
```

ZIM files are saved to `zim_files/` by default; change `"output_path"` in the config to override it.

## Features

- ✅ **Automatic path conversion** - Converts absolute paths to relative paths
- ✅ **Image optimization** - Resize and compress images (optional)
- ✅ **Progress bars** - Visual feedback during conversion
- ✅ **Dry run mode** - Analyze website without creating ZIM
- ✅ **HTML validation report** - Identify broken links and issues
- ✅ **Configuration files** - Reusable, self-contained conversion settings
- ✅ **Cross-platform** - Works on Linux, macOS, and Windows
- ✅ **External dependency resolution** - Downloads CDN assets into `_external/` for offline use
- ✅ **35+ MIME types** - Comprehensive file format support

## Directory Structure

```
ZimSite/
├── website_converter.py    # Main ZIM converter script (config-file CLI)
├── httrack_wrapper.py      # HTTrack wrapper script
├── create_config.py        # Interactive config file builder
├── converter/              # Converter package (one module per concern)
│   ├── config.py           # Config loading, defaults, logging
│   ├── validation.py       # Shared metadata validation
│   ├── path_utils.py       # Main-page path resolution
│   ├── external_deps.py    # External URL discovery/download/rewrite
│   ├── file_processor.py   # File processing and ZIM item creation
│   ├── image_optimizer.py  # Optional image optimization
│   ├── report_generator.py # HTML validation report
│   ├── mime_types.py       # Extension → MIME type mapping
│   └── zim_item.py         # libzim Item wrapper
├── tests/                  # Unit tests (pytest)
├── docs/                   # Numbered feature notes
├── pytest.ini              # Test configuration
├── config/                 # Config files
│   └── example.json
├── downloads/              # Downloaded websites (auto-created)
└── zim_files/              # Output directory for ZIM archives
```

## HTTrack Wrapper

The `httrack_wrapper.py` script simplifies downloading websites with HTTrack and preparing them for ZIM conversion.

**Basic usage:**
```bash
# Download website (name auto-generated from URL)
python3 httrack_wrapper.py https://example.com/docs/

# Download with custom name
python3 httrack_wrapper.py https://example.com/docs/ --name mydocs

# Pass additional httrack options
python3 httrack_wrapper.py https://example.com/ --httrack-args "-r3 --max-rate=1000000"

# Download a single page without following links
python3 httrack_wrapper.py https://example.com/docs/page.html --single-page
```

**What it does:**
1. Creates download folder in `downloads/`
2. Downloads website content using httrack
3. Tries to find/download a favicon and save it as `icons/<name>.png`
4. Generates config file in `config/` directory
5. Shows next steps for ZIM conversion

**Options:**
- `--name` - Custom project name (auto-generated if not provided)
- `--output` - Output directory (default: `downloads`)
- `--config-dir` - Config directory (default: `config`)
- `--httrack-args` - Additional httrack arguments
- `--single-page` - Download only the given URL (adds `-r1` to httrack)
- `--skip-download` - Only create config file, skip download
- `--no-favicon` - Skip favicon fetching

## Examples

### Example 1: Jekyll Website

```bash
# Build the Jekyll site
bundle exec jekyll build

# Create the config once, then reuse it for every rebuild
python3 create_config.py --site-path myblog/_site/ --output config/myblog.json

# Convert to ZIM
python3 website_converter.py config/myblog.json
```

### Example 2: External Website (Using HTTrack Wrapper)

```bash
# Install httrack if needed
sudo apt install httrack

# Download and prepare website (creates config/dataviz.json)
python3 httrack_wrapper.py https://clauswilke.com/dataviz/ --name dataviz

# Edit the generated config if needed
nano config/dataviz.json

# Convert to ZIM using the config
python3 website_converter.py config/dataviz.json
```

### Example 3: Optimized Conversion with Report

Put the feature settings in `config/myblog.json`:

```json
{
  "site_path": "myblog/_site",
  "name": "myblog",
  "title": "My Personal Blog",
  "creator": "John Doe",
  "description": "My blog, offline",
  "language": "eng",
  "optimize_images": true,
  "max_image_width": 1280,
  "image_quality": 85,
  "resolve_external": true,
  "cleanup": true
}
```

Then run:

```bash
python3 website_converter.py config/myblog.json --report
```

### Example 4: Dry Run (Analysis Only)

```bash
# Analyze without creating a ZIM; writes conversion_report.html
python3 website_converter.py config/myblog.json --dry-run
```

## Command-Line Options

The JSON config file is the only positional argument; it holds all project settings (see "Configuration File Format" below).

```bash
python3 website_converter.py --help
```

| Flag | Description |
|------|-------------|
| `--verbose` | DEBUG-level logging |
| `--quiet` | Errors only |
| `--dry-run` | Analyze and report without creating a ZIM file |
| `--report` | Generate the HTML validation report |
| `--no-progress` | Disable the progress bar |

## Configuration File Format

Required fields: `site_path`, `name`, `title`, `creator`, `description`, `language`.

```json
{
  "site_path": "downloads/my-site/example.com",
  "output_path": "zim_files",
  "icon": "icons/my-icon.png",
  "name": "my-website",
  "title": "My Website Title",
  "creator": "Your Name",
  "publisher": "Your Organization",
  "description": "Website description",
  "language": "eng",
  "main_page": "index.html",
  "resolve_external": false,
  "cleanup": false,
  "optimize_images": false,
  "max_image_width": 1920,
  "image_quality": 85
}
```

Optional fields and defaults: `output_path` (`zim_files`), `icon` (`icons/comment.png`), `publisher` (`You`), `main_page` (`index.html`), `resolve_external` (`false`), `cleanup` (`false`), `optimize_images` (`false`), `max_image_width` (`1920`), `image_quality` (`85`).

## Technical Details

### Path Conversion

Kiwix/ZIM viewers use relative paths. When a webpage requests `/assets/myfile.txt`,
it becomes `<kiwix_url>/zimfile/content/assets/myfile.txt`.

This script automatically converts absolute paths (`/assets/`) to relative paths
(`../assets/`, `../../assets/`, etc.) based on document depth in the directory tree.

### Supported MIME Types

**Images:** png, jpg, jpeg, gif, bmp, svg, webp, ico, tiff
**Styles:** css, scss
**Scripts:** js, ts, json
**Documents:** pdf, txt, xml, csv, doc, docx, odt, epub
**Media:** mp4, mpeg, wav, midi, mp3, ogg, webm
**Archives:** zip, rar, bz, bz2
**Fonts:** ttf, otf, woff, woff2
**Other:** 35+ types total

Unknown extensions are added to the validation report.

## Development

Tests and linting run against the project virtual environment:

```bash
my_env/bin/pip install -r requirements.txt
my_env/bin/python -m pytest -q
my_env/bin/ruff check .
my_env/bin/ruff check --fix .   # apply safe fixes
```

Lint rules and exclusions are configured in `ruff.toml`. Run `ruff check .` before committing: it is the code-quality gate for this project. The formatter (`ruff format .`) is available but is not enforced yet.

See `docs/` for notes describing each feature and the files it changed.

## Known Limitations

- **Permalinks:** Direct mappings like `/about/` → `about.html` may not work (ZIM viewer limitation)
- **Dynamic content:** JavaScript-heavy SPAs may need special handling
- **Large files:** Very large ZIM files (>4GB) may have compatibility issues with some readers

## Credits

- Icons from [Freepik](https://freepik.com/)
- Built with [python-libzim](https://github.com/openzim/python-libzim)
- Compatible with [Kiwix](https://kiwix.org/)
