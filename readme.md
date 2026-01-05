# Transform a Static Website into a ZIM File

A Python script to convert static websites into [ZIM archives](https://wiki.openzim.org/wiki/ZIM_file_format) for offline viewing with [Kiwix](https://kiwix.org/).

Uses [python-libzim](https://github.com/openzim/python-libzim) to create ZIM files with automatic path conversion, image optimization, and validation.

## Installation

```bash
# Required
pip install libzim

# Optional (for additional features)
pip install tqdm Pillow

# Or install all at once
pip install -r requirements.txt
```

## Quick Start

**Basic usage (interactive):**
```bash
python3 website_converter.py myblog/_site/
```
The script will prompt for metadata (name, creator, language, etc.).

**Non-interactive mode:**
```bash
python3 website_converter.py myblog/_site/ \
  --name "myblog" --title "My Blog" \
  --creator "Your Name" --language eng \
  --non-interactive
```

**Using a configuration file:**
```bash
python3 website_converter.py myblog/_site/ --config config/example.json
```

ZIM files are saved to `zim_files/` by default.

## Features

- ✅ **Automatic path conversion** - Converts absolute paths to relative paths
- ✅ **Image optimization** - Resize and compress images (optional)
- ✅ **Progress bars** - Visual feedback during conversion
- ✅ **Dry run mode** - Analyze website without creating ZIM
- ✅ **HTML validation report** - Identify broken links and issues
- ✅ **Configuration files** - Reusable conversion settings
- ✅ **Cross-platform** - Works on Linux, macOS, and Windows
- ✅ **Non-interactive mode** - Perfect for CI/CD pipelines
- ✅ **35+ MIME types** - Comprehensive file format support

## Directory Structure

```
ZimSite/
├── website_converter.py    # Main ZIM converter script
├── httrack_wrapper.py      # HTTrack wrapper script
├── requirements.txt         # Python dependencies
├── readme.md               # This file
├── icons/                  # Icon assets for ZIM metadata
├── config/                 # Configuration files
│   ├── example.json       # Example configuration
│   ├── myfamily.json      # User configs
│   └── interpretable.json
├── downloads/              # Downloaded websites (auto-created)
└── zim_files/             # Output directory for ZIM archives
    └── *.zim              # Your generated ZIM files
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
```

**What it does:**
1. Creates download folder in `downloads/`
2. Downloads website content using httrack
3. Generates config file in `config/` directory
4. Shows next steps for ZIM conversion

**Options:**
- `--name` - Custom project name (auto-generated if not provided)
- `--output` - Output directory (default: `downloads`)
- `--config-dir` - Config directory (default: `config`)
- `--httrack-args` - Additional httrack arguments
- `--skip-download` - Only create config file, skip download

## Examples

### Example 1: Jekyll Website

```bash
# Build the Jekyll site
bundle exec jekyll build

# Convert to ZIM
python3 website_converter.py myblog/_site/ \
  --name "myblog" \
  --title "My Personal Blog" \
  --creator "John Doe" \
  --language eng
```

### Example 2: External Website (Using HTTrack Wrapper)

```bash
# Install httrack if needed
sudo apt install httrack

# Download and prepare website
python3 httrack_wrapper.py https://clauswilke.com/dataviz/ --name dataviz

# Edit the generated config file if needed
nano config/dataviz.json

# Convert to ZIM using the config
python3 website_converter.py downloads/dataviz/*/ --config config/dataviz.json
```

### Example 3: Optimized Conversion

```bash
# With image optimization and validation report
python3 website_converter.py myblog/_site/ \
  --config config/example.json \
  --optimize-images \
  --max-image-width 1280 \
  --report
```

### Example 4: Dry Run (Analysis Only)

```bash
# Analyze website without creating ZIM
python3 website_converter.py myblog/_site/ --dry-run

# Opens conversion_report.html with all issues found
```



## Command-Line Options

```bash
python3 website_converter.py --help
```

**Positional:**
- `site_path` - Path to compiled website directory

**Metadata:**
- `--name` - ZIM filename (without .zim)
- `--title` - Title metadata
- `--creator` - Creator name
- `--publisher` - Publisher name (default: "You")
- `--description` - Content description
- `--language` - ISO 639-3 language code (eng, fra, etc.)

**Configuration:**
- `--config` - Path to JSON config file (e.g., `config/example.json`)
- `--non-interactive` - No prompts (requires all metadata via flags)
- `--output_path` - Output directory (default: `zim_files`)
- `--icon` - Path to icon PNG (default: `icons/comment.png`)

**Features:**
- `--optimize-images` - Resize/compress images (requires Pillow)
- `--max-image-width` - Max width for optimization (default: 1920)
- `--image-quality` - JPEG quality (default: 85)
- `--dry-run` - Analyze without creating ZIM
- `--report` - Generate HTML validation report

**Verbosity:**
- `--verbose` - Show debug output
- `--quiet` - Only show errors
- `--no-progress` - Disable progress bar

## Configuration File Format

Create a JSON file in `config/` directory:

```json
{
  "name": "my-website",
  "title": "My Website Title",
  "creator": "Your Name",
  "publisher": "Your Organization",
  "description": "Website description",
  "language": "eng"
}
```

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
**Media:** mp4, mpeg, wav, midi
**Archives:** zip, rar, bz, bz2
**Fonts:** ttf, otf
**Other:** 35+ types total

Unknown extensions are treated as HTML and logged in the report.

## Known Limitations

- **Permalinks:** Direct mappings like `/about/` → `about.html` may not work (ZIM viewer limitation)
- **Dynamic content:** JavaScript-heavy SPAs may need special handling
- **Large files:** Very large ZIM files (>4GB) may have compatibility issues with some readers

## Credits

- Icons from [Freepik](https://freepik.com/)
- Built with [python-libzim](https://github.com/openzim/python-libzim)
- Compatible with [Kiwix](https://kiwix.org/)